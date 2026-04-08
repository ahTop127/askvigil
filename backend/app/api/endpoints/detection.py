from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.orchestrator import scan_universal_input

router = APIRouter()


@router.post("/scan")
async def scan_message(text: str = Form(None), file: UploadFile = File(None)):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Must provide text or a file.")

    return await scan_universal_input(file=file, text=text)


# async def scan_message():
#     return {"status": "success", "message": "Scam detection endpoint is ready!"}
