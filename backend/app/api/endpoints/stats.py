from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from datetime import datetime, time, timezone
from typing import Literal, cast

from app.services import stats_svc
from app.schemas.stats import DetectionTrendOut
from app.models.scam import InputType

router = APIRouter()


class PublicStatsOut(BaseModel):
    users_protected: int
    checks_daily: int
    links_analysed: int
    total_checks: int


# The database is queried on a daily basis
def today_start_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime.combine(now.date(), time.min, tzinfo=timezone.utc)

@router.get("/public", response_model=PublicStatsOut)
async def get_public_stats():
    return await stats_svc.get_public_stats()

@router.get("/detection-trend", response_model=DetectionTrendOut)
async def get_detection_trend(
    days: int = Query(7, description="Only supports 7 or 30"),
    risk_level: Literal["all", "low", "medium", "high"] = Query("high"),
    input_types: list[InputType] | None = Query(
        None,
        description="Repeat query param, e.g. ?input_types=text&input_types=url",
    ),
):
    if days not in (7, 30):
        raise HTTPException(status_code=400, detail="days must be 7 or 30")

    days_literal = cast(Literal[7, 30], days)

    selected_types = input_types or [
        InputType.TEXT,
        InputType.IMAGE,
        InputType.URL,
        InputType.QR,
    ]

    return await stats_svc.get_detection_trend(
        days=days_literal,
        risk_level=risk_level,
        input_types=selected_types,
    )