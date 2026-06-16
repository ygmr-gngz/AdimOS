from fastapi import APIRouter
from app.api.routes import health, documents, chat, voice, agents, dashboard, crm, academy, automation, content, debug

router = APIRouter()

router.include_router(health.router,     prefix="/health",     tags=["health"])
router.include_router(documents.router,  prefix="/documents",  tags=["documents"])
router.include_router(chat.router,       prefix="/chat",        tags=["chat"])
router.include_router(voice.router,      prefix="/voice",       tags=["voice"])
router.include_router(agents.router,     prefix="/agents",      tags=["agents"])
router.include_router(dashboard.router,  prefix="/dashboard",   tags=["dashboard"])
router.include_router(crm.router,        prefix="/crm",         tags=["crm"])
router.include_router(academy.router,    prefix="/academy",     tags=["academy"])
router.include_router(automation.router, prefix="/automation",  tags=["automation"])
router.include_router(content.router,    prefix="/content",     tags=["content"])
router.include_router(debug.router,      prefix="/debug",       tags=["debug"])
