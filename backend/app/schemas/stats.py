from pydantic import BaseModel, Field
from typing import List, Literal
from app.models.scam import InputType

class PublicStatsOut(BaseModel):
    users_protected: int = Field(..., description="Total unique sessions")
    checks_daily: int = Field(..., description="Detection checks today (UTC)")
    links_analysed: int = Field(..., description="URL/QR checks count")
    total_checks: int = Field(..., description="Total detection checks")

class TrendPointOut(BaseModel):
    date: str = Field(..., description="UTC date in YYYY-MM-DD")
    total_count: int = Field(..., description="Total checks that day")
    risk_count: int = Field(..., description="Checks matching selected risk_level")
    text: int = 0
    image: int = 0
    url: int = 0
    qr: int = 0

class DetectionTrendOut(BaseModel):
    days: Literal[7, 30]
    risk_level: Literal["all", "low", "medium", "high"]
    input_types: List[InputType]
    points: List[TrendPointOut]