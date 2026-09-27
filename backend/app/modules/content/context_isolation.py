"""Content-generation RAG gate.

Chat RAG may use broad recall. Generated public content must not: weakly related
chunks can silently move a carousel to a previous/adjacent subject. This module
keeps retrieval stateless and only admits evidence tied to the current request.
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from typing import Callable

from app.modules.knowledge.retriever import retrieve
from app.core.config import settings

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "ve", "veya", "ile", "bir", "bu", "şu", "için", "nedir", "nasıl",
    "konusu", "konusunda", "farkı", "arasındaki", "olarak", "olan",
}

_TR_SUFFIXES = (
    "lerinden", "larından", "lerin", "ların", "leri", "ları", "lerden", "lardan",
    "lik", "lık", "luk", "lük", "dan", "den", "tan", "ten", "nin", "nın",
    "nun", "nün", "da", "de", "ta", "te", "yi", "yı", "yu", "yü",
)


class RequiredGroundingError(RuntimeError):
    """Raised when a document-bound request has no admissible evidence."""


def _stem(token: str) -> str:
    for suffix in _TR_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[:-len(suffix)]
    return token


def _tokens(value: str) -> set[str]:
    return {
        _stem(token) for token in re.findall(r"[a-zçğıöşü0-9]+", value.casefold())
        if len(token) >= 3 and token not in _STOPWORDS
    }


@dataclass(frozen=True)
class ContextBundle:
    text: str
    evidence_ids: tuple[str, ...]
    rejected_count: int


def _evidence_id(chunk: dict) -> str:
    raw = str(chunk.get("id") or chunk.get("chunk_id") or chunk.get("document_id") or "")
    if raw:
        return raw
    text = str(chunk.get("content") or chunk.get("chunk_data") or "")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def retrieve_isolated_context(
    topic: str,
    *,
    max_chars: int,
    per_chunk_chars: int,
    generation_id: str = "",
    workspace_id: str | None = None,
    required_grounding: bool = False,
    min_similarity: float | None = None,
    high_confidence_similarity: float | None = None,
    retriever: Callable[..., list[dict]] = retrieve,
) -> ContextBundle:
    """Return only evidence relevant to *this* topic.

    The RPC threshold is intentionally stricter than chat search. A lexical gate
    is also applied because older deployments of ``match_chunks`` did not always
    return a similarity field. Missing similarity therefore cannot bypass topic
    binding.
    """
    minimum = settings.CONTENT_RAG_MIN_SIMILARITY if min_similarity is None else min_similarity
    high_confidence = (
        settings.CONTENT_RAG_HIGH_CONFIDENCE
        if high_confidence_similarity is None else high_confidence_similarity
    )
    if not 0 <= minimum <= high_confidence <= 1:
        raise ValueError("RAG similarity eşikleri 0 <= min <= high <= 1 olmalı")
    scope = workspace_id or settings.CONTENT_WORKSPACE_ID
    topic_tokens = _tokens(topic)
    chunks = retriever(
        topic, match_count=10, match_threshold=minimum, workspace_id=scope,
    )
    accepted: list[str] = []
    evidence_ids: list[str] = []
    rejected = 0
    used = 0

    for chunk in chunks:
        text = str(chunk.get("content") or chunk.get("chunk_data") or "").strip()
        similarity = chunk.get("similarity")
        overlap = topic_tokens & _tokens(text)
        try:
            score = float(similarity) if similarity is not None else None
        except (TypeError, ValueError):
            score = None
        # Hybrid gate: medium-confidence matches need a normalized lexical
        # anchor; genuinely high-confidence semantic matches may bridge terms
        # such as "churn" / "abonelikten ayrılma". Old RPC rows without a
        # similarity score remain fail-safe and require an anchor.
        relevant = bool(text) and (
            (score is not None and score >= high_confidence)
            or (bool(overlap) and (score is None or score >= minimum))
        )
        if not relevant:
            rejected += 1
            continue
        excerpt = text[:per_chunk_chars]
        if used + len(excerpt) > max_chars:
            break
        accepted.append(excerpt)
        evidence_ids.append(_evidence_id(chunk))
        used += len(excerpt)

    logger.info(
        "[content-context] generation=%s workspace_hash=%s topic_hash=%s accepted=%d rejected=%d evidence=%s",
        generation_id[:12] or "unassigned",
        hashlib.sha256(scope.encode("utf-8")).hexdigest()[:12],
        hashlib.sha256(topic.casefold().strip().encode("utf-8")).hexdigest()[:12],
        len(accepted), rejected, evidence_ids,
    )
    if required_grounding and not accepted:
        raise RequiredGroundingError(
            "required_grounding_missing: İstek belgeye bağlı ancak ilgili kaynak bulunamadı"
        )
    fallback = (
        f"{topic} için yeterince ilgili kurum içi kaynak bulunamadı; "
        "yalnızca yerleşik temel bilgiyi kullan."
    )
    return ContextBundle("\n\n".join(accepted) if accepted else fallback, tuple(evidence_ids), rejected)
