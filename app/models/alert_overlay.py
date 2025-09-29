from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    reading_id = Column(Integer, ForeignKey("sensor_readings.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    metric = Column(String(50), nullable=False)       # e.g., pm25, co2, tvoc, humidity, mold_risk
    threshold = Column(Float, nullable=False)
    value = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False)     # e.g., info, warning, critical
    message = Column(String(255), nullable=False)

    location = relationship("Location")

class Overlay(Base):
    __tablename__ = "overlays"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    type = Column(String(100), nullable=False)        # e.g., asthma_rate
    year = Column(Integer, nullable=True)
    value = Column(Float, nullable=True)
    meta = Column(JSON, nullable=True)

    location = relationship("Location")
