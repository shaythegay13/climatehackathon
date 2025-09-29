from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from .. import models, schemas

from app.schemas.sensor_reading import LocationCreate

def get_location(db: Session, zipcode: str):
    return db.query(models.Location).filter(models.Location.zipcode == zipcode).first()

def create_location(db: Session, location: LocationCreate):
    db_location = models.Location(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def get_or_create_location(db: Session, location: LocationCreate):
    db_location = get_location(db, zipcode=location.zipcode)
    if not db_location:
        db_location = create_location(db, location)
    return db_location

def create_sensor_reading(db: Session, reading: schemas.SensorReadingCreate):
    # Get or create location
    location = get_or_create_location(
        db,
        LocationCreate(
            zipcode=reading.location_zipcode,
            borough=""  # This would be looked up in a real implementation
        )
    )
    
    # Create the reading
    db_reading = models.SensorReading(
        location_id=location.id,
        timestamp=reading.timestamp or datetime.utcnow(),
        pm25=reading.pm25,
        co2=reading.co2,
        tvoc=reading.tvoc,
        temperature=reading.temperature,
        humidity=reading.humidity,
        mold_risk=reading.mold_risk
    )
    
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading

def create_bulk_sensor_readings(db: Session, readings: List[schemas.SensorReadingCreate]):
    """Create multiple sensor readings in a single transaction"""
    db_readings = []
    for reading in readings:
        location = get_or_create_location(
            db,
            schemas.LocationCreate(
                zipcode=reading.location_zipcode,
                borough=""  # This would be looked up in a real implementation
            )
        )
        
        db_reading = models.SensorReading(
            location_id=location.id,
            timestamp=reading.timestamp or datetime.utcnow(),
            pm25=reading.pm25,
            co2=reading.co2,
            tvoc=reading.tvoc,
            temperature=reading.temperature,
            humidity=reading.humidity,
            mold_risk=reading.mold_risk
        )
        db.add(db_reading)
        db_readings.append(db_reading)
    
    db.commit()
    return db_readings

def get_sensor_readings(
    db: Session,
    location_zipcode: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100
):
    query = db.query(models.SensorReading).join(models.Location)
    
    if location_zipcode:
        query = query.filter(models.Location.zipcode == location_zipcode)
    
    if start_time:
        query = query.filter(models.SensorReading.timestamp >= start_time)
    
    if end_time:
        query = query.filter(models.SensorReading.timestamp <= end_time)
    
    return query.order_by(models.SensorReading.timestamp.desc()).limit(limit).all()

def get_latest_readings_by_location(db: Session, limit: int = 100):
    # This is a simplified version - in production, you'd want a more efficient query
    locations = db.query(models.Location).limit(limit).all()
    results = []
    
    for loc in locations:
        latest = (
            db.query(models.SensorReading)
            .filter(models.SensorReading.location_id == loc.id)
            .order_by(models.SensorReading.timestamp.desc())
            .first()
        )
        if latest:
            results.append(latest)
    
    return results

def get_sensor_stats(
    db: Session,
    location_zipcode: Optional[str] = None,
    time_window_hours: int = 24
):
    time_threshold = datetime.utcnow() - timedelta(hours=time_window_hours)
    
    query = db.query(
        models.Location,
        func.min(models.SensorReading.pm25).label("min_pm25"),
        func.max(models.SensorReading.pm25).label("max_pm25"),
        func.avg(models.SensorReading.pm25).label("avg_pm25"),
        func.min(models.SensorReading.co2).label("min_co2"),
        func.max(models.SensorReading.co2).label("max_co2"),
        func.avg(models.SensorReading.co2).label("avg_co2"),
        func.max(models.SensorReading.timestamp).label("last_updated")
    ).join(
        models.SensorReading,
        models.SensorReading.location_id == models.Location.id
    ).filter(
        models.SensorReading.timestamp >= time_threshold
    )
    
    if location_zipcode:
        query = query.filter(models.Location.zipcode == location_zipcode)
    
    query = query.group_by(models.Location.id)
    return query.all()

def add_public_health_data(db: Session, health_data: schemas.PublicHealthDataCreate):
    location = get_location(db, zipcode=health_data.location_zipcode)
    if not location:
        location = create_location(
            db,
            schemas.LocationCreate(
                zipcode=health_data.location_zipcode,
                borough=""  # Would be looked up in a real implementation
            )
        )
    
    db_health_data = models.PublicHealthData(
        location_id=location.id,
        year=health_data.year,
        asthma_rate=health_data.asthma_rate,
        emergency_visits=health_data.emergency_visits
    )
    
    db.add(db_health_data)
    db.commit()
    db.refresh(db_health_data)
    return db_health_data
