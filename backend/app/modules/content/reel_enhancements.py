"""Reels/Shorts için konuya özel animasyonlu illüstrasyon ve tek-soru akışları."""
from __future__ import annotations

import base64
import io
import logging
import hashlib
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
            "hook_text": "Ali bu kaydı doğru yapabilecek mi?", "highlight_stat": "1 SORU",
            "voice_text": f"Ali'nin günlük işinden yola çıkıp {topic} konusunu tek soruda netleştirelim.",
        },
        {
            "id": 2, "component": "DrawnQuestionExplainerScene", "segment_type": "question", "visual_source": "code_drawn",
            "title": "Ali'nin Yolculuğu", "story_character": "Ali", "question_text": question_text, "options": options,
            "correct_label": correct,
            "explanation": explanation, "memory_hook": memory_hook,
            "clue_text": "Sorudaki işlemin niteliğine ve hesabın çalışma yönüne odaklan.",
            "voice_text": f"{question_text} Beş şıktan birini seç. Doğru cevap {correct} şıkkı. {explanation} Akılda tut: {memory_hook}.",
        },
        {
            "id": 3, "component": "ReelCtaScene", "segment_type": "outro", "visual_source": "text_only",
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


_VIDEO_VISUAL_ROLES = (
    ("establishing_context", "wide contextual overview", "domain-specific environment"),
    ("person_action", "subject actively performing the scene action", "working environment"),
    ("process_detail", "close detail of the mechanism or process", "process area"),
    ("data_object", "important object, diagram or measurable detail", "clean neutral context"),
    ("result_environment", "visible outcome and its real-world context", "result environment"),
)


def _scene_visual_intent(topic: str, scene: dict[str, Any], order: int) -> dict[str, Any]:
    purpose, action, environment = _VIDEO_VISUAL_ROLES[(order - 1) % len(_VIDEO_VISUAL_ROLES)]
    focus = str(
        scene.get("title") or scene.get("exam_tip") or scene.get("common_mistake")
        or scene.get("voice_text") or topic
    ).strip()[:180]
    return {
        "scene_id": str(scene.get("id") or order),
        "scene_purpose": purpose,
        "semantic_focus": focus,
        "subject": topic,
        "action": action,
        "environment": environment,
        "visual_type": "hand_drawn_educational_illustration",
        "search_query": f"{topic} {focus} {action} {environment}"[:360],
        "avoid": [],
    }


def _illustration_prompt(
    topic: str, scene: dict[str, Any], intent: dict[str, Any] | None = None,
) -> str:
    facts = "\n".join(str(x) for x in (scene.get("bullet_points") or []))
    intent = intent or _scene_visual_intent(topic, scene, 1)
    return f"""Create one premium vertical educational illustration for a Turkish educational Reel.
SUBJECT: {topic}
SCENE TITLE: {scene.get('title') or scene.get('hook_text') or topic}
FACTS TO VISUALIZE: {facts or scene.get('voice_text', '')[:500]}
SCENE PURPOSE: {intent['scene_purpose']}
SEMANTIC FOCUS: {intent['semantic_focus']}
PRIMARY SUBJECT: {intent['subject']}
ACTION: {intent['action']}
ENVIRONMENT: {intent['environment']}
VISUAL QUERY: {intent['search_query']}
AVOID PREVIOUS SCENE CONCEPTS: {', '.join(intent.get('avoid') or []) or 'none'}

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
    used_concepts: list[str] = []
    for order, scene in enumerate(candidates, 1):
        intent = _scene_visual_intent(topic, scene, order)
        intent["avoid"] = used_concepts[-3:]
        response = image_client.images.generate(
            model=PROD_MODEL, prompt=_illustration_prompt(topic, scene, intent), n=1,
            size="1024x1536", quality=PROD_QUALITY, output_format="png",
        )
        png = _to_reel_portrait(base64.b64decode(response.data[0].b64_json))
        path = f"reel-illustrations/{job_id}/{order:02d}-{uuid.uuid4().hex[:8]}.png"
        url = upload_bytes(png, IMAGE_BUCKET, path, "image/png")
        scene["original_component"] = scene.get("component")
        scene["component"] = "AnimatedIllustrationScene"
        scene["visual_source"] = "photo"
        scene["illustration_url"] = url
        presets = ("draw_reveal", "parallax_parts", "focus_pulse")
        scene["animation_preset"] = presets[(order - 1) % len(presets)]
        takeaway = (
            scene.get("exam_tip") or scene.get("common_mistake")
            or (scene.get("bullet_points") or [scene.get("title") or topic])[0]
        )
        scene["key_takeaway"] = str(takeaway).strip()[:120]
        scene["save_label"] = "HIZLI BİLGİ • KAYDET"
        scene["visual_intent"] = intent
        used_concepts.append(f"{intent['scene_purpose']}: {intent['semantic_focus']}")
        logger.info(
            "[reel-illustration] job=%s scene=%s preset=%s intent_hash=%s query_hash=%s",
            job_id[:8], scene.get("id"), scene["animation_preset"],
            hashlib.sha256(intent["semantic_focus"].encode("utf-8")).hexdigest()[:10],
            hashlib.sha256(intent["search_query"].encode("utf-8")).hexdigest()[:10],
        )
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
