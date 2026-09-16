from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Literal

from tortoise.functions import Count

from app.models.scam import DetectionLog, InputType
from app.models.scam_case import ScamCase
from app.models.session import UserSession


def today_start_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime.combine(now.date(), time.min, tzinfo=timezone.utc)


def _risk_match(
    score: Decimal | float | None,
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

        if not _risk_match(row.get("risk_score"), risk_level):
            continue

        point["total_count"] += 1

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


async def get_input_type_distribution() -> dict:
    """
    Input type distribution map
    Based on 'DetectionLog.input_type' :
    pie chart or bar chart can be made:

    - Text checks
    - Image OCR checks
    - URL checks
    - QR checks

    This is also intuitive for users: What methods do people most commonly use to detect fraud?
    """
    rows = await DetectionLog.all().values("input_type")

    text_count = 0
    image_count = 0
    url_count = 0
    qr_count = 0

    for row in rows:
        it = row["input_type"]

        if it == InputType.TEXT:
            text_count += 1
        elif it == InputType.IMAGE:
            image_count += 1
        elif it == InputType.URL:
            url_count += 1
        elif it == InputType.QR:
            qr_count += 1

    total = text_count + image_count + url_count + qr_count

    return {
        "text_count": text_count,
        "image_count": image_count,
        "url_count": url_count,
        "qr_count": qr_count,
        "total": total,
    }


async def get_risk_level_distribution() -> dict:
    """
    Distribution of risk levels

    Based on 'DetectionLog.risk_score' :

    -Low risk: 0-39
    -Medium risk: 40-69
    -High risk: 70-100

    donut chart or stacked bar can be made.

    This is more meaningful than simply showing the average score, as users can know the proportion of risky content recently discovered by the platform.
    """

    rows = await DetectionLog.all().values("risk_score")

    low_count = 0
    medium_count = 0
    high_count = 0
    unknown_count = 0

    for row in rows:
        score = row.get("risk_score")

        if score is None:
            unknown_count += 1
            continue

        try:
            s = float(score)
        except (TypeError, ValueError):
            unknown_count += 1
            continue

        # Bucket definition: 0-39/40-69/70-100
        if 0 <= s < 40:
            low_count += 1
        elif 40 <= s < 70:
            medium_count += 1
        elif 70 <= s <= 100:
            high_count += 1
        else:
            # The out-of-bounds value should be regarded as unknown and be protected from dirty data
            unknown_count += 1

    total = low_count + medium_count + high_count + unknown_count

    return {
        "low_count": low_count,
        "medium_count": medium_count,
        "high_count": high_count,
        "unknown_count": unknown_count,
        "total": total,
    }


async def get_scam_type_ranking(top_n: int = 10) -> dict:
    """
    Scam Type ranking: Use Horizontal Bar Chart

    Using a horizontal bar chart is better than a pie chart because the names of fraud types are longer
    """
    total_cases = await ScamCase.all().count()

    rows = (
        await ScamCase.all()
        .group_by("scam_type")
        .annotate(case_count=Count("id"))
        .values("scam_type", "case_count")
    )

    # 按数量倒序，再按类型名升序（数量相同稳定排序）
    rows_sorted = sorted(
        rows, key=lambda x: (-int(x["case_count"]), str(x["scam_type"]))
    )

    if top_n > 0:
        rows_sorted = rows_sorted[:top_n]

    items = [
        {
            "scam_type": str(row["scam_type"]),
            "count": int(row["case_count"]),
            "rank": idx + 1,
        }
        for idx, row in enumerate(rows_sorted)
    ]

    return {
        "total_cases": total_cases,
        "items": items,
    }
