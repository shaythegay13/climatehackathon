from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database import get_db
from ... import models, schemas
from ...crud import crud_sensor_reading as readings_crud
from ...crud import crud_alerts as alerts_crud
from ...crud import crud_households as hh_crud
from ...schemas.alerts import IngestPayload, AlertsResponse, AlertOut, OverlayOut, RecommendationsResponse
from ...services.alert_engine import evaluate_reading
from ...services.recommendations import actions_for_alerts
from app.schemas.sensor_reading import LocationCreate

router = APIRouter()

@router.post("/sensor-ingest", response_model=Dict[str, Any])
def sensor_ingest(payload: IngestPayload, db: Session = Depends(get_db)):
    """Accept a single sensor reading, store it, evaluate alerts, and persist alerts."""
    # Ensure location exists
    location = readings_crud.get_or_create_location(
        db,
        LocationCreate(
            zipcode=payload.zipcode,
            borough=payload.borough or "",
        ),
    )

    # Persist the reading (Step 1/2 tables)
    reading = models.SensorReading(
        location_id=location.id,
        timestamp=payload.timestamp or datetime.utcnow(),
        pm25=payload.pm25,
        co2=payload.co2,
        tvoc=payload.tvoc,
        temperature=payload.temperature,
        humidity=payload.humidity,
        mold_risk=payload.mold_risk,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # Evaluate alerts
    triggered = evaluate_reading(payload.dict())
    saved_alerts: List[models.Alert] = []
    for a in triggered:
        saved = alerts_crud.create_alert(
            db,
            location_id=location.id,
            reading_id=reading.id,
            metric=a["metric"],
            threshold=a["threshold"],
            value=a["value"],
            severity=a["severity"],
            message=a["message"],
        )
        saved_alerts.append(saved)

    # If a household_id is provided, also persist to Step 3 tables
    household_reading_id = None
    if payload.household_id is not None:
        # Map tvoc -> voc; mold_flag -> bool based on mold_risk threshold
        mold_flag = False
        if payload.mold_risk is not None:
            mold_flag = bool(payload.mold_risk >= 0.6)

        hh_reading = hh_crud.add_sensor_reading(
            db,
            household_id=payload.household_id,
            device_id=None,
            timestamp=payload.timestamp or datetime.utcnow(),
            pm25=payload.pm25,
            co2=int(payload.co2) if payload.co2 is not None else None,
            voc=payload.tvoc,
            humidity=payload.humidity,
            mold_flag=mold_flag,
        )
        household_reading_id = hh_reading.reading_id

        # Mirror alerts into household_alerts with event_type derived from metric/direction
        for a in triggered:
            metric = a["metric"]
            value = a["value"]
            threshold = a["threshold"]
            # Determine event type suffix
            if metric == "humidity":
                suffix = "low" if value < threshold else "high"
                event_type = f"humidity_{suffix}"
            elif metric in ("pm25", "co2", "tvoc", "mold_risk"):
                event_type = f"{metric}_high"
            else:
                event_type = metric

            hh_crud.create_alert(
                db,
                household_id=payload.household_id,
                event_type=event_type,
                alert_message=a["message"],
                reading_id=household_reading_id,
                timestamp=datetime.utcnow(),
            )

    # Prepare advice if alerts were triggered
    advice = None
    reasons = None
    if triggered:
        advice = actions_for_alerts(triggered)
        reasons = [f"{a['metric']}={a['value']} threshold={a['threshold']} ({a['severity']})" for a in triggered]

    return {
        "status": "ok",
        "reading_id": reading.id,
        "alerts_created": len(saved_alerts),
        "household_reading_id": household_reading_id,
        "advice": advice,
        "reasons": reasons,
    }


@router.get("/alerts", response_model=AlertsResponse)
def get_alerts(
    zipcode: Optional[str] = Query(None),
    time_window_hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(hours=time_window_hours)
    alerts = alerts_crud.get_alerts(db, zipcode=zipcode, since=since)

    out: List[AlertOut] = []
    for a in alerts:
        out.append(
            AlertOut(
                metric=a.metric,
                threshold=a.threshold,
                value=a.value,
                severity=a.severity,
                message=a.message,
                created_at=a.created_at,
                zipcode=a.location.zipcode if a.location else "",
                borough=a.location.borough if a.location else None,
            )
        )
    return AlertsResponse(count=len(out), alerts=out)


@router.get("/context", response_model=Dict[str, Any])
def get_context(
    zipcode: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    # Mock overlays now; in future, fetch from public datasets and cache
    overlays: List[OverlayOut] = []
    if zipcode:
        overlays.append(OverlayOut(type="asthma_rate", zipcode=zipcode, year=year or 2023, value=18.3))
    else:
        overlays.append(OverlayOut(type="asthma_rate", zipcode="10001", year=2023, value=18.3))
    return {"overlays": [o.dict() for o in overlays]}


@router.get("/recommendations", response_model=RecommendationsResponse)
def get_recommendations(
    zipcode: Optional[str] = Query(None),
    latest: bool = Query(True),
    db: Session = Depends(get_db),
):
    # Find latest reading and evaluate
    reading = alerts_crud.get_latest_reading_for_zip(db, zipcode)
    if not reading:
        return RecommendationsResponse(status="no data", zipcode=zipcode)

    payload = {
        "zipcode": reading.location.zipcode if reading.location else zipcode or "",
        "borough": reading.location.borough if reading.location else "",
        "timestamp": reading.timestamp,
        "pm25": reading.pm25,
        "co2": reading.co2,
        "tvoc": reading.tvoc,
        "humidity": reading.humidity,
        "temperature": reading.temperature,
        "mold_risk": reading.mold_risk,
    }

    triggered = evaluate_reading(payload)
    if not triggered:
        return RecommendationsResponse(status="no action needed", zipcode=payload["zipcode"]) 

    actions = actions_for_alerts(triggered)
    reasons = [f"{a['metric']}={a['value']} threshold={a['threshold']} ({a['severity']})" for a in triggered]
    return RecommendationsResponse(status="action recommended", zipcode=payload["zipcode"], actions=actions, reasons=reasons)
