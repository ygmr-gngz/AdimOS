"""SGS motivasyon içeriği storyboard üreticisi (GPT-4o-mini)."""
import json
import logging
import openai

logger = logging.getLogger(__name__)

_PLATFORM_STYLE = {
    "reels":    "Dikey video (9:16). Hızlı geçişler. Büyük, çarpıcı metin. Duygusal müzik ritmine uygun.",
    "shorts":   "YouTube Shorts (9:16). Enerjik tempo. Her cümle yeni bilgi. Kısa ve etkili.",
    "carousel": "Instagram Carousel (1:1). Her slide tek mesaj. 5-7 slide. Son slide CTA.",
    "post":     "Tek kare Instagram postu (1:1). Etkileyici başlık, açıklayıcı subtitle, CTA.",
}

_SYSTEM_PROMPT = """Sen SGS (Sermaye Piyasası Lisanslama Sınavları) öğrenci koçusun.
Adım Müşavirlik adına Türkçe motivasyon içeriği üretiyorsun.
Her zaman sıcak, samimi ve gerçekçi bir dil kullanıyorsun.
Öğrencinin zor sürecini gerçekten anlıyor gibi konuşuyorsun, yüzeysel tebrik cümlelerinden kaçınıyorsun.
Cümleler kısa, güçlü ve akılda kalıcı olacak."""

_USER_TEMPLATE = """Konu: {topic}
Platform: {platform} — {platform_style}
Ton: {tone}

5 adımlı motivasyon storyboard üret:
1. hook — Duygusal açılış, öğrencinin dikkatini çekecek
2. problem — Öğrencinin yaşadığı zorluğu anlayışla anlat
3. message — Kısa, güçlü motivasyon mesajı (1-2 cümle)
4. tip — Somut ve uygulanabilir öneri (örn: "Her gün 10 soru çöz, yavaş ama bırakma")
5. cta — Harekete geçirici kapanış

JSON formatı:
{{
  "title": "İçerik başlığı (max 60 karakter)",
  "description": "Açıklama (max 120 karakter)",
  "hashtags": ["#sgs", "#motivasyon", "#smmm"],
  "scenes": [
    {{
      "type": "hook",
      "title": "Ekran başlığı (max 40 karakter)",
      "narration": "Seslendirilecek Türkçe metin (2-3 cümle, toplam max 200 karakter)",
      "display_lines": ["Ekranda gösterilecek satır 1", "satır 2", "satır 3"]
    }}
  ]
}}

Tüm metinler Türkçe. display_lines max 5 satır, her satır max 50 karakter."""


def generate_motivation_storyboard(
    topic: str,
    platform: str = "reels",
    tone: str = "sıcak ve samimi",
) -> dict:
    platform_style = _PLATFORM_STYLE.get(platform, _PLATFORM_STYLE["reels"])

    client = openai.OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _USER_TEMPLATE.format(
                topic=topic,
                platform=platform,
                platform_style=platform_style,
                tone=tone,
            )},
        ],
        response_format={"type": "json_object"},
        max_tokens=1800,
        temperature=0.88,
    )

    raw = resp.choices[0].message.content or "{}"
    result = json.loads(raw)
    logger.info(f"[motivation] storyboard üretildi: {result.get('title')} | {len(result.get('scenes', []))} sahne")
    return result
