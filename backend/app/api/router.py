from fastapi import APIRouter, Depends
from app.api.routes import health, documents, chat, voice, agents, dashboard, crm, academy, automation, content, debug, webhooks, sgs, notifications, social, brand, oauth, video
from app.api.routes import users
from app.api.routes.meta_webhook import router as meta_router, protected_router as meta_protected_router
from app.core.auth import get_current_user

router = APIRouter()

# Public (auth gerektirmeyen)
router.include_router(health.router,        prefix="/health",   tags=["health"])
router.include_router(webhooks.router,      prefix="/webhooks", tags=["webhooks"])
router.include_router(meta_router,          prefix="/meta",     tags=["meta"])
router.include_router(oauth.router,         prefix="/oauth",    tags=["oauth"])
router.include_router(video.public_router,  prefix="/video",    tags=["video"])

# Protected — auth zorunlu
_protected = APIRouter(dependencies=[Depends(get_current_user)])
_protected.include_router(documents.router,  prefix="/documents",  tags=["documents"])
_protected.include_router(chat.router,       prefix="/chat",       tags=["chat"])
_protected.include_router(voice.router,      prefix="/voice",      tags=["voice"])
_protected.include_router(agents.router,     prefix="/agents",     tags=["agents"])
_protected.include_router(dashboard.router,  prefix="/dashboard",  tags=["dashboard"])
_protected.include_router(crm.router,        prefix="/crm",        tags=["crm"])
_protected.include_router(academy.router,    prefix="/academy",    tags=["academy"])
_protected.include_router(automation.router, prefix="/automation", tags=["automation"])
_protected.include_router(content.router,    prefix="/content",    tags=["content"])
_protected.include_router(debug.router,      prefix="/debug",      tags=["debug"])
_protected.include_router(users.router,      prefix="/users",      tags=["users"])
_protected.include_router(sgs.router,           prefix="/sgs",           tags=["sgs"])
_protected.include_router(notifications.router, prefix="/notifications",  tags=["notifications"])
_protected.include_router(social.router,            prefix="/social",    tags=["social"])
_protected.include_router(brand.router,            prefix="/brand",     tags=["brand"])
_protected.include_router(video.router,            prefix="/video",     tags=["video"])
_protected.include_router(meta_protected_router,   prefix="/meta",      tags=["meta"])

router.include_router(_protected)
