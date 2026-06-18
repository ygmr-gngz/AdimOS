"""İçerik düzenleme — doğal dil ile yeniden üretim planı oluştur."""
import json
import logging
from openai import OpenAI
from app.core.config import settings

_client = OpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger(__name__)

_SYSTEM = """Sen bir video içerik editörüsün.
Kullanıcının düzenleme isteğini analiz et ve yeniden üretim için JSON plan döndür.

Format (sadece JSON):
{
  "enhanced_topic": "Orijinal konu + edit talimatını birleştirmiş geliştirilmiş konu",
  "changes_summary": ["Değişiklik 1", "Değişiklik 2"],
  "explanation": "Kısa özet (1 cümle)"
}

Kurallar:
- enhanced_topic doğrudan yeniden üretimde kullanılacak — çok spesifik ve kapsamlı olsun
- Türkçe yaz
- JSON dışında hiçbir şey yazma"""


def build_edit_plan(content: dict, user_message: str) -> dict:
    title = content.get("title") or content.get("topic", "")
    script = (content.get("script") or "")[:600]
    content_type = content.get("type", "video")

    prompt = f"""Orijinal başlık: {title}
Tür: {content_type}
Mevcut script (kısaltılmış): {script or '(yok)'}

Kullanıcı isteği: {user_message}

Bu isteği uygulayarak geliştirilmiş içerik planı oluştur."""

    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=400,
            temperature=0.3,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        logger.error(f"[editor] build_edit_plan hatası: {e}")
        return {
            "enhanced_topic": f"{title}. Düzenleme notu: {user_message}",
            "changes_summary": [user_message],
            "explanation": "Düzenleme planı oluşturulamadı, not eklenerek devam edildi.",
        }
