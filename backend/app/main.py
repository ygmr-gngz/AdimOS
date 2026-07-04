from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.router import router


import logging
_startup_logger = logging.getLogger("adimos.startup")

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.modules.automation.scheduler import start_scheduler, stop_scheduler
    _startup_logger.info(f"AdimOS API başlatılıyor — ortam: {settings.ENVIRONMENT}")
    _startup_logger.info(f"META_VERIFY_TOKEN loaded: {bool(settings.META_VERIFY_TOKEN)}")
    _startup_logger.info(f"META_ACCESS_TOKEN loaded: {bool(settings.META_ACCESS_TOKEN)}")
    _startup_logger.info(f"INSTAGRAM_BUSINESS_ACCOUNT_ID loaded: {bool(settings.INSTAGRAM_BUSINESS_ACCOUNT_ID)}")
    start_scheduler()

    # Railway yeniden başlatma sonrası pending işleri kurtar
    try:
        from app.api.routes.video import recover_pending_jobs
        recover_pending_jobs()
    except Exception as e:
        _startup_logger.error(f"[startup] Video job recovery hatası: {e}")

    yield
    stop_scheduler()
    _startup_logger.info("AdimOS API kapatılıyor")


app = FastAPI(
    title="AdimOS API",
    description="Adım Müşavirlik & SGS Academy — Çok Ajanlı AI Sistemi",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://adim-os-web.vercel.app",
        "https://adimos-production.up.railway.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
