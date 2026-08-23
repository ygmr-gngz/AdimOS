"""Reels/Shorts için konuya özel animasyonlu illüstrasyon ve tek-soru akışları."""
from __future__ import annotations

import base64
import io
import logging
import uuid
from typing import Any

from openai import OpenAI
from PIL import Image

from app.core.config import settings
from app.core.visual_manifest import PROD_MODEL, PROD_QUALITY
from app.modules.content.storage import IMAGE_BUCKET, upload_bytes

logger = logging.getLogger(__name__)


def build_single_question_reel(
    *, title: str, topic: str, subject: str, question: dict[str, Any], brand: dict[str, Any]
) -> dict[str, Any]:
    options = question.get("options") or []
    labels = [str(option.get("label") or "").upper() for option in options]
    if labels != ["A", "B", "C", "D", "E"] or any(not str(o.get("text") or "").strip() for o in options):
        raise ValueError("Tek-soru Reels için A-E şıkları eksiksiz olmalı")
    correct = str(question.get("correct_label") or "").upper()
    if correct not in labels:
        raise ValueError("Tek-soru Reels doğru cevabı A-E arasında olmalı")
    explanation = str(question.get("explanation") or "Doğru seçeneği konu kuralıyla birlikte hatırla.").strip()
    question_text = str(question.get("text") or "").strip()
    memory_hook = explanation.split(".")[0].strip() or explanation
    scenes = [
        {
            "id": 1, "component": "ReelHookScene", "segment_type": "hook", "visual_source": "text_only",
            "hook_text": "Bunu gerçekten anladın mı?", "highlight_stat": "1 SORU",
            "voice_text": f"{topic} konusunda zorlandığın noktayı tek soruda netleştirelim.",
        },
        {
            "id": 2, "component": "ReelQuestionScene", "segment_type": "question", "visual_source": "text_only",
            "title": "Önce sen cevapla", "question_text": question_text, "options": options,
            "correct_label": correct,
            "voice_text": f"{question_text} Beş şık ekranda. Cevabını seçmek için birkaç saniye düşün.",
        },
        {
            "id": 3, "component": "ReelAnswerScene", "segment_type": "answer", "visual_source": "text_only",
            "title": f"Doğru cevap: {correct}", "options": options, "correct_label": correct,
            "explanation": explanation, "memory_hook": memory_hook,
            "voice_text": f"Doğru cevap {correct} şıkkı. {explanation} Akılda tut: {memory_hook}.",
        },
        {
            "id": 4, "component": "ReelCtaScene", "segment_type": "outro", "visual_source": "text_only",
            "title": "Şimdi gerçekten biliyorsun", "cta_text": "Zorlandığın konuyu yaz",
            "voice_text": "Anlamadığın konuyu yaz; onu da mantığıyla açıklayalım. @adimmusavir",
        },
    ]
    return {
        "video_type": "reel", "title": title, "lesson_name": subject, "topic": topic,
        "format": "9:16", "language": "tr", "brand": brand, "reel_mode": "single_question", "scenes": scenes,
    }


def _to_reel_portrait(source: bytes) -> bytes:
    with Image.open(io.BytesIO(source)) as image:
        image = image.convert("RGB")
        target_ratio = 9 / 16
        crop_width = round(image.height * target_ratio)
        if crop_width <= image.width:
            left = (image.width - crop_width) // 2
            image = image.crop((left, 0, left + crop_width, image.height))
        image = image.resize((1080, 1920), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format="PNG", optimize=True)
        return output.getvalue()


def _illustration_prompt(topic: str, scene: dict[str, Any]) -> str:
    facts = "\n".join(str(x) for x in (scene.get("bullet_points") or []))
    return f"""Create one premium vertical educational illustration for a Turkish accounting Reel.
SUBJECT: {topic}
SCENE TITLE: {scene.get('title') or scene.get('hook_text') or topic}
FACTS TO VISUALIZE: {facts or scene.get('voice_text', '')[:500]}

Match this art direction: warm white graph-paper background, one blank pastel sticky-note
shape in the center, hand-drawn black ink accounting doodles and curved arrows arranged around
it, restrained yellow, teal, sage and powder-blue accents, sparse editorial explainer Reel,
polished human-made composition, generous negative space. Every object should have a clear
teaching role and be visually separable for subtle motion. NO words, NO letters, NO numbers,
NO captions, NO watermark, NO logo, NO photograph, NO 3D, NO dark background. Keep the top
22 percent and bottom 15 percent empty. The center must remain uncluttered enough for one
short Turkish rule to be overlaid later by code."""


def add_animated_illustrations(
    storyboard: dict[str, Any], *, job_id: str, topic: str, client: OpenAI | None = None, limit: int = 5
) -> dict[str, Any]:
    """En öğretici üç sahneye metinsiz illüstrasyon üretip animasyon metadata'sı ekler."""
    # TableScene/JournalEntryScene gibi yapısal kartlar gerçek Remotion
    # bileşeni olarak kalır; yapay görsele çevrilmez. Böylece tablo çizgileri
    # ve hücre metinleri deterministik, okunaklı ve sabit kalır.
    candidates = [
        s for s in storyboard.get("scenes", [])
        if s.get("component") in {
            "ReelConceptScene", "ReelExampleScene", "ReelMistakeScene", "ReelExamTipScene",
        }
    ][:limit]
    image_client = client or OpenAI(api_key=settings.OPENAI_API_KEY, timeout=180.0)
    for order, scene in enumerate(candidates, 1):
        response = image_client.images.generate(
            model=PROD_MODEL, prompt=_illustration_prompt(topic, scene), n=1,
            size="1024x1536", quality=PROD_QUALITY, output_format="png",
        )
        png = _to_reel_portrait(base64.b64decode(response.data[0].b64_json))
        path = f"reel-illustrations/{job_id}/{order:02d}-{uuid.uuid4().hex[:8]}.png"
        url = upload_bytes(png, IMAGE_BUCKET, path, "image/png")
        scene["original_component"] = scene.get("component")
        scene["component"] = "AnimatedIllustrationScene"
        scene["visual_source"] = "photo"
        scene["illustration_url"] = url
        scene["animation_preset"] = ("draw_reveal", "parallax_parts", "focus_pulse")[order - 1]
        takeaway = (
            scene.get("exam_tip") or scene.get("common_mistake")
            or (scene.get("bullet_points") or [scene.get("title") or topic])[0]
        )
        scene["key_takeaway"] = str(takeaway).strip()[:120]
        scene["save_label"] = "HIZLI BİLGİ • KAYDET"
        logger.info("[reel-illustration] job=%s scene=%s preset=%s", job_id[:8], scene.get("id"), scene["animation_preset"])
    storyboard["reel_mode"] = "animated_illustration"
    return storyboard
def build_viral_title_reel(*, title: str, topic: str, brand: dict) -> dict:
    """Onaylı kısa metin bankasından unvan/emeğe odaklı, özgün Reel üretir.

    Viral içeriklerden yapı alınır; üçüncü taraf sözleri otomatik kopyalanmaz.
    """
    clean_topic = (topic or "").strip().lower()
    if any(word in clean_topic for word in ("sınav", "sgs", "smmm", "ymm", "unvan")):
        hook = "Biz soyadına eklenenlerle değil,"
        payoff = "adının önüne emekle eklenen unvanlarla ilgileniyoruz."
        note = "SMMM • YMM • SGS — Her harfin arkasında emek var."
    else:
        hook = "Herkes sonucu konuşurken,"
        payoff = "biz o sonucun arkasındaki sessiz emeği büyütüyoruz."
        note = "Bugünkü küçük çalışma, yarının unvanına yazılır."
    return {
        "video_type": "reel", "title": title, "format": "9:16", "language": "tr",
        "brand": brand,
        "scenes": [{
            "id": 1, "component": "ViralTitleScene", "duration_seconds": 18,
            "title": hook, "subtitle": payoff, "key_takeaway": note,
            "voice_text": f"{hook} {payoff} {note}",
        }],
    }
