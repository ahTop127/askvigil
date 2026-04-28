from app.models.scam_case import ScamCase
from typing import List, Optional
from datetime import date


async def get_filtered_cases(
    scam_type: Optional[str] = None,
    platform: Optional[str] = None,
    year: Optional[int] = None,
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
    if year is not None:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        query = query.filter(news_date__gte=start_date, news_date__lte=end_date)

    return await query.order_by("-news_date")


async def get_case_detail(case_id: int) -> Optional[ScamCase]:
    """
    User Story 6.2: Obtain individual cases based on ID
    """
    return await ScamCase.get_or_none(id=case_id)
