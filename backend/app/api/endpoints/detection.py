from fastapi import APIRouter

router = APIRouter()


@router.post("/scan")
async def scan_message():
    return {"status": "success", "message": "Scam detection endpoint is ready!"}
