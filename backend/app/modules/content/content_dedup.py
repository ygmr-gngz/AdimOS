"""
İçerik tekrar engeli — cosine similarity >= 0.82 eşiğiyle benzer video başlıklarını filtreler.

Gerekli Supabase tablosu:
  content_history (
    id              uuid primary key default gen_random_uuid(),
    job_id          text,
    title           text not null,
    topic           text,
    content_series  text,
    embedding       vector(1536),      -- pgvector gerektirir
    created_at      timestamptz default now()
  )

pgvector yoksa embedding text[] olarak saklanabilir, kosinüs hesabı Python tarafında yapılır.
Bu modül pgvector olmadan da çalışır (Python-side similarity).
"""
import logging
import math
from typing import Optional

from app.db.supabase import get_supabase_client
from app.core.config import settings

logger = logging.getLogger(__name__)

_SIMILARITY_THRESHOLD = 0.82
_EMBED_MODEL          = "text-embedding-3-small"


# ── Embedding üretimi ─────────────────────────────────────────

def _get_embedding(text: str) -> list[float]:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30.0)
    resp = client.embeddings.create(model=_EMBED_MODEL, input=text[:4000])
    return resp.data[0].embedding


def _cosine(a: list[float], b: list[float]) -> float:
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── Tekrar kontrolü ───────────────────────────────────────────

def check_content_duplicate(
    title: str,
    topic: str,
    content_series: Optional[str] = None,
) -> tuple[bool, Optional[str], float]:
    """
    Yeni içerik üretmeden önce benzer bir içerik var mı kontrol eder.

    Returns:
      (is_duplicate, similar_title, similarity_score)
      is_duplicate = True  → üretimi durdur veya kullanıcıyı uyar
    """
    try:
        sb = get_supabase_client()
        q  = sb.table("content_history").select("id, title, topic, embedding")
        if content_series:
            q = q.eq("content_series", content_series)
        history = q.order("created_at", desc=True).limit(200).execute().data or []

        if not history:
            return False, None, 0.0

        query_emb = _get_embedding(f"{title} {topic}")

        best_sim   = 0.0
        best_title = None
        for record in history:
            stored = record.get("embedding")
            if not stored or not isinstance(stored, list):
                continue
            sim = _cosine(query_emb, stored)
            if sim > best_sim:
                best_sim   = sim
                best_title = record["title"]

        if best_sim >= _SIMILARITY_THRESHOLD:
            logger.warning(
                f"[dedup] Benzer içerik: '{best_title}' "
                f"(benzerlik={best_sim:.3f} ≥ eşik={_SIMILARITY_THRESHOLD})"
            )
            return True, best_title, best_sim

        return False, None, best_sim

    except Exception as exc:
        logger.warning(f"[dedup] kontrol başarısız (atlanıyor): {exc}")
        return False, None, 0.0


# ── Parmak izi kaydetme ───────────────────────────────────────

def save_content_fingerprint(
    job_id: str,
    title: str,
    topic: str,
    content_series: Optional[str] = None,
) -> None:
    """
    Üretimi tamamlanan içeriği content_history'ye kaydeder.
    Pipeline sonunda çağrılır — hata halinde loglanır ama pipeline durdurmaz.
    """
    try:
        embedding = _get_embedding(f"{title} {topic}")
        sb = get_supabase_client()
        sb.table("content_history").insert({
            "job_id":         job_id,
            "title":          title,
            "topic":          topic or "",
            "content_series": content_series,
            "embedding":      embedding,
        }).execute()
        logger.info(f"[dedup] parmak izi kaydedildi: job={job_id[:8]}")
    except Exception as exc:
        logger.warning(f"[dedup] parmak izi kayıt hatası: {exc}")
