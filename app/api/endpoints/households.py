from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database import get_db
from ...schemas.household import (
    HouseholdCreate,
    Household,
    HouseholdReadingCreate,
    HouseholdReading,
    HouseholdAlertCreate,
    HouseholdAlert,
    HealthContextUpsert,
    HealthContext,
)
from ...crud import crud_households as hh

router = APIRouter()

# Households CRUD
@router.post("/households", response_model=Household)
def create_household(payload: HouseholdCreate, db: Session = Depends(get_db)):
    return hh.create_household(
        db,
        zipcode=payload.zipcode,
        housing_type=payload.housing_type,
        address=payload.address,
        risk_score=payload.risk_score,
    )

@router.get("/households/{household_id}", response_model=Household)
def get_household(household_id: int, db: Session = Depends(get_db)):
    obj = hh.get_household_by_id(db, household_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Household not found")
    return obj

@router.get("/households", response_model=List[Household])
def list_households(zipcode: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if zipcode:
        return hh.get_households_by_zip(db, zipcode)
    # Simple fallback list
    return hh.get_households_by_zip(db, zipcode="10001")

# Readings
@router.post("/households/{household_id}/readings", response_model=HouseholdReading)
def add_reading(household_id: int, payload: HouseholdReadingCreate, db: Session = Depends(get_db)):
    if payload.household_id != household_id:
        raise HTTPException(status_code=400, detail="household_id mismatch in path and payload")
    return hh.add_sensor_reading(
        db,
        household_id=payload.household_id,
        device_id=payload.device_id,
        timestamp=payload.timestamp,
        pm25=payload.pm25,
        co2=payload.co2,
        voc=payload.voc,
        humidity=payload.humidity,
        mold_flag=payload.mold_flag,
    )

@router.get("/households/{household_id}/readings", response_model=List[HouseholdReading])
def get_readings(household_id: int, limit: int = Query(50, le=500), db: Session = Depends(get_db)):
    # use zip-based listing for now by fetching zip of household, then latest-by-zip
    obj = hh.get_household_by_id(db, household_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Household not found")
    return hh.get_latest_readings_for_zip(db, obj.zipcode, limit=limit)

# Alerts
@router.post("/households/{household_id}/alerts", response_model=HouseholdAlert)
def add_alert(household_id: int, payload: HouseholdAlertCreate, db: Session = Depends(get_db)):
    if payload.household_id != household_id:
        raise HTTPException(status_code=400, detail="household_id mismatch in path and payload")
    return hh.create_alert(
        db,
        household_id=payload.household_id,
        event_type=payload.event_type,
        alert_message=payload.alert_message,
        reading_id=payload.reading_id,
        timestamp=payload.timestamp,
    )

@router.get("/households/{household_id}/alerts", response_model=List[HouseholdAlert])
def get_alerts(household_id: int, hours_back: int = Query(24, ge=1, le=168), db: Session = Depends(get_db)):
    return hh.get_alerts_for_household(db, household_id=household_id, hours_back=hours_back)

# Health Context
@router.put("/health-context", response_model=HealthContext)
def upsert_context(payload: HealthContextUpsert, db: Session = Depends(get_db)):
    return hh.upsert_health_context(
        db,
        zipcode=payload.zipcode,
        asthma_rate=payload.asthma_rate,
        er_visit_rate=payload.er_visit_rate,
        ej_index=payload.ej_index,
    )

@router.get("/health-context/{zipcode}", response_model=HealthContext)
def get_context(zipcode: str, db: Session = Depends(get_db)):
    ctx = db.get(hh.HealthContext, zipcode)
    if not ctx:
        raise HTTPException(status_code=404, detail="Not found")
    return ctx


# Aggregations and context refresh (Step 4)
@router.get("/aggregations/zip-trends")
def get_zip_trends(hours_back: int = Query(24, ge=1, le=168), db: Session = Depends(get_db)):
    """Return anonymized zip-level trends for the last N hours."""
    return {"results": hh.aggregate_zip_trends(db, hours_back=hours_back)}


@router.post("/context/refresh")
def refresh_context(zipcode: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Mock external PEDP/NYC health context refresh.
    If zipcode provided, refresh for that zip; else refresh for zipcodes seen in households.
    """
    zips: List[str] = []
    if zipcode:
        zips = [zipcode]
    else:
        # collect distinct zips from households
        zips = list({h.zipcode for h in db.query(hh.Household).all()})
    # mock values; in a real impl, call external APIs and map
    for z in zips:
        hh.upsert_health_context(db, zipcode=z, asthma_rate=18.3, er_visit_rate=22.7, ej_index=0.63)
    return {"status": "ok", "updated": zips}
