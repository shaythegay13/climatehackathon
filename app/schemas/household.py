from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# Households
class HouseholdBase(BaseModel):
    zipcode: str = Field(..., example="10001")
    housing_type: str = Field(..., example="apartment")
    address: Optional[str] = Field(None, example="123 Example St")
    risk_score: float = Field(0.0, ge=0, le=100)

class HouseholdCreate(HouseholdBase):
    pass

class Household(HouseholdBase):
    household_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Readings
class HouseholdReadingBase(BaseModel):
    household_id: int
    device_id: Optional[str] = Field(None, example="dev-001")
    timestamp: Optional[datetime] = None
    pm25: Optional[float] = Field(None, ge=0, le=1000)
    co2: Optional[int] = Field(None, ge=0, le=100000)
    voc: Optional[float] = Field(None, ge=0, le=100000)
    humidity: Optional[float] = Field(None, ge=0, le=100)
    mold_flag: bool = False

class HouseholdReadingCreate(HouseholdReadingBase):
    pass

class HouseholdReading(HouseholdReadingBase):
    reading_id: int

    class Config:
        from_attributes = True

# Alerts
class HouseholdAlertBase(BaseModel):
    household_id: int
    event_type: str
    alert_message: str
    reading_id: Optional[int] = None
    timestamp: Optional[datetime] = None

class HouseholdAlertCreate(HouseholdAlertBase):
    pass

class HouseholdAlert(HouseholdAlertBase):
    alert_id: int

    class Config:
        from_attributes = True

# Health Context
class HealthContextBase(BaseModel):
    zipcode: str
    asthma_rate: Optional[float] = None
    er_visit_rate: Optional[float] = None
    ej_index: Optional[float] = None

class HealthContextUpsert(HealthContextBase):
    pass

class HealthContext(HealthContextBase):
    class Config:
        from_attributes = True
