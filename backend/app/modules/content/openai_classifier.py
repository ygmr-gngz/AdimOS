"""
OpenAI hata sınıflandırma — yapısal kod alanı önce, string eşleme yedek olarak.
insufficient_quota → tek denemede durur, retry sayacı 0.
rate_limit → exponential backoff, maks. 4 deneme.
"""
import time
import random
import logging
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

_QUOTA_MARKERS = (
    "insufficient_quota",
    "exceeded your current quota",
    "billing_hard_limit_reached",
    "You exceeded your current quota",
)

_T = TypeVar("_T")


def classify_openai_error(exc: Exception) -> str:
    """
    OpenAI SDK exception'ını canonical hata koduna çevirir.
    Dönen değerler: 'insufficient_quota' | 'rate_limit' | 'auth_error' | 'unknown'
    """
    # Önce yapısal body.code alanı
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        code = body.get("code") or body.get("error", {}).get("code", "")
        if code in ("insufficient_quota", "billing_hard_limit_reached"):
            return "insufficient_quota"
        if code == "rate_limit_exceeded":
            return "rate_limit"

    # HTTP durum kodu
    status = getattr(exc, "status_code", None)
    if status in (401, 403):
        return "auth_error"

    # String eşleme — son çare
    message = str(exc).lower()
    if any(m.lower() in message for m in _QUOTA_MARKERS):
        return "insufficient_quota"
    if status == 429 or "rate_limit" in message or "too many requests" in message:
        return "rate_limit"

    return "unknown"


def with_openai_retry(
    fn: Callable[[], _T],
    *,
    max_attempts: int = 4,
    base_delay: float = 1.0,
    stage: str = "llm",
    job_id: str = "",
) -> _T:
    """
    Exponential backoff ile OpenAI çağrısı yapar.
    insufficient_quota → anında RuntimeError (retry yok).
    rate_limit → 1s → 2s → 4s → 8s + jitter, maks. 4 deneme, toplam bütçe 30s.
    """
    from app.errors.registry import PipelineErrorException

    last_exc: Exception | None = None
    total_waited = 0.0

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"[openai] attempt={attempt}/{max_attempts} stage={stage} job={job_id[:8] if job_id else '-'}")
            return fn()
        except Exception as exc:
            kind = classify_openai_error(exc)
            last_exc = exc

            if kind == "insufficient_quota":
                logger.error(
                    f"[openai] billing_error=insufficient_quota stage={stage} attempt={attempt}/1"
                )
                raise PipelineErrorException(
                    "openai_insufficient_quota",
                    admin_detail={"raw_error": str(exc)[:300], "stage": stage},
                    stage=stage,
                ) from exc

            if kind == "auth_error":
                raise PipelineErrorException(
                    "openai_insufficient_quota",
                    admin_detail={"raw_error": str(exc)[:300], "kind": "auth_error", "stage": stage},
                    stage=stage,
                ) from exc

            if attempt >= max_attempts:
                break

            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            total_waited += delay
            if total_waited > 30:
                break

            logger.warning(
                f"[openai] {kind} · attempt {attempt}/{max_attempts} · retry in {delay:.1f}s"
            )
            time.sleep(delay)

    raise PipelineErrorException(
        "openai_rate_limit" if classify_openai_error(last_exc) == "rate_limit" else "openai_content_invalid",
        admin_detail={"raw_error": str(last_exc)[:300], "attempts": max_attempts, "stage": stage},
        stage=stage,
    ) from last_exc
