"""
EducationalReel120 Storyboard Üretici — GPT-4o ile ~120 saniyelik SGS eğitim Reels.

Spec Section 9 akışı:
  0-5s    hook    — güçlü kanca, sürpriz istatistik
  5-20s   context — konunun önemi, sınav bağlantısı
  20-45s  content — 1. bilgi / çözüm adımı (bullet_points)
  45-70s  content — 2. bilgi / örnek / detay
  70-95s  mistake — sık yapılan hata (common_mistake)
  95-110s tip     — sınav ipucu (exam_tip)
  110-120s outro  — özet + CTA + kanal yönlendirmesi

Her sahne EducationalReelScene component'ine yüklenecek.
İçerik serisi (content_series) başlık şablonunu belirler.
"""
import json
import logging
import unicodedata
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)
_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# İçerik serisi başlık şablonları (Section 11)
SERIES_TITLE_TEMPLATES: dict[str, str] = {
    "cikmis_soru":      "{topic} — Çıkmış Soru Çözümü",
    "iki_dakikada_sgs": "2 Dakikada SGS: {topic}",
    "sik_hata":         "SGS'de {topic} Hakkında Sık Yapılan Hatalar",
    "bir_soruda_ogren": "Bir Soruda Öğren: {topic}",
    "konu_anlatimi":    "{topic} Konu Anlatımı — SGS",
    "motivasyon":       "{topic} | Adım Müşavir Motivasyon",
}

_SYSTEM = """Sen Türkiye'nin en iyi SGS (Özel Güvenlik) ve SMMM sınav koçusun.
2 dakikalık Instagram Reels eğitim videoları üretiyorsun.
Her video 7 sahneden oluşur, akıcı Türkçe anlatım yapar, sınavda çıkan bilgilere odaklanır.

KURALLAR:
- Tüm çıktılar Türkçe.
- Sadece geçerli JSON döndür.
- Her sahne için voice_text 30-80 kelime arasında olmalı (sahneye göre değişir).
- hook sahnesinde hook_text kısa ve çarpıcı olsun (maksimum 10 kelime, 2 satır).
- highlight_stat rakam veya yüzde içermeli (örn: "%73", "5 yıl", "3 gün").
- bullet_points maksimum 4 madde, her madde 8-12 kelime.
- common_mistake ve exam_tip 1-2 cümle.
- cta_text kanal adına yönlendirme içermeli: "@adimmusavir".
- Yasaklı ifadeler: "Teşekkür ederim", "Hoşçakalın", "İzlediğiniz için".
"""

_SCENE_SCHEMA = """
Storyboard JSON formatı — tam olarak 7 sahne döndür:

{
  "scenes": [
    {
      "id": 1,
      "component": "EducationalReelScene",
      "segment_type": "hook",
      "duration_seconds": 5,
      "hook_text": "Kısa çarpıcı kanca (2 satır, maks 10 kelime)",
      "highlight_stat": "Dikkat çeken rakam/yüzde",
      "voice_text": "30-50 kelime — sürükleyici giriş, sürpriz bir bilgi ver"
    },
    {
      "id": 2,
      "component": "EducationalReelScene",
      "segment_type": "context",
      "duration_seconds": 15,
      "title": "Neden bilmen gerekiyor?",
      "bullet_points": ["Madde 1", "Madde 2", "Madde 3"],
      "voice_text": "50-70 kelime — konunun sınavdaki önemini anlat"
    },
    {
      "id": 3,
      "component": "EducationalReelScene",
      "segment_type": "content",
      "duration_seconds": 25,
      "title": "Ana Kural / Birinci Bilgi",
      "bullet_points": ["Madde 1", "Madde 2", "Madde 3", "Madde 4"],
      "voice_text": "70-80 kelime — detaylı anlatım, örneklerle pekiştir"
    },
    {
      "id": 4,
      "component": "EducationalReelScene",
      "segment_type": "content",
      "duration_seconds": 25,
      "title": "İkinci Bilgi / Örnek",
      "bullet_points": ["Madde 1", "Madde 2", "Madde 3"],
      "voice_text": "70-80 kelime — ikinci detay veya somut örnek"
    },
    {
      "id": 5,
      "component": "EducationalReelScene",
      "segment_type": "mistake",
      "duration_seconds": 25,
      "title": "Dikkat!",
      "common_mistake": "Sık yapılan hatanın 1-2 cümlelik açıklaması",
      "voice_text": "60-70 kelime — hatayı açıkla, neden yanlış olduğunu göster"
    },
    {
      "id": 6,
      "component": "EducationalReelScene",
      "segment_type": "tip",
      "duration_seconds": 15,
      "title": "Sınav İpucu",
      "exam_tip": "Sınava özel pratik ipucu — 1-2 cümle",
      "voice_text": "40-60 kelime — sınavda nasıl ayırt edeceğini anlat"
    },
    {
      "id": 7,
      "component": "EducationalReelScene",
      "segment_type": "outro",
      "duration_seconds": 10,
      "title": "Özet",
      "bullet_points": ["Özet madde 1", "Özet madde 2", "Özet madde 3"],
      "cta_text": "Daha fazla SGS sorusu için @adimmusavir'i takip et!",
      "voice_text": "30-50 kelime — özet + @adimmusavir'e yönlendirme"
    }
  ]
}
"""


def _apply_series_title(title: str, topic: str, content_series: str | None) -> str:
    """İçerik serisine göre video başlığını şablondan üretir."""
    if not content_series or content_series not in SERIES_TITLE_TEMPLATES:
        return title
    template = SERIES_TITLE_TEMPLATES[content_series]
    return template.format(topic=topic or title)


def generate_educational_reel_storyboard(
    title: str,
    topic: str,
    subject: str,
    content_series: str | None = None,
    description: str = "",
    brand: dict | None = None,
) -> dict:
    """
    EducationalReel120 composition için 7 sahnelik storyboard üretir.
    Döner: tam storyboard dict (video_type, scenes, brand vb.)
    """
    from app.modules.content.pronunciation_dict import latex_to_spoken_turkish

    series_label = ""
    if content_series and content_series in SERIES_TITLE_TEMPLATES:
        series_label = f"İçerik serisi: {SERIES_TITLE_TEMPLATES[content_series].replace('{topic}', topic)}\n"

    desc_note = f"Ek bağlam / yönetmen notu: {description}\n" if description else ""

    prompt = f"""Aşağıdaki SGS konusu için 7 sahnelik EducationalReel120 storyboard üret.

Konu: {topic}
Ders / Alan: {subject}
Video başlığı: {title}
{series_label}{desc_note}
Toplam hedef süre: ~120 saniye (5+15+25+25+25+15+10 = 120).

{_SCENE_SCHEMA}

ÖNEMLİ: Tam olarak 7 sahne üret. Her sahnede voice_text zorunlu. Sadece JSON döndür.
"""

    try:
        raw = _client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            temperature=0.45,
            max_tokens=4000,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user",   "content": prompt},
            ],
        )
        data = json.loads(raw.choices[0].message.content)
        scenes = data.get("scenes", [])
    except Exception as exc:
        logger.error(f"[reel_storyboard] GPT hatası: {exc}")
        raise RuntimeError(f"EducationalReel storyboard üretilemedi: {exc}") from exc

    # Unicode NFC normalleştirme
    def _norm(obj):
        if isinstance(obj, str):
            return unicodedata.normalize("NFC", obj)
        if isinstance(obj, list):
            return [_norm(i) for i in obj]
        if isinstance(obj, dict):
            return {k: _norm(v) for k, v in obj.items()}
        return obj
    scenes = _norm(scenes)

    # id'leri sırayla ata, component'i zorla
    for i, s in enumerate(scenes, 1):
        s["id"]        = i
        s["component"] = "EducationalReelScene"
        if not s.get("segment_type"):
            default_types = ["hook", "context", "content", "content", "mistake", "tip", "outro"]
            s["segment_type"] = default_types[i - 1] if i <= len(default_types) else "content"
        # voice_text eksikse basit fallback
        if not (s.get("voice_text") or "").strip():
            s["voice_text"] = s.get("hook_text") or s.get("title") or topic

    if len(scenes) < 5:
        logger.warning(f"[reel_storyboard] Yetersiz sahne üretildi: {len(scenes)}/7")

    final_title = _apply_series_title(title, topic, content_series)

    default_brand = {
        "primary_color": "#0B2A4A", "secondary_color": "#C9A96E",
        "background_color": "#FAF7F0", "font_heading": "Playfair Display",
        "font_body": "Lato", "handle": "@adimmusavir",
    }
    if brand:
        default_brand.update(brand)

    return {
        "video_type":    "reel",
        "title":         final_title,
        "lesson_name":   subject,
        "topic":         topic,
        "format":        "9:16",
        "language":      "tr",
        "brand":         default_brand,
        "content_series": content_series,
        "scenes":        scenes,
    }
