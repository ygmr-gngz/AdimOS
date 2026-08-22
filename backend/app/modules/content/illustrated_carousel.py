"""Premium 4:5 Instagram carousel üretimi: içerik planı + raster PNG seti."""
from __future__ import annotations

import base64
import io
import logging
import time
import uuid
from typing import Any

from openai import OpenAI
from PIL import Image

from app.core.config import settings
from app.core.llm_client import chat_json as llm_json
from app.core.visual_manifest import PROD_MODEL, PROD_QUALITY
from app.modules.content.storage import IMAGE_BUCKET, upload_bytes
from app.modules.knowledge.retriever import retrieve

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
    {{"kind":"hook", "title":"çarpıcı ama doğru soru", "subtitle":"tek cümle vaat", "bullets":[]}},
    {{"kind":"overview", "title":"konunun özeti", "subtitle":"girdi-işlem-çıktı veya kavram haritası", "bullets":["en çok 4 kısa madde"]}},
    {{"kind":"worked_example", "title":"Çözümlü Örnek", "subtitle":"kısa senaryo", "bullets":["Verilen", "İşlem", "Sonuç"]}},
    {{"kind":"account_application", "title":"Muhasebe Kaydı / Uygulama", "subtitle":"konuya uygunsa borç-alacak kaydı, değilse uygulama tablosu", "bullets":["en çok 4 satır"]}},
    {{"kind":"common_mistake", "title":"Sık Yapılan Hata", "subtitle":"yanlış ve doğru yaklaşım", "bullets":["Yanlış: ...", "Doğru: ..."]}},
    {{"kind":"exam_tip", "title":"Sınav İpucu", "subtitle":"tek cümle hafıza kancası", "bullets":["Kaydet • Tekrar et"]}}
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
    return "Hedef konunun tanım, uygulama ve sınav mantığından ayrılma."


def _context(topic: str, max_chars: int = 3200) -> str:
    chunks = retrieve(topic, match_count=8, match_threshold=0.25)
    if not chunks:
        return f"{topic} için kurum içi kaynak bulunamadı; yalnızca yerleşik temel bilgiyi kullan."
    result: list[str] = []
    used = 0
    for chunk in chunks:
        text = str(chunk.get("content") or chunk.get("chunk_data") or "")[:700]
        if used + len(text) > max_chars:
            break
        result.append(text)
        used += len(text)
    return "\n\n".join(result)


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


def generate_carousel_plan(topic: str, mode: str) -> dict[str, Any]:
    if mode not in CAROUSEL_MODES:
        raise ValueError(f"Desteklenmeyen premium carousel modu: {mode}")
    context = _context(topic)
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
                plan=__import__("json").dumps(plan, ensure_ascii=False),
            )},
        ],
        model="gpt-4o",
        temperature=0.0,
        max_tokens=1800,
        caller="illustrated_carousel/audit",
    )
    validate_carousel_plan(audited)
    return audited


def _card_prompt(topic: str, card: dict[str, Any], index: int) -> str:
    bullets = "\n".join(f"- {item}" for item in card.get("bullets") or []) or "- Metin maddesi yok"
    role = {
        "hook": "Strong cover with one central metaphor and generous negative space.",
        "overview": "Hand-drawn systems overview with a central machine, labeled inputs and outputs, curved arrows.",
        "worked_example": "Worked example shown as three clear panels: given, calculation, result.",
        "account_application": "A physical quantity-flow reconciliation table with exactly two filled columns. Left column GİRDİLER contains DBYM 10.000 and Başlanan 15.000, total 25.000. Right column ÇIKTILAR contains Tamamlanan 20.000 and DSYM 5.000, total 25.000. Never place output items in the left column. No arrows between individual rows. Never use debit, credit, borç, alacak, debet or kredi because this is not a journal entry.",
        "common_mistake": "Split comparison: muted red wrong side and calm green correct side. Use only the supplied wrong/right sentences; do not invent captions inside illustrations.",
        "exam_tip": "Memorable exam tip with a small lightbulb, mnemonic ribbon and save reminder.",
    }[card["kind"]]
    return f"""Create slide {index} of 6 for a premium Turkish accounting education Instagram carousel.

SUBJECT: {topic}
EXACT TITLE: {card['title']}
EXACT SUBTITLE: {card.get('subtitle') or ''}
EXACT SHORT LINES:
{bullets}

COMPOSITION: {role}

STYLE CONTRACT: 4:5 portrait educational poster, warm ivory recycled-paper background,
hand-drawn black ink linework, editorial sketchbook infographic, restrained pastel teal,
powder blue, sage green and warm orange accents, subtle imperfect arrows and small doodles,
high-end human-made art direction, clear hierarchy, ample breathing room. Keep all important
content inside the central 83 percent vertically because the source will be cropped to 4:5.
Use correct Turkish characters and reproduce only the supplied text. Add a tiny unobtrusive
@adimmusavir signature at the bottom. No Instagram interface, no phone mockup, no photograph,
no 3D render, no dark navy background, no neon, no gradients, no watermark, no extra claims,
no gibberish, no tiny paragraphs. The result must look like one consistent series with the
other five slides."""


def _to_instagram_4x5(source: bytes) -> bytes:
    with Image.open(io.BytesIO(source)) as image:
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


def generate_carousel_pngs(
    job_id: str,
    topic: str,
    mode: str,
    *,
    plan: dict[str, Any] | None = None,
    client: OpenAI | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Altı bağımsız PNG üretir, Storage'a yükler ve URL listesini döndürür."""
    plan = plan or generate_carousel_plan(topic, mode)
    validate_carousel_plan(plan)
    image_client = client or OpenAI(api_key=settings.OPENAI_API_KEY, timeout=180.0)
    urls: list[str] = []
    for index, card in enumerate(plan["cards"], 1):
        urls.append(generate_carousel_card_png(job_id, topic, card, index, client=image_client))
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
    response = image_client.images.generate(
        model=PROD_MODEL,
        prompt=_card_prompt(topic, card, index),
        n=1,
        size="1024x1536",
        quality=PROD_QUALITY,
        output_format="png",
    )
    raw = base64.b64decode(response.data[0].b64_json)
    png = _to_instagram_4x5(raw)
    remote_path = f"carousel/{job_id}/{index:02d}-{uuid.uuid4().hex[:8]}.png"
    url = upload_bytes(png, IMAGE_BUCKET, remote_path, "image/png")
    logger.info("[carousel] %s kart=%d/6 %.1fs", job_id[:8], index, time.monotonic() - started)
    return url
