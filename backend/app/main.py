from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
import httpx

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
    _startup_logger.info(f"Instagram DM automation enabled={settings.INSTAGRAM_DM_ENABLED}")
    start_scheduler()

    # Railway yeniden başlatma sonrası pending işleri kurtar
    try:
        from app.api.routes.video import recover_pending_jobs
        recover_pending_jobs()
    except Exception as e:
        _startup_logger.error(f"[startup] Video job recovery hatası: {e}")

    # Kritik kolon varlığını doğrula — şema/kod uyumsuzluklarını erken yakala
    try:
        from app.db.supabase import get_supabase_client
        _sb = get_supabase_client()
        _checks = [
            ("generated_contents", ["id", "title", "type", "status", "topic", "created_at"]),
            ("documents", ["id", "file_name", "storage_path", "status", "source_module"]),
            ("sgs_questions", ["id", "lesson_name", "topic", "document_id"]),
        ]
        for table, cols in _checks:
            r = _sb.table(table).select(",".join(cols)).limit(0).execute()
            _startup_logger.info(f"[startup] şema kontrol OK: {table} ({','.join(cols)})")
    except Exception as e:
        _startup_logger.error(f"[startup] ŞEMA UYUMSUZLUĞU — bazı kolonlar eksik: {e}")

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

_widget_dist = Path(__file__).resolve().parent / "static" / "widget"
if _widget_dist.exists():
    app.mount("/widget", StaticFiles(directory=str(_widget_dist)), name="widget")

_widget_allowed_origins = {
    "https://adimmusavir.com",
    "https://www.adimmusavir.com",
}


@app.middleware("http")
async def widget_cors(request: Request, call_next):
    is_widget_api = request.url.path.startswith("/api/v1/chat/")
    origin = request.headers.get("origin")
    if is_widget_api and origin and origin not in _widget_allowed_origins:
        return JSONResponse(status_code=403, content={"detail": "Widget origin izinli değil"})

    if is_widget_api and request.method == "OPTIONS":
        return JSONResponse(status_code=204, content=None, headers={
            "Access-Control-Allow-Origin": origin or "https://www.adimmusavir.com",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,X-Adimos-Key",
        })
    response = await call_next(request)
    if is_widget_api and origin in _widget_allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    return response


# Supabase HTTP/2 protokol ve zaman aşımı hatalarını yakala — container crash'i önle
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    exc_type = type(exc).__name__
    if "LocalProtocolError" in exc_type or "ConnectionTerminated" in exc_type:
        _startup_logger.warning(f"[http2] Supabase bağlantı hatası ({exc_type}): {exc}")
        return JSONResponse(status_code=503, content={"detail": "Geçici bağlantı hatası, yeniden deneyin."})
    if isinstance(exc, httpx.TimeoutException):
        _startup_logger.warning(f"[timeout] Sorgu zaman aşımı ({exc_type}) path={request.url.path}")
        return JSONResponse(status_code=504, content={"detail": "Veritabanı sorgusu zaman aşımına uğradı. Yeniden deneyin."})
    raise exc


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
