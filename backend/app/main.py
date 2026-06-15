from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.modules.automation.scheduler import start_scheduler, stop_scheduler
    print(f"AdimOS API başlatılıyor — ortam: {settings.ENVIRONMENT}")
    start_scheduler()
    yield
    stop_scheduler()
    print("AdimOS API kapatılıyor")


app = FastAPI(
    title="AdimOS API",
    description="Adım Müşavirlik & SGS Academy — Çok Ajanlı AI Sistemi",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://adim-os-web.vercel.app", "https://adimos-production.up.railway.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
