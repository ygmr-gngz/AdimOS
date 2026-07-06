from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


# Supabase HTTP/2 protokol hatası — container crash'i önle
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    exc_type = type(exc).__name__
    if "LocalProtocolError" in exc_type or "ConnectionTerminated" in exc_type:
        _startup_logger.warning(f"[http2] Supabase bağlantı hatası yakalandı ({exc_type}): {exc}")
        return JSONResponse(status_code=503, content={"detail": "Geçici bağlantı hatası, yeniden deneyin."})
    raise exc


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
