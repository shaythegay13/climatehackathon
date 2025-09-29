from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class LocationBase(BaseModel):
    zipcode: str = Field(..., example="10001")
    borough: str = Field(..., example="Manhattan")
    latitude: Optional[float] = Field(None, example=40.7506)
    longitude: Optional[float] = Field(None, example=-73.9974)

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    id: int
    
    class Config:
        from_attributes = True

class SensorReadingBase(BaseModel):
    location_zipcode: str = Field(..., example="10001")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    pm25: Optional[float] = Field(None, ge=0, le=1000, description="PM2.5 in μg/m³")
    co2: Optional[float] = Field(None, ge=300, le=10000, description="CO2 in ppm")
    tvoc: Optional[float] = Field(None, ge=0, le=1000, description="Total VOCs in ppb")
    temperature: Optional[float] = Field(None, ge=-20, le=60, description="Temperature in °C")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Relative humidity in %")
    mold_risk: Optional[float] = Field(None, ge=0, le=1, description="Mold risk index (0-1)")

class SensorReadingCreate(SensorReadingBase):
    pass

class SensorReading(SensorReadingBase):
    id: int
    location: Location
    
    class Config:
        from_attributes = True

# Response model that matches ORM output (no location_zipcode on the model)
class SensorReadingOut(BaseModel):
    id: int
    timestamp: Optional[datetime] = None
    pm25: Optional[float] = None
    co2: Optional[float] = None
    tvoc: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    mold_risk: Optional[float] = None
    location: Location

    class Config:
        from_attributes = True

class PublicHealthDataBase(BaseModel):
    location_zipcode: str = Field(..., example="10001")
    year: int = Field(..., ge=2000, le=2030, example=2023)
    asthma_rate: Optional[float] = Field(None, ge=0, description="Asthma rate per 10,000 people")
    emergency_visits: Optional[int] = Field(None, ge=0, description="Annual respiratory emergency visits")

class PublicHealthDataCreate(PublicHealthDataBase):
    pass

class PublicHealthData(PublicHealthDataBase):
    id: int
    
    class Config:
        from_attributes = True

class SensorStats(BaseModel):
    metric: str
    min: float
    max: float
    avg: float
    latest: float
    unit: str

class LocationStats(BaseModel):
    location: Location
    stats: Dict[str, SensorStats]
    last_updated: datetime

class BulkSensorReading(BaseModel):
    readings: List[SensorReadingBase]
