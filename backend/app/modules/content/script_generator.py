from openai import OpenAI
from app.core.config import settings
import json

_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_video_script(topic: str, duration_minutes: int = 5) -> dict:
    prompt = f""""{topic}" konusunda {duration_minutes} dakikalık muhasebe/mevzuat eğitim videosu için Türkçe script yaz.

JSON formatında döndür:
{{
    "title": "SEO uyumlu video başlığı",
    "description": "YouTube açıklaması (500 karakter, hashtag dahil)",
    "tags": ["tag1", "tag2", "tag3"],
    "sections": [
        {{
            "title": "Bölüm başlığı",
            "content": "Seslendirilecek metin, sade ve anlaşılır Türkçe"
        }}
    ]
}}

Kurallar:
- Toplam {duration_minutes * 60} saniye civarı metin (dakikada ~130 kelime)
- Her bölüm max 90 saniye
- Uzman ama sade dil, teknik jargon açıkla
- Türk vergi/muhasebe mevzuatına uygun"""

    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def generate_shorts_script(topic: str) -> dict:
    prompt = f""""{topic}" konusunda 50-60 saniyelik YouTube Shorts / Instagram Reels için Türkçe script yaz.

JSON formatında döndür:
{{
    "title": "Dikkat çekici soru başlığı",
    "hook": "İlk 3 saniyede söylenecek dikkat çekici cümle",
    "content": "Ana içerik (max 80 kelime, akıcı konuşma dili)",
    "cta": "Sona eklenen çağrı (abone ol, yorum yap vb.)",
    "caption": "Instagram/YouTube caption (emoji + hashtag)",
    "tags": ["tag1", "tag2"]
}}"""

    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def generate_post_content(topic: str) -> dict:
    prompt = f""""{topic}" konusunda Instagram eğitici post içeriği yaz.

JSON formatında döndür:
{{
    "title": "Post başlığı",
    "question": "Takipçileri düşündürecek soru",
    "answer_points": ["Madde 1", "Madde 2", "Madde 3", "Madde 4"],
    "caption": "Instagram caption (emoji ve hashtag dahil, max 300 karakter)",
    "image_text": "Görselde yazacak kısa metin (max 15 kelime)"
}}"""

    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
