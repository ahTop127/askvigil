from fastapi import APIRouter
from app.api.endpoints import detection, learning, session_api, scam_cases, qr_detection, stats

api_router = APIRouter()

# 将 Epic 1 的检测接口挂载到总路由上
api_router.include_router(detection.router, prefix="/detection", tags=["Detection"])
api_router.include_router(
    session_api.router, prefix="/session", tags=["Session Tracking"]
)
api_router.include_router(learning.router, prefix="/learning", tags=["Learning & Quiz"])
# Epic 6
api_router.include_router(scam_cases.router, prefix="/scam", tags=["Scam Cases"])

# api_router.include_router(qr_detection.router, prefix="/qr", tags=["QR Detection"])

api_router.include_router(stats.router, prefix="/stats", tags=["Public Stats"])
