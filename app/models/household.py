from sqlalchemy import Column, BigInteger, Integer, String, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Household(Base):
    __tablename__ = "households"

    household_id = Column(BigInteger, primary_key=True, autoincrement=True)
    address = Column(String(255), nullable=True)
    zipcode = Column(String(10), nullable=False, index=True)
    housing_type = Column(String(50), nullable=False)
    risk_score = Column(Numeric(5, 2), nullable=False, default=0.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    readings = relationship("HouseholdSensorReading", back_populates="household", cascade="all, delete-orphan")
    alerts = relationship("HouseholdAlert", back_populates="household", cascade="all, delete-orphan")


class HouseholdSensorReading(Base):
    __tablename__ = "household_sensor_readings"

    reading_id = Column(BigInteger, primary_key=True, autoincrement=True)
    household_id = Column(BigInteger, ForeignKey("households.household_id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(100), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    pm25 = Column(Numeric(6, 2), nullable=True)
    co2 = Column(Integer, nullable=True)
    voc = Column(Numeric(8, 2), nullable=True)
    humidity = Column(Numeric(5, 2), nullable=True)
    mold_flag = Column(Boolean, nullable=False, default=False)

    household = relationship("Household", back_populates="readings")
    alerts = relationship("HouseholdAlert", back_populates="reading")


class HouseholdAlert(Base):
    __tablename__ = "household_alerts"

    alert_id = Column(BigInteger, primary_key=True, autoincrement=True)
    reading_id = Column(BigInteger, ForeignKey("household_sensor_readings.reading_id", ondelete="SET NULL"), nullable=True)
    household_id = Column(BigInteger, ForeignKey("households.household_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    alert_message = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    household = relationship("Household", back_populates="alerts")
    reading = relationship("HouseholdSensorReading", back_populates="alerts")


class HealthContext(Base):
    __tablename__ = "health_context"

    zipcode = Column(String(10), primary_key=True)
    asthma_rate = Column(Numeric(6, 3), nullable=True)
    er_visit_rate = Column(Numeric(6, 3), nullable=True)
    ej_index = Column(Numeric(6, 3), nullable=True)
