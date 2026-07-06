"""
Merkezi LLM istemcisi — retry, timeout ve loglama burada.

Tüm OpenAI çağrıları bu modül üzerinden geçer.
Doğrudan `openai.OpenAI()` kullanımı yeni kodlarda yasak.
"""
import json
import logging
import time
from typing import Any

from openai import OpenAI, RateLimitError, APITimeoutError, APIConnectionError, APIStatusError
from app.core.config import settings

logger = logging.getLogger(__name__)

_client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=90.0)

_RETRYABLE = (RateLimitError, APITimeoutError, APIConnectionError)
_BACKOFF = (2, 5, 15)  # saniye — 3 deneme


def chat(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    max_tokens: int = 1500,
    json_mode: bool = False,
    caller: str = "unknown",
) -> str:
    """
    OpenAI chat tamamlama — retry + backoff + timeout.
    json_mode=True → response_format={"type": "json_object"} zorunlu kılar.
    Döndürür: model yanıtının metin içeriği (str).
    """
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    last_error: Exception | None = None
    for attempt, backoff in enumerate((*_BACKOFF, None), 1):
        try:
            t0 = time.monotonic()
            resp = _client.chat.completions.create(**kwargs)
            elapsed = time.monotonic() - t0
            finish = resp.choices[0].finish_reason
            tokens = getattr(resp.usage, "total_tokens", "?")
            logger.info(
                f"[llm/{caller}] model={model} tokens={tokens} "
                f"finish={finish} elapsed={elapsed:.1f}s attempt={attempt}"
            )
            return resp.choices[0].message.content or ""
        except _RETRYABLE as e:
            last_error = e
            if backoff is None:
                break
            logger.warning(
                f"[llm/{caller}] {type(e).__name__} — {backoff}s sonra tekrar (deneme {attempt})"
            )
            time.sleep(backoff)
        except APIStatusError as e:
            logger.error(f"[llm/{caller}] API hatası {e.status_code}: {e.message}")
            raise
        except Exception as e:
            logger.error(f"[llm/{caller}] beklenmedik hata: {e}", exc_info=True)
            raise

    raise RuntimeError(
        f"[llm/{caller}] {max(len(_BACKOFF), 1)} denemede yanıt alınamadı: {last_error}"
    )


def chat_json(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_tokens: int = 2000,
    caller: str = "unknown",
) -> dict:
    """JSON mod kısayolu — otomatik parse + tek seferlik hata-düzeltme denemesi."""
    raw = chat(messages, model=model, temperature=temperature,
               max_tokens=max_tokens, json_mode=True, caller=caller)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning(f"[llm/{caller}] JSON parse hatası, onarım deneniyor: {e}")
        # Tek seferlik "JSON'u düzelt" denemesi
        fix_messages = messages + [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": "Yanıtın geçerli JSON değil. SADECE düzeltilmiş JSON döndür."},
        ]
        raw2 = chat(fix_messages, model=model, temperature=0.0,
                    max_tokens=max_tokens, json_mode=True, caller=f"{caller}/fix")
        return json.loads(raw2)


def embed(text: str) -> list[float]:
    """Tek metin embedding."""
    resp = _client.embeddings.create(model="text-embedding-3-small", input=text)
    return resp.data[0].embedding


def embed_batch(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """Toplu embedding — büyük listeleri batch_size'lık dilimlerle gönderir."""
    results: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        chunk = texts[i:i + batch_size]
        resp = _client.embeddings.create(model="text-embedding-3-small", input=chunk)
        results.extend(item.embedding for item in resp.data)
    return results
