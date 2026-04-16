from fastapi import APIRouter

from app.api.v1.routers import chat, health, research, sessions

router = APIRouter()
router.include_router(health.router)
router.include_router(research.router)
router.include_router(chat.router)
router.include_router(sessions.router)
