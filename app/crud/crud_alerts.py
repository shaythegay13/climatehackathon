from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .. import models


def create_alert(
    db: Session,
    *,
    location_id: int,
    reading_id: Optional[int],
    metric: str,
    threshold: float,
    value: float,
    severity: str,
    message: str,
) -> models.Alert:
    alert = models.Alert(
        location_id=location_id,
        reading_id=reading_id,
        metric=metric,
        threshold=threshold,
        value=value,
        severity=severity,
        message=message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def create_alerts_bulk(db: Session, alerts: List[models.Alert]) -> List[models.Alert]:
    for a in alerts:
        db.add(a)
    db.commit()
    return alerts


def get_alerts(
    db: Session,
    *,
    zipcode: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 200,
) -> List[models.Alert]:
    q = db.query(models.Alert).join(models.Location, models.Location.id == models.Alert.location_id)
    if zipcode:
        q = q.filter(models.Location.zipcode == zipcode)
    if since:
        q = q.filter(models.Alert.created_at >= since)
    return q.order_by(models.Alert.created_at.desc()).limit(limit).all()


def get_latest_reading_for_zip(db: Session, zipcode: Optional[str]) -> Optional[models.SensorReading]:
    q = db.query(models.SensorReading).join(models.Location)
    if zipcode:
        q = q.filter(models.Location.zipcode == zipcode)
    return q.order_by(models.SensorReading.timestamp.desc()).first()


def add_overlay(
    db: Session,
    *,
    location_id: int,
    type: str,
    year: Optional[int] = None,
    value: Optional[float] = None,
    meta: Optional[dict] = None,
) -> models.Overlay:
    overlay = models.Overlay(
        location_id=location_id, type=type, year=year, value=value, meta=meta
    )
    db.add(overlay)
    db.commit()
    db.refresh(overlay)
    return overlay


def get_overlays(
    db: Session,
    *,
    zipcode: Optional[str] = None,
    limit: int = 200,
) -> List[models.Overlay]:
    q = db.query(models.Overlay).join(models.Location)
    if zipcode:
        q = q.filter(models.Location.zipcode == zipcode)
    return q.order_by(models.Overlay.year.desc().nullslast()).limit(limit).all()
