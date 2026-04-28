from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from app.models.scam_case import ScamTypeEnum, PlatformEnum


class ScamCaseResponse(BaseModel):
    id: int = Field(..., description="The unique system identifier of the case ID")

    title: str = Field(..., description="News headlines of fraud cases")

    content: str = Field(
        ...,
        description="A complete description of the case, including the course of events and details",
    )

    scam_type: str = Field(
        ...,
        description="Classification of fraud types, for example：'Job Scams', 'Phishing Scams', 'QR Code Scams', 'OTP / SMS Scams'",
    )

    platform: str = Field(
        ...,
        description="The communication platform or social media where the fraud occurred，such as：'TikTok', 'Facebook', 'WhatsApp', 'Phone call'",
        examples=["WhatsApp", "Facebook", "TikTok"],
    )

    news_date: date = Field(
        ...,
        description="The specific date of the case or news report, in the format YYYY-MM-DD",
    )

    # Optional 字段，默认值给 None
    source: Optional[str] = Field(
        None,
        description="Source agencies of news or cases, such as: 'Bernama', 'The Star'. It might be empty.",
    )

    url_link: Optional[str] = Field(None, description="the url link of the scam cases.")

    class Config:
        # Allow conversion from ORM objects to Pydantic objects
        from_attributes = True


class ScamCaseFilterRequest(BaseModel):
    scam_type: Optional[ScamTypeEnum] = Field(
        default=None, description="Types of fraud"
    )
    platform: Optional[PlatformEnum] = Field(default=None, description="platform")
    year: Optional[int] = Field(default=None, description="year")
