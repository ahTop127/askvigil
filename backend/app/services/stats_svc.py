from datetime import datetime, time, timezone, timedelta
from decimal import Decimal
from typing import Literal

from app.models.scam import InputType, DetectionLog
from app.models.session import UserSession


def today_start_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime.combine(now.date(), time.min, tzinfo=timezone.utc)


def _risk_match(
    score: Decimal | float | int | None,
    risk_level: Literal["all", "low", "medium", "high"],
) -> bool:
    if risk_level == "all":
        return True
    if score is None:
        return False
    s = float(score)
    if risk_level == "high":
        return s >= 70
    if risk_level == "medium":
        return 40 <= s < 70
    return 0 <= s < 40  # low


# Static statistics
async def get_public_stats() -> dict:
    today_start = today_start_utc()

    users_protected = await UserSession.all().count()
    total_checks = await DetectionLog.all().count()
    checks_daily = await DetectionLog.filter(
        created_at__gte=today_start,
    ).count()

    links_analysed = await DetectionLog.filter(
        input_type__in=[InputType.URL, InputType.QR],
    ).count()

    return {
        "users_protected": users_protected,
        "checks_daily": checks_daily,
        "links_analysed": links_analysed,
        "total_checks": total_checks,
    }


"""
    Detect the trend line chart

    Based on 'detection_logs.created_at' :
    - Daily testing volume for the last 7 days / 30 days (date optional by the user)
    - Daily high-risk detection volume (risk level can be selected by users)
    Trends of different input types: text, image, url, qr (users can choose the type)
    
    Users can see how much suspicious content the system has recently identified, which also reflects the system's activity level.
"""


async def get_detection_trend(
    days: Literal[7, 30],
    risk_level: Literal["all", "low", "medium", "high"],
    input_types: list[InputType],
) -> dict:
    now_utc = datetime.now(timezone.utc)
    start_date = (now_utc - timedelta(days=days - 1)).date()
    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    rows = await DetectionLog.filter(
        created_at__gte=start_dt,
        input_type__in=input_types,
    ).values("created_at", "input_type", "risk_score")

    # Make up for every day and ensure that the front-end line chart is not disconnected
    bucket: dict[str, dict] = {}
    for i in range(days):
        d = (start_date + timedelta(days=i)).isoformat()
        bucket[d] = {
            "date": d,
            "total_count": 0,
            "risk_count": 0,
            "text": 0,
            "image": 0,
            "url": 0,
            "qr": 0,
        }

    for row in rows:
        created_at: datetime = row["created_at"]
        day_key = created_at.astimezone(timezone.utc).date().isoformat()
        point = bucket.get(day_key)
        if point is None:
            continue
        point["total_count"] += 1
        if _risk_match(row.get("risk_score"), risk_level):
            point["risk_count"] += 1
        it = row["input_type"]
        if it == InputType.TEXT:
            point["text"] += 1
        elif it == InputType.IMAGE:
            point["image"] += 1
        elif it == InputType.URL:
            point["url"] += 1
        elif it == InputType.QR:
            point["qr"] += 1

    return {
        "days": days,
        "risk_level": risk_level,
        "input_types": input_types,
        "points": [bucket[k] for k in sorted(bucket.keys())],
    }
