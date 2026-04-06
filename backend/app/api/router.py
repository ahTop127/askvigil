from fastapi import APIRouter
from app.api.endpoints import detection, learning, session_api

api_router = APIRouter()

# 将 Epic 1 的检测接口挂载到总路由上
api_router.include_router(detection.router, prefix="/detection", tags=["Detection"])
api_router.include_router(
    session_api.router, prefix="/session", tags=["Session Tracking"]
)
api_router.include_router(learning.router, prefix="/learning", tags=["Learning & Quiz"])
