from app.models.scam_case import ScamCase
from typing import List, Optional
from datetime import date, timedelta


async def get_filtered_cases(
    scam_type: Optional[str] = None,
    platform: Optional[str] = None,
    time_range: int = 0,  # 0=All, 1=3 months, 2=6 months, 3=1 year
) -> List[ScamCase]:
    """
    User Story 6.1: Encapsulate Multi-dimensional Filtering logic
    """
    query = ScamCase.all()

    if scam_type is not None:
        query = query.filter(scam_type=scam_type)
    if platform is not None:
        # icontains ignores case blur matching
        query = query.filter(platform=platform)

    # Time range filtering
    if time_range == 1:  # Last 3 Months
        start_date = date.today() - timedelta(days=90)
        query = query.filter(news_date__gte=start_date)
    elif time_range == 2:  # Last 6 Months
        start_date = date.today() - timedelta(days=180)
        query = query.filter(news_date__gte=start_date)
    elif time_range == 3:  # Last Year
        start_date = date.today() - timedelta(days=365)
        query = query.filter(news_date__gte=start_date)
    # time_range == 0 It indicates "All Time" and does not filter

    return await query.order_by("-news_date")


async def get_case_detail(case_id: int) -> Optional[ScamCase]:
    """
    User Story 6.2: Obtain individual cases based on ID
    """
    return await ScamCase.get_or_none(id=case_id)
