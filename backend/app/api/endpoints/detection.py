from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.orchestrator import scan_universal_input
from typing import Literal

router = APIRouter()


@router.post("/scan")
async def scan_message(
        text: str = Form(None),
        file: UploadFile = File(None),
        input_type: Literal["text", "image", "audio", "video", "qr", "auto"] = Form("auto"),
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Must provide text or a file.")

    return await scan_universal_input(file=file, text=text, input_type=input_type)


# async def scan_message():
#     return {"status": "success", "message": "Scam detection endpoint is ready!"}
