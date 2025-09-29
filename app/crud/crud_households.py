from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func

from ..models import (
    Household,
    HouseholdSensorReading,
    HouseholdAlert,
    HealthContext,
)

# Households

def create_household(
    db: Session,
    *,
    zipcode: str,
    housing_type: str,
    address: Optional[str] = None,
    risk_score: float = 0.0,
) -> Household:
    hh = Household(
        address=address,
        zipcode=zipcode,
        housing_type=housing_type,
        risk_score=risk_score,
    )
    db.add(hh)
    db.commit()
    db.refresh(hh)
    return hh


def get_household_by_id(db: Session, household_id: int) -> Optional[Household]:
    return db.get(Household, household_id)


def get_households_by_zip(db: Session, zipcode: str, limit: int = 100) -> List[Household]:
    stmt = select(Household).where(Household.zipcode == zipcode).limit(limit)
    return list(db.scalars(stmt))


# Sensor readings

def add_sensor_reading(
    db: Session,
    *,
    household_id: int,
    device_id: Optional[str],
    timestamp: Optional[datetime] = None,
    pm25: Optional[float] = None,
    co2: Optional[int] = None,
    voc: Optional[float] = None,
    humidity: Optional[float] = None,
    mold_flag: bool = False,
) -> HouseholdSensorReading:
    reading = HouseholdSensorReading(
        household_id=household_id,
        device_id=device_id,
        timestamp=timestamp or datetime.now(timezone.utc),
        pm25=pm25,
        co2=co2,
        voc=voc,
        humidity=humidity,
        mold_flag=mold_flag,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def get_latest_readings_for_zip(db: Session, zipcode: str, limit: int = 20) -> List[HouseholdSensorReading]:
    stmt = (
        select(HouseholdSensorReading)
        .join(Household, Household.household_id == HouseholdSensorReading.household_id)
        .where(Household.zipcode == zipcode)
        .order_by(desc(HouseholdSensorReading.timestamp))
        .limit(limit)
    )
    return list(db.scalars(stmt))


# Alerts

def create_alert(
    db: Session,
    *,
    household_id: int,
    event_type: str,
    alert_message: str,
    reading_id: Optional[int] = None,
    timestamp: Optional[datetime] = None,
) -> HouseholdAlert:
    alert = HouseholdAlert(
        household_id=household_id,
        reading_id=reading_id,
        event_type=event_type,
        alert_message=alert_message,
        timestamp=timestamp or datetime.now(timezone.utc),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_alerts_for_household(db: Session, household_id: int, hours_back: int = 24, limit: int = 200) -> List[HouseholdAlert]:
    since = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    stmt = (
        select(HouseholdAlert)
        .where(HouseholdAlert.household_id == household_id)
        .where(HouseholdAlert.timestamp >= since)
        .order_by(desc(HouseholdAlert.timestamp))
        .limit(limit)
    )
    return list(db.scalars(stmt))


# Health context

def upsert_health_context(
    db: Session,
    *,
    zipcode: str,
    asthma_rate: Optional[float],
    er_visit_rate: Optional[float],
    ej_index: Optional[float],
) -> HealthContext:
    ctx = db.get(HealthContext, zipcode)
    if not ctx:
        ctx = HealthContext(
            zipcode=zipcode,
            asthma_rate=asthma_rate,
            er_visit_rate=er_visit_rate,
            ej_index=ej_index,
        )
        db.add(ctx)
    else:
        ctx.asthma_rate = asthma_rate
        ctx.er_visit_rate = er_visit_rate
        ctx.ej_index = ej_index
    db.commit()
    return ctx


# Aggregations
def aggregate_zip_trends(
    db: Session,
    *,
    hours_back: int = 24,
) -> List[dict]:
    """Return anonymized zip-level trends over the time window.
    Includes counts and avg metrics for pm25, co2, voc, humidity.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    # Join households->readings and compute aggregates by zipcode
    stmt = (
        select(
            Household.zipcode.label("zipcode"),
            func.count(HouseholdSensorReading.reading_id).label("reading_count"),
            func.avg(HouseholdSensorReading.pm25).label("avg_pm25"),
            func.avg(HouseholdSensorReading.co2).label("avg_co2"),
            func.avg(HouseholdSensorReading.voc).label("avg_voc"),
            func.avg(HouseholdSensorReading.humidity).label("avg_humidity"),
            func.max(HouseholdSensorReading.timestamp).label("last_updated"),
        )
        .join(Household, Household.household_id == HouseholdSensorReading.household_id)
        .where(HouseholdSensorReading.timestamp >= since)
        .group_by(Household.zipcode)
        .order_by(desc(func.count(HouseholdSensorReading.reading_id)))
    )
    rows = db.execute(stmt).all()
    results = []
    for zipcode, reading_count, avg_pm25, avg_co2, avg_voc, avg_humidity, last_updated in rows:
        results.append({
            "zipcode": zipcode,
            "reading_count": int(reading_count or 0),
            "averages": {
                "pm25": float(avg_pm25) if avg_pm25 is not None else None,
                "co2": float(avg_co2) if avg_co2 is not None else None,
                "voc": float(avg_voc) if avg_voc is not None else None,
                "humidity": float(avg_humidity) if avg_humidity is not None else None,
            },
            "last_updated": last_updated,
        })
    return results
