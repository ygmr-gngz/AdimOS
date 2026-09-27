"""Premium 4:5 Instagram carousel üretimi: içerik planı + raster PNG seti."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import re
import time
import uuid
from typing import Any

from openai import OpenAI
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings
from app.core.llm_client import chat_json as llm_json
from app.core.visual_manifest import PROD_MODEL, PROD_QUALITY
from app.modules.content.storage import IMAGE_BUCKET, upload_bytes
from app.modules.content.context_isolation import ContextBundle, retrieve_isolated_context

logger = logging.getLogger(__name__)

CAROUSEL_MODES = {
    "illustrated", "mind_map", "process", "accounting_solution",
    "comparison", "formula_example", "exam_tip",
}

_PLAN_SYSTEM = """Sen deneyimli bir Türk muhasebe eğitmeni ve içerik editörüsün.
Hedef konuya semantik olarak uymayan kaynak parçalarını kesinlikle kullanma; alakasız
RAG bağlamı yerine yerleşik muhasebe bilgini kullan. Kaynakta bulunmayan güncel oran,
hesap kodu veya mevzuat hükmü uydurma. Mobil ekranda okunacak kısa metinler yaz.
Yalnızca geçerli JSON döndür."""

_PLAN_PROMPT = """'{topic}' konusunda altı kartlık Instagram eğitim carousel'i hazırla.

KAYNAK:
{context}

VURGU: {mode}
KONUYA ÖZEL ZORUNLU KURAL:
{guardrails}

Tam olarak şu JSON şemasını doldur:
{{
  "topic": "kısa konu adı",
  "cards": [
    {{"kind":"hook", "title":"çarpıcı ama doğru soru", "subtitle":"tek cümle vaat", "bullets":[], "visual_intent":{{"semantic_focus":"tek özgül kavram", "visual_concept":"kapak metaforu", "subjects":["ana nesne"], "action":"görsel eylem", "environment":"özgül ortam", "symbols":["özgül sembol"], "search_query":"konuya özel benzersiz görsel sorgu", "avoid":["diğer kartların ana metaforları"]}}}},
    {{"kind":"overview", "title":"konunun özeti", "subtitle":"girdi-işlem-çıktı veya kavram haritası", "bullets":["en çok 4 kısa madde"], "visual_intent":{{"semantic_focus":"...", "visual_concept":"...", "subjects":["..."], "action":"...", "environment":"...", "symbols":["..."], "search_query":"...", "avoid":["..."]}}}},
    {{"kind":"worked_example", "title":"Çözümlü Örnek", "subtitle":"kısa senaryo", "bullets":["Verilen", "İşlem", "Sonuç"], "visual_intent":{{"semantic_focus":"...", "visual_concept":"...", "subjects":["..."], "action":"...", "environment":"...", "symbols":["..."], "search_query":"...", "avoid":["..."]}}}},
    {{"kind":"account_application", "title":"Muhasebe Kaydı / Uygulama", "subtitle":"konuya uygunsa borç-alacak kaydı, değilse uygulama tablosu", "bullets":["en çok 4 satır"], "visual_intent":{{"semantic_focus":"...", "visual_concept":"...", "subjects":["..."], "action":"...", "environment":"...", "symbols":["..."], "search_query":"...", "avoid":["..."]}}}},
    {{"kind":"common_mistake", "title":"Sık Yapılan Hata", "subtitle":"yanlış ve doğru yaklaşım", "bullets":["Yanlış: ...", "Doğru: ..."], "visual_intent":{{"semantic_focus":"...", "visual_concept":"...", "subjects":["..."], "action":"...", "environment":"...", "symbols":["..."], "search_query":"...", "avoid":["..."]}}}},
    {{"kind":"exam_tip", "title":"Sınav İpucu", "subtitle":"tek cümle hafıza kancası", "bullets":["Kaydet • Tekrar et"], "visual_intent":{{"semantic_focus":"...", "visual_concept":"...", "subjects":["..."], "action":"...", "environment":"...", "symbols":["..."], "search_query":"...", "avoid":["..."]}}}}
  ]
}}

Kurallar:
- cards sırası ve kind değerleri birebir aynı, kart sayısı tam 6.
- Her title en fazla 7 kelime, subtitle en fazla 16 kelime.
- Her bullet en fazla 12 kelime; toplam metni seyrek tut.
- Sayısal örnek kendi içinde tutarlı olsun.
- Muhasebe kaydında borç ve alacak toplamları eşit olsun.
- Konuyu komşu bir başlığa kaydırma: her kart yalnızca TAM OLARAK '{topic}' konusunu öğretmeli.
- Konuya doğal bir yevmiye kaydı yoksa kayıt UYDURMA; 4. kartta uygulama/miktar akış tablosu kullan.
- Çözümlü örnekte verilen her sayı işlemde kullanılmalı ve sonuç aritmetik olarak doğrulanmalı.
- Türkçe yaz; emoji, hashtag ve kaynakta olmayan iddia kullanma."""

_AUDIT_PROMPT = """Aşağıdaki altı kartlık planı bağımsız bir kıdemli muhasebe editörü olarak denetle.
Konu dışına kayan kavramı, uydurma yevmiye kaydını, eşit olmayan borç/alacağı,
kullanılmayan sayıyı ve hatalı aritmetiği düzelt. Metinleri kısa tut.

HEDEF KONU: {topic}
KONUYA ÖZEL ZORUNLU KURAL: {guardrails}
KAYNAK:
{context}

PLAN:
{plan}

İlk plandaki aynı JSON şemasında yalnızca düzeltilmiş planı döndür. Kart sayısı,
sırası ve kind değerleri değişmesin. Konuya doğal kayıt yoksa 4. kart uygulama
tablosu olsun; sırf şemada geçtiği için muhasebe kaydı uydurma."""

_MODE_LABELS = {
    "illustrated": "el çizimi girdi-işlem-çıktı anlatımı",
    "mind_map": "kavramlar arası bağlantılar",
    "process": "adımlar ve neden-sonuç ilişkisi",
    "accounting_solution": "çözümlü işlem ve yevmiye mantığı",
    "comparison": "karıştırılan kavramların karşılaştırılması",
    "formula_example": "formül ve sayısal örnek",
    "exam_tip": "sık hata ve sınav hafıza tekniği",
}

_KINDS = ["hook", "overview", "worked_example", "account_application", "common_mistake", "exam_tip"]
_INTENT_JACCARD_LIMIT = 0.72
_DHASH_MIN_DISTANCE = 8
_MAX_IMAGE_ATTEMPTS_PER_SLIDE = 3
_VISUAL_FAMILIES = {
    "computer_workspace": {
        "laptop", "computer", "bilgisayar", "developer", "engineer", "coding", "code",
        "editor", "desk", "masa", "workstation",
    },
    "factory_line": {"factory", "fabrika", "production", "üretim", "line", "hat", "conveyor"},
    "sewing_detail": {"needle", "iğne", "sewing", "dikiş"},
    "fabric_inspection": {"fabric", "kumaş", "textile", "tekstil", "defect", "kusur"},
    "logistics": {"shipping", "container", "konteyner", "cargo", "lojistik", "sevkiyat"},
    "retail": {"retail", "mağaza", "clothing", "giysi", "rack", "askı", "raf"},
}


def _topic_guardrails(topic: str) -> str:
    normalized = topic.casefold()
    if "safha" in normalized and "miktar" in normalized:
        return (
            "Bu içerik MALİYET TUTARINI değil FİZİKİ MİKTAR DENGESİNİ öğretmeli. "
            "2-4. kartlarda 'DBYM + Dönemde üretime başlanan = Tamamlanan + DSYM' "
            "eşitliği açıkça yer almalı. Sayısal örnek: DBYM 10.000 + Başlanan "
            "15.000 = Tamamlanan 20.000 + DSYM 5.000; iki taraf da 25.000. "
            "Normal/değişken maliyet, kapasite oranı ve yevmiye kaydı bu konunun "
            "dışındadır; kesinlikle kullanma. 4. kart miktar akış tablosu olmalı."
        )
    if "kdv" in normalized and "ticari mal" in normalized and "alış" in normalized:
        return (
            "Ticari mal alış kaydında 153 Ticari Mallar ve 191 İndirilecek KDV "
            "BORÇ, 320 Satıcılar toplam tutar kadar ALACAK çalışır; borç ve alacak "
            "eşit olmalı. Toplam tutara 'borç kaydı' deme. Vergi oranını güncel genel "
            "kural gibi sunma; kaynakta örnek oran varsa 'örnekte verilen oran' de. "
            "Hata kartında doğru yaklaşım 'KDV'yi verilen oranla hesaplamak' olmalı."
        )
    return "Hedef konunun tanım, uygulama ve sınav mantığından ayrılma."


def _context(topic: str, max_chars: int = 3200) -> str:
    return _context_bundle(topic, max_chars=max_chars).text


def _context_bundle(
    topic: str, max_chars: int = 3200, generation_id: str = "",
    required_grounding: bool = False,
) -> ContextBundle:
    return retrieve_isolated_context(
        topic, max_chars=max_chars, per_chunk_chars=700,
        generation_id=generation_id,
        required_grounding=required_grounding,
    )


def _words(value: str) -> set[str]:
    return set(re.findall(r"[a-zçğıöşü0-9]+", value.casefold()))


def _similarity(left: str, right: str) -> float:
    a, b = _words(left), _words(right)
    return len(a & b) / len(a | b) if a and b else 0.0


def _visual_families(value: str) -> set[str]:
    words = _words(value)
    return {name for name, vocabulary in _VISUAL_FAMILIES.items() if words & vocabulary}


def _intent_text(card: dict[str, Any]) -> str:
    intent = card.get("visual_intent") or {}
    return " ".join(str(intent.get(key) or "") for key in (
        "semantic_focus", "visual_concept", "action", "environment", "search_query",
    ))


def _family_text(card: dict[str, Any]) -> str:
    """Central depiction only; exclude topic-bearing focus/query boilerplate."""
    intent = card.get("visual_intent") or {}
    return " ".join(str(intent.get(key) or "") for key in (
        "visual_concept", "action", "environment",
    ))


def validate_carousel_plan(plan: dict[str, Any]) -> None:
    cards = plan.get("cards") or []
    if len(cards) != 6 or [card.get("kind") for card in cards] != _KINDS:
        raise RuntimeError("carousel_plan_invalid: altı kartın sırası veya türü hatalı")
    for index, card in enumerate(cards, 1):
        if not str(card.get("title") or "").strip():
            raise RuntimeError(f"carousel_plan_invalid: kart {index} başlıksız")
        bullets = card.get("bullets") or []
        if not isinstance(bullets, list) or len(bullets) > 4:
            raise RuntimeError(f"carousel_plan_invalid: kart {index} madde sayısı hatalı")
        intent = card.get("visual_intent") or {}
        required = ("semantic_focus", "visual_concept", "action", "environment", "search_query")
        if any(not str(intent.get(field) or "").strip() for field in required):
            raise RuntimeError(f"carousel_plan_invalid: kart {index} visual_intent eksik")
    intents = [_intent_text(card) for card in cards]
    family_texts = [_family_text(card) for card in cards]
    family_counts: dict[str, int] = {}
    for index, current in enumerate(intents):
        for previous in intents[:index]:
            if _similarity(current, previous) >= _INTENT_JACCARD_LIMIT:
                raise RuntimeError(
                    f"carousel_plan_invalid: kart {index + 1} görsel niyeti önceki kartla fazla benzer"
                )
        for family in _visual_families(family_texts[index]):
            family_counts[family] = family_counts.get(family, 0) + 1
            # Laptop/desk imagery is the proven generic collapse. Broad domain
            # families (e.g. several textile process cards) are not a duplicate
            # by themselves; Jaccard + rendered dHash handle those cases.
            if family == "computer_workspace" and family_counts[family] > 1:
                raise RuntimeError(
                    f"carousel_plan_invalid: kart {index + 1} görsel ailesi fazla tekrarlandı"
                )


def generate_carousel_plan(
    topic: str, mode: str, *, generation_id: str = "", required_grounding: bool = False,
) -> dict[str, Any]:
    if mode not in CAROUSEL_MODES:
        raise ValueError(f"Desteklenmeyen premium carousel modu: {mode}")
    context_bundle = _context_bundle(
        topic, generation_id=generation_id, required_grounding=required_grounding,
    )
    context = context_bundle.text
    plan = llm_json(
        messages=[
            {"role": "system", "content": _PLAN_SYSTEM},
            {"role": "user", "content": _PLAN_PROMPT.format(
                topic=topic, context=context, mode=_MODE_LABELS[mode],
                guardrails=_topic_guardrails(topic),
            )},
        ],
        model="gpt-4o",
        temperature=0.25,
        max_tokens=1800,
        caller="illustrated_carousel/plan",
    )
    validate_carousel_plan(plan)
    # Görsel üretimi pahalıdır; konu ve matematik hatalarını ikinci, bağımsız
    # editör geçişinde düzeltmeden image API'ye hiçbir şey gönderme.
    audited = llm_json(
        messages=[
            {"role": "system", "content": _PLAN_SYSTEM},
            {"role": "user", "content": _AUDIT_PROMPT.format(
                topic=topic,
                guardrails=_topic_guardrails(topic),
                context=context,
                plan=json.dumps(plan, ensure_ascii=False),
            )},
        ],
        model="gpt-4o",
        temperature=0.0,
        max_tokens=1800,
        caller="illustrated_carousel/audit",
    )
    validate_carousel_plan(audited)
    # The request is the source of truth; never trust the model to rename it.
    audited["topic"] = topic
    audited["generation_debug"] = {
        "generation_id": generation_id,
        "topic_hash": hashlib.sha256(topic.casefold().strip().encode("utf-8")).hexdigest()[:12],
        "context_hash": hashlib.sha256(context.encode("utf-8")).hexdigest()[:12],
        "context_evidence_ids": list(context_bundle.evidence_ids),
        "context_rejected_count": context_bundle.rejected_count,
        "cache_hit": False,
        "slides": [
            {
                "slide_id": f"{generation_id or 'pending'}:{index}",
                "semantic_focus_hash": hashlib.sha256(
                    str((card.get("visual_intent") or {}).get("semantic_focus") or "").encode("utf-8")
                ).hexdigest()[:12],
                "image_query_hash": hashlib.sha256(
                    str((card.get("visual_intent") or {}).get("search_query") or "").encode("utf-8")
                ).hexdigest()[:12],
            }
            for index, card in enumerate(audited["cards"], 1)
        ],
    }
    return audited


def _card_prompt(topic: str, card: dict[str, Any], index: int, diversity_note: str = "") -> str:
    bullets = "\n".join(f"- {item}" for item in card.get("bullets") or []) or "- Metin maddesi yok"
    role = {
        "hook": "Strong cover with one central metaphor and generous negative space.",
        "overview": "Hand-drawn systems overview with a central machine, labeled inputs and outputs, curved arrows.",
        "worked_example": "Worked example shown as three clear panels: given, calculation, result.",
        "account_application": "A clean application card or table chosen only from the supplied exact lines. Do not reuse facts, numbers, account labels or abbreviations from any other subject. If the supplied lines describe steps, show a numbered process; if they describe a journal entry, show balanced debit and credit columns; otherwise use a neutral two-column application table.",
        "common_mistake": "Split comparison: muted red wrong side and calm green correct side. Use only the supplied wrong/right sentences; do not invent captions inside illustrations.",
        "exam_tip": "Memorable exam tip with a small lightbulb, mnemonic ribbon and save reminder.",
    }[card["kind"]]
    intent = card.get("visual_intent") or {}
    return f"""Create slide {index} of 6 for a premium Turkish accounting education Instagram carousel.

SUBJECT: {topic}
EXACT TITLE: {card['title']}
EXACT SUBTITLE: {card.get('subtitle') or ''}
EXACT SHORT LINES:
{bullets}

COMPOSITION: {role}
SLIDE PURPOSE: {intent.get('semantic_focus', '')}
UNIQUE VISUAL CONCEPT: {intent.get('visual_concept', '')}
SUBJECTS: {', '.join(intent.get('subjects') or [])}
ACTION: {intent.get('action', '')}
ENVIRONMENT: {intent.get('environment', '')}
SYMBOLS: {', '.join(intent.get('symbols') or [])}
VISUAL QUERY: {intent.get('search_query', '')}
DO NOT SHOW: {', '.join(intent.get('avoid') or [])}
GENERATION-SPECIFIC DIVERSITY NOTE: {diversity_note or 'No previous rendered card is available.'}

STYLE CONTRACT: 4:5 portrait educational poster, warm ivory recycled-paper background,
hand-drawn black ink linework, editorial sketchbook infographic, restrained pastel teal,
powder blue, sage green and warm orange accents, subtle imperfect arrows and small doodles,
high-end human-made art direction, clear hierarchy, ample breathing room. Keep all important
content inside the central 83 percent vertically because the source will be cropped to 4:5.
Use correct Turkish characters and reproduce only the supplied text. Add a tiny unobtrusive
@adimmusavir signature at the bottom. No Instagram interface, no phone mockup, no photograph,
no 3D render, no dark navy background, no neon, no gradients, no watermark, no extra claims,
no gibberish, no tiny paragraphs. The result must look like one consistent series with the
other five slides, while using a clearly different central subject, action and composition."""


def _to_instagram_4x5(source: bytes) -> bytes:
    try:
        opened = Image.open(io.BytesIO(source))
    except (UnidentifiedImageError, OSError) as exc:
        raise RuntimeError("carousel_image_invalid: image API geçersiz görsel döndürdü") from exc
    with opened as original:
        original.seek(0)  # animated inputs: deterministic first frame
        image = ImageOps.exif_transpose(original)
        if image.width < 32 or image.height < 32:
            raise RuntimeError("carousel_image_invalid: görsel boyutu çok küçük")
        if image.mode in ("RGBA", "LA") or "transparency" in image.info:
            rgba = image.convert("RGBA")
            background = Image.new("RGBA", rgba.size, "white")
            image = Image.alpha_composite(background, rgba).convert("RGB")
        else:
            image = image.convert("RGB")
        target_ratio = 4 / 5
        crop_height = round(image.width / target_ratio)
        if crop_height <= image.height:
            top = (image.height - crop_height) // 2
            image = image.crop((0, top, image.width, top + crop_height))
        else:
            crop_width = round(image.height * target_ratio)
            left = (image.width - crop_width) // 2
            image = image.crop((left, 0, left + crop_width, image.height))
        image = image.resize((1080, 1350), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format="PNG", optimize=True)
        return output.getvalue()


def _difference_hash(png: bytes) -> int:
    """Small dependency-free perceptual hash used only inside one generation."""
    try:
        opened = Image.open(io.BytesIO(png))
    except (UnidentifiedImageError, OSError) as exc:
        raise RuntimeError("carousel_image_invalid: perceptual hash hesaplanamadı") from exc
    with opened as original:
        original.seek(0)
        image = ImageOps.exif_transpose(original).convert("L")
        pixels = list(image.resize((9, 8), Image.Resampling.LANCZOS).getdata())
    bits = 0
    for row in range(8):
        for column in range(8):
            bits = (bits << 1) | int(pixels[row * 9 + column] > pixels[row * 9 + column + 1])
    return bits


def _hash_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def _generate_card_bytes(
    topic: str,
    card: dict[str, Any],
    index: int,
    *,
    client: OpenAI,
    diversity_note: str = "",
) -> bytes:
    response = client.images.generate(
        model=PROD_MODEL,
        prompt=_card_prompt(topic, card, index, diversity_note),
        n=1,
        size="1024x1536",
        quality=PROD_QUALITY,
        output_format="png",
    )
    return _to_instagram_4x5(base64.b64decode(response.data[0].b64_json))


def generate_carousel_pngs(
    job_id: str,
    topic: str,
    mode: str,
    *,
    plan: dict[str, Any] | None = None,
    client: OpenAI | None = None,
    required_grounding: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """Altı bağımsız PNG üretir, Storage'a yükler ve URL listesini döndürür."""
    plan = plan or generate_carousel_plan(
        topic, mode, generation_id=job_id, required_grounding=required_grounding,
    )
    validate_carousel_plan(plan)
    image_client = client or OpenAI(api_key=settings.OPENAI_API_KEY, timeout=180.0)
    urls: list[str] = []
    hashes: list[int] = []
    used_concepts: list[str] = []
    for index, card in enumerate(plan["cards"], 1):
        started = time.monotonic()
        png = b""
        card_hash = 0
        best: tuple[int, bytes, int] | None = None  # nearest distance, png, hash
        dedup_exhausted = False
        attempts_used = 0
        for attempt in range(_MAX_IMAGE_ATTEMPTS_PER_SLIDE):
            attempts_used = attempt + 1
            note = ""
            if used_concepts:
                note = (
                    "Previous cards already used these concepts: "
                    + " | ".join(used_concepts)
                    + ". Do not repeat their central object, silhouette, spatial layout or metaphor."
                )
            png = _generate_card_bytes(topic, card, index, client=image_client, diversity_note=note)
            card_hash = _difference_hash(png)
            nearest = min((_hash_distance(card_hash, old) for old in hashes), default=64)
            if best is None or nearest > best[0]:
                best = (nearest, png, card_hash)
            if nearest >= _DHASH_MIN_DISTANCE:
                break
            logger.warning(
                "[carousel] generation=%s card=%d perceptual_duplicate distance=%d retry=%d",
                job_id[:12], index, nearest, attempt + 1,
            )
        else:
            # Quality control must not turn into an availability outage. Keep
            # the least-similar bounded attempt and make the residual risk visible.
            assert best is not None
            dedup_exhausted = True
            nearest, png, card_hash = best
            logger.error(
                "[carousel] generation=%s card=%d dedup_exhausted best_distance=%d attempts=%d",
                job_id[:12], index, nearest, _MAX_IMAGE_ATTEMPTS_PER_SLIDE,
            )
        remote_path = f"carousel/{job_id}/{index:02d}-{uuid.uuid4().hex[:8]}.png"
        urls.append(upload_bytes(png, IMAGE_BUCKET, remote_path, "image/png"))
        hashes.append(card_hash)
        used_concepts.append(str((card.get("visual_intent") or {}).get("visual_concept") or card["title"]))
        debug_slides = (plan.get("generation_debug") or {}).get("slides") or []
        if len(debug_slides) >= index:
            debug_slides[index - 1].update({
                "selected_asset_id": remote_path,
                "perceptual_hash": f"{card_hash:016x}",
                "image_attempts": attempts_used,
                "retry_count": attempts_used - 1,
                "dedup_exhausted": dedup_exhausted,
            })
        logger.info(
            "[carousel] generation=%s card=%d/6 concept_hash=%s image_dhash=%016x %.1fs",
            job_id[:12], index,
            hashlib.sha256(used_concepts[-1].encode("utf-8")).hexdigest()[:10],
            card_hash, time.monotonic() - started,
        )
    return plan, urls


def generate_carousel_card_png(
    job_id: str,
    topic: str,
    card: dict[str, Any],
    index: int,
    *,
    client: OpenAI | None = None,
) -> str:
    """Tek kartı yeniden üretme/QA için kullanılan düşük seviyeli giriş."""
    if card.get("kind") not in _KINDS or not 1 <= index <= 6:
        raise ValueError("Geçersiz carousel kartı veya sırası")
    image_client = client or OpenAI(api_key=settings.OPENAI_API_KEY, timeout=180.0)
    started = time.monotonic()
    png = _generate_card_bytes(topic, card, index, client=image_client)
    remote_path = f"carousel/{job_id}/{index:02d}-{uuid.uuid4().hex[:8]}.png"
    url = upload_bytes(png, IMAGE_BUCKET, remote_path, "image/png")
    logger.info("[carousel] %s kart=%d/6 %.1fs", job_id[:8], index, time.monotonic() - started)
    return url
