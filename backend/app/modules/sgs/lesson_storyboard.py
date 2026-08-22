"""
Konu Anlatımı Storyboard Üretici — LessonVideo pedagojik format.

Hedef: 20-25 dakikalık kapsamlı konu anlatımı videosu.
Sahne tipleri: LessonTitleScene → LessonConceptScene → LessonCardScene → LessonExampleScene → LessonSummaryScene

Çıktı doğrudan Remotion-hazır JSON'dur (id alanı eklenmemiştir).
"""
import json
import logging
import unicodedata
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)
_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Lesson pipeline için geçerli bileşen adları (registry.py ile senkronize)
_VALID_COMPONENTS = frozenset({
    "LessonTitleScene", "LessonConceptScene", "LessonCardScene",
    "LessonExampleScene", "LessonSummaryScene",
    "LessonInfographicScene", "LessonMindMapScene",
})

# Bilinen eşdeğer adlar → kanonik bileşen (registry veya LLM kalıntısı)
_COMPONENT_ALIASES: dict[str, str] = {
    "LessonIntroScene":      "LessonTitleScene",
    "AgendaScene":           "LessonConceptScene",
    "ConceptScene":          "LessonConceptScene",
    "DefinitionCardScene":   "LessonCardScene",
    "AccountCardScene":      "LessonCardScene",
    "JournalEntryScene":     "LessonExampleScene",
    "TableScene":            "LessonCardScene",
    "ComparisonScene":       "LessonCardScene",
    "ExampleScene":          "LessonExampleScene",
    "CommonMistakeScene":    "LessonConceptScene",
    "ExamTipScene":          "LessonConceptScene",
    "MiniRecapScene":        "LessonConceptScene",
    "LessonOutroScene":      "LessonSummaryScene",
    "TAccountScene":         "LessonExampleScene",
    "CalculationStepsScene": "LessonExampleScene",
    "SplitLessonScene":      "LessonConceptScene",
}

# Structured output şeması — component alanını enum ile kısıtla
_COMPONENT_SCHEMA = {
    "name": "lesson_storyboard",
    "schema": {
        "type": "object",
        "properties": {
            "scenes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "component": {
                            "type": "string",
                            "enum": sorted(_VALID_COMPONENTS),
                        }
                    },
                    "required": ["component"],
                    "additionalProperties": True,
                },
            }
        },
        "required": ["scenes"],
    },
    "strict": False,
}

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
    desc_note = f"\nEk bağlam ve üretim düzeltmesi: {description}" if description else ""
    min_scene_count = 8 if target_minutes <= 12 else 10
    ideal_scene_count = "10-14" if target_minutes <= 12 else "12-18"
    min_voice_seconds = round(float(target_minutes) * 60 * 0.80)

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
   - duration_seconds: 0  (TTS sonrası hesaplanır — bu alanı 0 bırak)

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
   - duration_seconds: 0  (TTS sonrası hesaplanır — bu alanı 0 bırak)

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
   - duration_seconds: 0  (TTS sonrası hesaplanır — bu alanı 0 bırak)

5. LessonSummaryScene (1 adet — en sonda):
   - title: "{{topic}} — Özet"
   - bullet_points: 4-6 kritik madde, max 80 karakter/madde
   - key_point: En önemli tek kuralı vurgula (max 100 karakter)
   - voice_text: Konuyu özetle, sınav odaklı kritik noktaları vurgula,
     kapanış yapabilirsin (100-140 kelime)
   - duration_seconds: 0  (TTS sonrası hesaplanır — bu alanı 0 bırak)

6. LessonInfographicScene (1-2 adet — kavramları görsel olarak karşılaştır):
   - infographic_title: ana başlık
   - infographic_subtitle: 1-2 cümlelik bağlam
   - cards: 3-4 kavram; her kartta title, category, content ve rule zorunlu
   - key_point: sağ/alt vurgu kutusundaki sınav sonucu
   - voice_text: kavramları sırayla karşılaştır (120-180 kelime)
   - duration_seconds: 0
   - Kullanım: hukuk sistemleri, hesap türleri, yöntem karşılaştırmaları.

7. LessonMindMapScene (1 adet — konu ağacını göster):
   - title: haritanın başlığı
   - infographic_title: merkez düğüm
   - definition: kısa giriş
   - bullet_points: 4-6 dal; her dal tek, somut kavram cümlesi
   - voice_text: dallar arasındaki ilişkiyi açıkla (100-150 kelime)
   - duration_seconds: 0
   - Kullanım: alt konu haritası ve dersin genel sistemi. Serbest görsel/prompt üretme.

════════ SAHNE SAYISI VE EKRAN KULLANIMI KILAVUZU ════════
{target_minutes} dakika için ZORUNLU sahne dizisi ({min_scene_count}-18 sahne):
- 1 LessonTitleScene (~25s)
- 4-6 LessonConceptScene (her biri ~90-120s — kavram başına ayrı sahne, alt konuları böl)
- 2-3 LessonCardScene (her biri ~75s — tablo/liste içerikleri için)
- 1-2 LessonInfographicScene (kavram karşılaştırması)
- 1 LessonMindMapScene (konu haritası)
- 4-6 LessonExampleScene (her biri ~110-140s — her örnek için ayrı sahne)
- 1 LessonSummaryScene (~60s)

EKRAN KULLANIMI KURALLARI (%75-85 hedef):
- bullet_points: 4-5 madde (3 madde ekranı boş bırakır — yetersiz)
- cards: 4-5 kart (3 kart yetersiz doluluk)
- journal_rows: en az 3 kayıt satırı içeren örnekler tercih et
- definition alanı: 2 cümle — ekranın üst bölümünü doldurmak için yeterince uzun olmalı
- LessonConceptScene bullet_points: maksimum 5 madde, her madde ≥8 kelime
- LessonCardScene cards: her kart için content VE rule alanı doldurulmalı

MİNİMUM KURAL — KELİMESİ KELİMESİNE UYULACAK:
- Toplam sahne sayısı: EN AZ {min_scene_count}, ideal {ideal_scene_count}
- Toplam voice_text için tahmini seslendirme süresi: EN AZ {min_voice_seconds} saniye
- Her kavram için ayrı LessonConceptScene — tek sahnede tıkıştırma
- Her örnek için ayrı LessonExampleScene — tek sahnede tıkıştırma
- Alt konuları böl: "Hesap işleyişi" ve "Örnek kayıtlar" iki ayrı sahne olsun
- voice_text'ler uzun ve detaylı olsun:
    başlık: 100-130 kelime
    kavram: 200-270 kelime
    kart: 160-220 kelime
    örnek: 220-300 kelime
    özet: 130-170 kelime

Hedef süreyle çelişen sabit 18 dakika alt sınırı kullanma. Ek bağlamda süre
düzeltmesi varsa voice_text uzunluklarını o geri bildirime göre değiştir.

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
      "duration_seconds": 0
    }},
    {{
      "component": "LessonCardScene",
      "infographic_title": "...",
      "infographic_subtitle": "...",
      "cards": [
        {{"icon": "📈", "title": "...", "category": "BORÇ", "content": "...", "rule": "..."}}
      ],
      "voice_text": "...",
      "duration_seconds": 0
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
      "duration_seconds": 0
    }},
    {{
      "component": "LessonInfographicScene",
      "infographic_title": "Ticaret Hukukuna İlişkin Temel Sistemler",
      "infographic_subtitle": "Sistemler kapsam ölçütüne göre ayrılır.",
      "cards": [
        {{"title": "Subjektif Sistem", "category": "TACİR ODAKLI", "content": "Tacir sıfatını esas alır.", "rule": "Odak: kişi"}},
        {{"title": "Objektif Sistem", "category": "İŞLEM ODAKLI", "content": "Ticari işlemi esas alır.", "rule": "Odak: eylem"}},
        {{"title": "Modern Sistem", "category": "İŞLETME ODAKLI", "content": "Ticari işletmeyi esas alır.", "rule": "6102 sayılı TTK"}}
      ],
      "key_point": "Türkiye modern sistemi benimser.",
      "voice_text": "...",
      "duration_seconds": 0
    }},
    {{
      "component": "LessonMindMapScene",
      "title": "Konu Haritası",
      "infographic_title": "Ticaret Hukukuna İlişkin Sistemler",
      "definition": "Dört temel yaklaşım bulunur.",
      "bullet_points": ["Subjektif sistem: taciri esas alır", "Objektif sistem: ticari işlemi esas alır", "Karma sistem: tacir ve işlemi birlikte esas alır", "Modern sistem: ticari işletmeyi esas alır"],
      "voice_text": "...",
      "duration_seconds": 0
    }},
    {{
      "component": "LessonSummaryScene",
      "title": "{topic} — Özet",
      "bullet_points": ["...", "..."],
      "key_point": "...",
      "voice_text": "...",
      "duration_seconds": 0
    }}
  ]
}}

Sadece JSON döndür. Başka hiçbir metin yok."""

    def _nfc(obj):
        if isinstance(obj, str):
            return unicodedata.normalize("NFC", obj)
        if isinstance(obj, list):
            return [_nfc(v) for v in obj]
        if isinstance(obj, dict):
            return {k: _nfc(v) for k, v in obj.items()}
        return obj

    def _apply_aliases(scenes: list) -> list:
        for s in scenes:
            comp = s.get("component", "")
            if comp in _COMPONENT_ALIASES:
                s["component"] = _COMPONENT_ALIASES[comp]
        return scenes

    def _unknown_components(scenes: list) -> list[str]:
        return sorted({s.get("component", "") for s in scenes if s.get("component") not in _VALID_COMPONENTS})

    logger.info(f"[lesson-storyboard] '{topic}' konu anlatımı üretiliyor, hedef={target_minutes}dk, ders={subject}")
    try:
        raw_resp = _client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_schema", "json_schema": _COMPONENT_SCHEMA},
            temperature=0.40,
            max_tokens=14000,
        )
        raw_content = raw_resp.choices[0].message.content
        result = json.loads(raw_content)
        scenes = [_nfc(s) for s in result.get("scenes", [])]
        result["scenes"] = scenes

        _apply_aliases(scenes)
        unknown = _unknown_components(scenes)

        if unknown:
            logger.warning(
                f"[lesson-storyboard] geçersiz bileşen(ler): {unknown} — şema hatası geri besleniyor"
            )
            retry_msg = (
                f"Hata: Geçersiz bileşen adı kullanıldı: {unknown}. "
                f"Yalnızca şu adlar geçerlidir: {sorted(_VALID_COMPONENTS)}. "
                "Storyboard'u aynı içerikle ancak yalnızca bu geçerli bileşen adlarını kullanarak yeniden üret."
            )
            raw_resp2 = _client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": raw_content},
                    {"role": "user", "content": retry_msg},
                ],
                response_format={"type": "json_schema", "json_schema": _COMPONENT_SCHEMA},
                temperature=0.40,
                max_tokens=14000,
            )
            result = json.loads(raw_resp2.choices[0].message.content)
            scenes = [_nfc(s) for s in result.get("scenes", [])]
            result["scenes"] = scenes

            _apply_aliases(scenes)
            still_unknown = _unknown_components(scenes)
            if still_unknown:
                from app.errors.registry import PipelineErrorException
                raise PipelineErrorException(
                    "invalid_scene_for_content_type",
                    admin_detail={
                        "invalid_scenes": still_unknown,
                        "content_type": "konu_anlatimi",
                        "attempts": 2,
                    },
                    stage="routing",
                )

        component_counts: dict[str, int] = {}
        for s in scenes:
            c = s.get("component", "unknown")
            component_counts[c] = component_counts.get(c, 0) + 1
        logger.info(f"[lesson-storyboard] tamamlandı: {len(scenes)} sahne — {component_counts}")
        return result
    except Exception as e:
        from app.errors.registry import PipelineErrorException
        if isinstance(e, PipelineErrorException):
            raise
        err_str = str(e)
        logger.error(f"[lesson-storyboard] hata: {e}", exc_info=True)
        if "429" in err_str or "quota" in err_str.lower() or "insufficient_quota" in err_str:
            raise RuntimeError(
                "OpenAI API kredisi tükendi (429 insufficient_quota). "
                "platform.openai.com/account/billing adresinden kredi ekleyin."
            ) from e
        raise RuntimeError(f"Konu anlatımı storyboard üretimi başarısız: {e}") from e
