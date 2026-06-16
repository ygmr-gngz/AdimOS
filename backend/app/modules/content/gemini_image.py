"""
Gemini Flash ile Instagram post için görsel prompt + içerik üretir,
ardından PIL ile profesyonel branded görsel oluşturur.
Gemini API key yoksa doğrudan PIL şablonuna düşer.
"""
import os
import uuid
import json
from app.core.config import settings
from app.modules.content.slide_generator import create_post_image

_OUTPUT_DIR = "/tmp/slides"


def generate_post_image_with_gemini(topic: str) -> tuple[str, str]:
    """
    Returns (image_path, script_text).
    Uses Gemini to generate structured post content, then PIL for the image.
    """
    if not settings.GEMINI_API_KEY:
        return _fallback(topic)

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f""""{topic}" konusunda Instagram eğitici post içeriği oluştur.
Hedef kitle: SGS/SMMM/YMM sınavına hazırlanan adaylar.
Ton: Profesyonel, eğitici, akılda kalıcı.

Sadece JSON döndür, başka hiçbir şey yazma:
{{
    "baslik": "Konuyu özetleyen kısa başlık (max 5 kelime)",
    "maddeler": [
        "Birinci önemli nokta",
        "İkinci önemli nokta",
        "Üçüncü önemli nokta",
        "Dördüncü önemli nokta",
        "Beşinci önemli nokta"
    ],
    "alt_not": "Kısa hatırlatma notu (max 8 kelime)",
    "caption": "Instagram caption (emoji + hashtag, 200 karakter)"
}}"""

        response = model.generate_content(prompt)
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)

        image_path = create_post_image(
            question=data.get("baslik", topic),
            answer_points=data.get("maddeler", []),
            image_text=data.get("alt_not", ""),
        )
        script_text = data.get("baslik", topic) + "\n\n" + "\n".join(
            f"• {m}" for m in data.get("maddeler", [])
        ) + "\n\n" + data.get("caption", "")
        return image_path, script_text

    except Exception:
        return _fallback(topic)


def _fallback(topic: str) -> tuple[str, str]:
    """Gemini yoksa PIL şablonu ile devam et"""
    image_path = create_post_image(
        question=topic,
        answer_points=[
            "Konu hakkında temel bilgi",
            "Dikkat edilmesi gereken noktalar",
            "Sınav için önemli ayrıntılar",
            "Pratik uygulama ipuçları",
            "Adım Müşavir ile öğren",
        ],
        image_text="@adimmusavir",
    )
    script_text = topic
    return image_path, script_text
