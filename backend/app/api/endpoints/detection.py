from typing import Literal

from app.models.scam import DetectionLog
from app.services.orchestrator import scan_universal_input
from app.services.session_svc import get_or_create_session_from_cookie
from app.utils.text_scam_tools import build_detection_log_rows
from fastapi import APIRouter, Cookie, File, Form, HTTPException, UploadFile

router = APIRouter()


@router.post("/scan")
async def scan_message(
    text: str = Form(None),
    file: UploadFile = File(None),
    input_type: Literal["text", "image", "url", "qr"] = Form("text"),
    session_id: str | None = Cookie(default=None),
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Must provide text or a file.")

    session = await get_or_create_session_from_cookie(session_id)

    result = await scan_universal_input(file=file, text=text, input_type=input_type)

    # store into detection_log table
    rows = build_detection_log_rows(
        input_type=input_type,  # Here, make sure that what is passed in is text/image/url/qr
        result=result,
        raw_text=text,
    )
    for row in rows:
        await DetectionLog.create(
            session=session,
            input_type=row["input_type"],
            input_content=row["input_content"],
            risk_score=row["risk_score"],
        )

    return result


# async def scan_message():
#     return {"status": "success", "message": "Scam detection endpoint is ready!"}
