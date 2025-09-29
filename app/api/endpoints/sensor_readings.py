from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ... import crud, schemas, models
from ...database import get_db

router = APIRouter()

def generate_sensor_data() -> Dict[str, float]:
    """Generate random sensor data for simulation"""
    import random
    return {
        "pm25": round(random.uniform(0, 100), 2),  # μg/m³
        "co2": random.randint(400, 2000),  # ppm
        "tvoc": round(random.uniform(0, 500), 2),  # ppb
        "temperature": round(random.uniform(15, 30), 1),  # °C
        "humidity": round(random.uniform(30, 80), 1),  # %
        "mold_risk": round(random.uniform(0, 1), 2)  # 0-1 scale
    }

@router.post("/readings/", response_model=schemas.SensorReadingOut)
def create_reading(
    reading: schemas.SensorReadingCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new sensor reading.
    """
    return crud.create_sensor_reading(db=db, reading=reading)

@router.post("/readings/bulk/", response_model=List[schemas.SensorReadingOut])
def create_bulk_readings(
    readings: schemas.BulkSensorReading,
    db: Session = Depends(get_db)
):
    """
    Create multiple sensor readings in a single request.
    """
    return crud.create_bulk_sensor_readings(db=db, readings=readings.readings)

@router.get("/readings/", response_model=List[schemas.SensorReadingOut])
def read_readings(
    location_zipcode: Optional[str] = Query(None, description="Filter by location zipcode"),
    start_time: Optional[datetime] = Query(None, description="Start time for filtering"),
    end_time: Optional[datetime] = Query(None, description="End time for filtering"),
    limit: int = Query(100, le=1000, description="Limit number of results"),
    db: Session = Depends(get_db)
):
    """
    Retrieve sensor readings with optional filters.
    """
    return crud.get_sensor_readings(
        db=db,
        location_zipcode=location_zipcode,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )

@router.get("/readings/latest/", response_model=List[schemas.SensorReadingOut])
def read_latest_readings(
    limit: int = Query(10, le=100, description="Number of latest readings to return"),
    db: Session = Depends(get_db)
):
    """
    Get the latest sensor readings from different locations.
    """
    return crud.get_latest_readings_by_location(db=db, limit=limit)

@router.get("/readings/stats/", response_model=Dict[str, Any])
def get_statistics(
    location_zipcode: Optional[str] = Query(None, description="Filter by location zipcode"),
    time_window_hours: int = Query(24, description="Time window in hours for statistics"),
    db: Session = Depends(get_db)
):
    """
    Get statistics for sensor readings within a time window.
    """
    stats = crud.get_sensor_stats(
        db=db,
        location_zipcode=location_zipcode,
        time_window_hours=time_window_hours
    )
    
    # Format the response
    result = []
    for stat in stats:
        location, min_pm25, max_pm25, avg_pm25, min_co2, max_co2, avg_co2, last_updated = stat
        result.append({
            "location": {
                "zipcode": location.zipcode,
                "borough": location.borough,
                "latitude": location.latitude,
                "longitude": location.longitude
            },
            "stats": {
                "pm25": {
                    "min": float(min_pm25) if min_pm25 is not None else None,
                    "max": float(max_pm25) if max_pm25 is not None else None,
                    "avg": float(avg_pm25) if avg_pm25 is not None else None,
                    "unit": "μg/m³"
                },
                "co2": {
                    "min": float(min_co2) if min_co2 is not None else None,
                    "max": float(max_co2) if max_co2 is not None else None,
                    "avg": float(avg_co2) if avg_co2 is not None else None,
                    "unit": "ppm"
                }
            },
            "last_updated": last_updated
        })
    
    return {"results": result}

@router.get("/readings/simulate/")
def simulate_reading(
    zipcode: str = Query("10001", description="Zipcode for the simulated reading"),
    borough: str = Query("Manhattan", description="Borough for the simulated reading")
):
    """
    Generate a simulated sensor reading (for testing/demo purposes).
    """
    data = generate_sensor_data()
    return {
        "location_zipcode": zipcode,
        "borough": borough,
        "timestamp": datetime.utcnow().isoformat(),
        **data
    }

@router.post("/public-health/", response_model=schemas.PublicHealthData)
def add_public_health_data(
    health_data: schemas.PublicHealthDataCreate,
    db: Session = Depends(get_db)
):
    """
    Add public health data for a location.
    """
    return crud.add_public_health_data(db=db, health_data=health_data)

@router.get("/public-health/{zipcode}", response_model=List[schemas.PublicHealthData])
def get_public_health_data(
    zipcode: str,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get public health data for a location.
    """
    location = crud.get_location(db, zipcode=zipcode)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    query = db.query(models.PublicHealthData).filter(
        models.PublicHealthData.location_id == location.id
    )
    
    if year is not None:
        query = query.filter(models.PublicHealthData.year == year)
    
    return query.all()
