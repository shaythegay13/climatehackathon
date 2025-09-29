from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    zipcode = Column(String(10), unique=True, index=True, nullable=False)
    borough = Column(String(50), index=True, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Relationship
    sensor_readings = relationship("SensorReading", back_populates="location")

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Air quality metrics
    pm25 = Column(Float, nullable=True)  # PM2.5 in μg/m³
    co2 = Column(Float, nullable=True)   # CO2 in ppm
    tvoc = Column(Float, nullable=True)  # Total VOCs in ppb
    temperature = Column(Float, nullable=True)  # Temperature in °C
    humidity = Column(Float, nullable=True)     # Relative humidity in %
    mold_risk = Column(Float, nullable=True)    # Mold risk index (0-1)
    
    # Relationship
    location = relationship("Location", back_populates="sensor_readings")

class PublicHealthData(Base):
    __tablename__ = "public_health_data"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    year = Column(Integer, nullable=False)
    asthma_rate = Column(Float, nullable=True)  # Asthma rate per 10,000 people
    emergency_visits = Column(Integer, nullable=True)  # Annual respiratory emergency visits
    
    # Relationship
    location = relationship("Location")
