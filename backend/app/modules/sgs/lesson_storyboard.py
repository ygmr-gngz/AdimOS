"""
Konu Anlatımı Storyboard Üretici — LessonVideo pedagojik format.

Hedef: 20-25 dakikalık kapsamlı konu anlatımı videosu.
Sahne tipleri: LessonTitleScene → LessonConceptScene → LessonCardScene → LessonExampleScene → LessonSummaryScene

Çıktı doğrudan Remotion-hazır JSON'dur (id alanı eklenmemiştir).
"""
import json
import logging
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)
_client = OpenAI(api_key=settings.OPENAI_API_KEY)

_SYSTEM = """Sen Türkiye'nin en deneyimli SMMM/SGS muhasebe eğitmenlerinden birisin.
20 yıldır bu sınavı hazırlıyorsun. Konu anlatımın: akıcı, kapsamlı, sınav odaklı.
Her konuyu somut örneklerle, yevmiye kayıtlarıyla ve sınav ipuçlarıyla anlatırsın.

YASAKLI İFADELER (yalnızca son LessonSummaryScene'de kullanılabilir, diğer sahnelerde kesinlikle geçemez):
- "Teşekkür ederim", "teşekkür ederiz", "teşekkürler"
- "Bir sonraki videoda görüşmek üzere"
- "Hoşçakalın", "İyi çalışmalar"
- "Bu videoyu izlediğiniz için"
- "Konuyu burada kapatalım" (konu bitmeden)

Tüm çıktılar Türkçe. Sadece geçerli JSON döndür."""


def generate_lesson_storyboard(
    title: str,
    topic: str,
    subject: str,
    target_minutes: int = 20,
    description: str = "",
) -> dict:
    """
    LessonVideo composition için kapsamlı konu anlatımı storyboard üretir.
    Remotion-hazır JSON döner (id alanı eklenmemiştir).

    Returns: {"scenes": [...]}
    """
    desc_note = f"\nEk bağlam: {description}" if description else ""

    prompt = f""""{topic}" konusu için {target_minutes} dakikalık kapsamlı konu anlatımı videosu storyboard üret.

VİDEO BİLGİSİ:
- Başlık: {title}
- Konu: {topic}
- Ders: {subject}
- Hedef Süre: {target_minutes} dakika
- Format: 16:9{desc_note}

════════ SAHNE TİPLERİ VE KURALLARI ════════

1. LessonTitleScene (1 adet — en başta):
   - icon: emoji (konuyla alakalı: 💰📊📋🏦📈 gibi)
   - title: Konu başlığı (max 50 karakter)
   - subtitle: Ders adı büyük harf (max 30 karakter)
   - key_point: Konunun en kritik tek cümlesi (max 80 karakter)
   - voice_text: Giriş anlatımı — konuyu tanıt, sınavdaki önemini vurgula (80-120 kelime)
   - duration_seconds: 25

2. LessonConceptScene (2-4 adet — temel kavramlar):
   - icon: emoji
   - title: Alt konu başlığı (max 50 karakter)
   - definition: Konunun tanımı veya temel açıklaması (1-2 cümle, max 180 karakter)
   - bullet_points: 3-5 madde, her biri max 70 karakter
   - voice_text: Kavramı detaylıca anlat, örneklerle pekiştir, sınav bağlantısı kur
     (150-220 kelime — uzun ve öğretici olsun)
   - duration_seconds: 90

3. LessonCardScene (1-2 adet — görsel referans kartları):
   - infographic_title: Kart grubunun başlığı (max 50 karakter)
   - infographic_subtitle: Alt başlık (max 40 karakter)
   - cards: 3-5 kart, her biri:
     - icon: emoji
     - title: Kart başlığı (max 30 karakter)
     - category: Kategori rozeti (max 15 karakter, büyük harf: AKTİF/PASİF/BORÇ/ALACAK vb.)
     - content: Ana açıklama (max 80 karakter)
     - rule: Kural/sonuç (max 60 karakter)
   - voice_text: Kartları sırayla açıkla, aralarındaki farkı vurgula (120-180 kelime)
   - duration_seconds: 75

4. LessonExampleScene (2-3 adet — çözümlü örnekler):
   - title: Örnek başlığı (max 50 karakter)
   - question_text: Muhasebe sorusu veya durum açıklaması (max 200 karakter)
   - journal_rows: Yevmiye kaydı satırları (her biri):
     - code: Hesap kodu (ör: "100")
     - name: Hesap adı (ör: "Kasa" veya "    Yurt İçi Satışlar" — alacak satırları 4 boşluk girintili)
     - debit: Borç tutarı (sayı, varsa)
     - credit: Alacak tutarı (sayı, varsa)
     - indent: true (alacak satırları için)
   - explanation: Kaydın açıklaması — neden bu hesaplar (max 200 karakter)
   - voice_text: Örneği adım adım anlat, her kaydın neden yapıldığını açıkla,
     sınava özel uyarılar ekle (180-250 kelime — en detaylı anlatım burada olsun)
   - duration_seconds: 110

5. LessonSummaryScene (1 adet — en sonda):
   - title: "{{topic}} — Özet"
   - bullet_points: 4-6 kritik madde, max 80 karakter/madde
   - key_point: En önemli tek kuralı vurgula (max 100 karakter)
   - voice_text: Konuyu özetle, sınav odaklı kritik noktaları vurgula,
     kapanış yapabilirsin (100-140 kelime)
   - duration_seconds: 60

════════ SAHNE SAYISI KILAVUZU ════════
{target_minutes} dakika için önerilen sahne dizisi:
- 1 LessonTitleScene (~25s)
- 3 LessonConceptScene (~270s = 4.5dk)
- 1 LessonCardScene (~75s = 1.25dk)
- 2-3 LessonExampleScene (~220-330s = 3.5-5.5dk)
- 1 LessonSummaryScene (~60s)
Toplam içerik: ~650-760s ≈ 11-12dk minimum (TTS ile gerçek süre daha uzun olacak)
Hedef {target_minutes}dk için her scene'in voice_text'ini DOLU ve DETAYLI yaz.

════════ JSON FORMAT ════════
{{
  "scenes": [
    {{
      "component": "LessonTitleScene",
      "icon": "💰",
      "title": "...",
      "subtitle": "MUHASEBE",
      "key_point": "...",
      "voice_text": "...",
      "duration_seconds": 25
    }},
    {{
      "component": "LessonConceptScene",
      "icon": "📌",
      "title": "...",
      "definition": "...",
      "bullet_points": ["...", "...", "..."],
      "voice_text": "...",
      "duration_seconds": 90
    }},
    {{
      "component": "LessonCardScene",
      "infographic_title": "...",
      "infographic_subtitle": "...",
      "cards": [
        {{"icon": "📈", "title": "...", "category": "BORÇ", "content": "...", "rule": "..."}}
      ],
      "voice_text": "...",
      "duration_seconds": 75
    }},
    {{
      "component": "LessonExampleScene",
      "title": "Örnek: ...",
      "question_text": "...",
      "journal_rows": [
        {{"code": "100", "name": "Kasa", "debit": 15000}},
        {{"code": "600", "name": "    Yurt İçi Satışlar", "credit": 15000, "indent": true}}
      ],
      "explanation": "...",
      "voice_text": "...",
      "duration_seconds": 110
    }},
    {{
      "component": "LessonSummaryScene",
      "title": "{topic} — Özet",
      "bullet_points": ["...", "..."],
      "key_point": "...",
      "voice_text": "...",
      "duration_seconds": 60
    }}
  ]
}}

Sadece JSON döndür. Başka hiçbir metin yok."""

    logger.info(f"[lesson-storyboard] '{topic}' konu anlatımı üretiliyor, hedef={target_minutes}dk, ders={subject}")
    try:
        r = _client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.40,
            max_tokens=14000,
        )
        result = json.loads(r.choices[0].message.content)
        scenes = result.get("scenes", [])
        component_counts = {}
        for s in scenes:
            c = s.get("component", "unknown")
            component_counts[c] = component_counts.get(c, 0) + 1
        logger.info(f"[lesson-storyboard] tamamlandı: {len(scenes)} sahne — {component_counts}")
        return result
    except Exception as e:
        err_str = str(e)
        logger.error(f"[lesson-storyboard] hata: {e}", exc_info=True)
        if "429" in err_str or "quota" in err_str.lower() or "insufficient_quota" in err_str:
            raise RuntimeError(
                "OpenAI API kredisi tükendi (429 insufficient_quota). "
                "platform.openai.com/account/billing adresinden kredi ekleyin."
            ) from e
        raise RuntimeError(f"Konu anlatımı storyboard üretimi başarısız: {e}") from e
