from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any, Dict

class IngestPayload(BaseModel):
    zipcode: str = Field(..., example="10001")
    borough: str = Field(..., example="Manhattan")
    household_id: Optional[int] = Field(None, description="Optional: map this reading to a household")
    timestamp: Optional[datetime] = Field(default=None)
    pm25: Optional[float] = Field(None, ge=0, le=1000)
    co2: Optional[float] = Field(None, ge=300, le=10000)
    tvoc: Optional[float] = Field(None, ge=0, le=2000)
    humidity: Optional[float] = Field(None, ge=0, le=100)
    temperature: Optional[float] = Field(None, ge=-20, le=60)
    mold_risk: Optional[float] = Field(None, ge=0, le=1)

class AlertOut(BaseModel):
    metric: str
    threshold: float
    value: float
    severity: str
    message: str
    created_at: datetime
    zipcode: str
    borough: Optional[str] = None

class AlertsResponse(BaseModel):
    count: int
    alerts: List[AlertOut]

class OverlayOut(BaseModel):
    type: str
    zipcode: str
    year: Optional[int] = None
    value: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None

class RecommendationsResponse(BaseModel):
    status: str
    zipcode: Optional[str] = None
    actions: Optional[List[str]] = None
    reasons: Optional[List[str]] = None
