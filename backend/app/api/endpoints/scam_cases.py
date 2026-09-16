from app.schemas.scam_case import ScamCaseFilterRequest, ScamCaseResponse
from app.services import cases_svc
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/filter", response_model=list[ScamCaseResponse])
async def read_scam_cases(
    filter: ScamCaseFilterRequest,
):
    return await cases_svc.get_filtered_cases(
        scam_type=filter.scam_type,
        platform=filter.platform,
        time_range=filter.time_range,
    )


@router.get("/{case_id}", response_model=ScamCaseResponse)
async def get_scam_case(case_id: int):
    case = await cases_svc.get_case_detail(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Scam case not found")

    return case
