"""Sağlık kontrol endpoint'leri — temel + sağlayıcı durumu."""
import time
import logging
from fastapi import APIRouter
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
def health_check():
    return {"status": "ok", "service": "AdimOS API", "version": "0.1.0"}


@router.get("/providers")
def provider_health():
    """
    OpenAI, Remotion ve Supabase durumunu kontrol eder.
    Frontend bu endpoint'i 60 saniyede bir sorgular (settings sayfası).
    """
    results: dict = {}

    # ── OpenAI ───────────────────────────────────────────────
    t0 = time.monotonic()
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=5.0)
        client.models.list()
        latency = int((time.monotonic() - t0) * 1000)
        results["openai"] = {"status": "ok", "latency_ms": latency}
    except Exception as e:
        detail = str(e)[:120]
        if "insufficient_quota" in detail:
            results["openai"] = {"status": "quota_exceeded", "detail": "TTS kotası tükendi"}
        elif "invalid_api_key" in detail or "Incorrect API key" in detail:
            results["openai"] = {"status": "error", "detail": "Geçersiz API anahtarı"}
        elif not settings.OPENAI_API_KEY:
            results["openai"] = {"status": "error", "detail": "OPENAI_API_KEY tanımlı değil"}
        else:
            results["openai"] = {"status": "error", "detail": detail}
        logger.warning(f"[health] OpenAI kontrol başarısız: {e}")

    # ── Remotion ─────────────────────────────────────────────
    remotion_url = settings.REMOTION_URL
    if not remotion_url:
        results["remotion"] = {"status": "not_configured", "detail": "REMOTION_URL tanımlı değil"}
    else:
        t0 = time.monotonic()
        try:
            import httpx
            r = httpx.get(f"{remotion_url}/health", timeout=5.0)
            latency = int((time.monotonic() - t0) * 1000)
            if r.status_code == 200:
                results["remotion"] = {"status": "ok", "latency_ms": latency}
            else:
                results["remotion"] = {
                    "status": "degraded",
                    "detail": f"HTTP {r.status_code}",
                    "latency_ms": latency,
                }
        except Exception as e:
            results["remotion"] = {"status": "error", "detail": "Ulaşılamıyor"}
            logger.warning(f"[health] Remotion kontrol başarısız: {e}")

    # ── Supabase ─────────────────────────────────────────────
    t0 = time.monotonic()
    try:
        from app.db.supabase import get_supabase_client
        sb = get_supabase_client()
        sb.table("video_jobs").select("id").limit(1).execute()
        latency = int((time.monotonic() - t0) * 1000)
        results["supabase"] = {"status": "ok", "latency_ms": latency}
    except Exception as e:
        detail = str(e)[:120]
        if not settings.SUPABASE_URL:
            results["supabase"] = {"status": "error", "detail": "SUPABASE_URL tanımlı değil"}
        else:
            results["supabase"] = {"status": "error", "detail": detail}
        logger.warning(f"[health] Supabase kontrol başarısız: {e}")

    # Genel özet
    all_statuses = [v["status"] for v in results.values()]
    if all(s == "ok" for s in all_statuses):
        overall = "ok"
    elif "error" in all_statuses:
        overall = "degraded"
    else:
        overall = "partial"

    return {"overall": overall, "providers": results}
