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
from app.core.content_constants import TR_SPS, CHARS_PER_SYLLABLE

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

# TR_SPS (hece/saniye) ve CHARS_PER_SYLLABLE (karakter/hece) artık
# shared/content-types.json'dan geliyor (app.core.content_constants) — tek
# kaynak, backend/app/api/routes/video.py ile paylaşılır.
# OpenAI structured outputs strict:true bile string maxLength'i zorlamıyor
# (doğrulandı, bkz. OpenAI docs: "pattern, minLength, format ... not enforced
# by the model in strict mode"), o yüzden şema yerine üretim sonrası
# deterministik kontrol + 1 yeniden deneme kullanılıyor (bkz.
# generate_educational_reel_storyboard).

_SYSTEM = """Sen Türkiye'nin en iyi SGS (Özel Güvenlik) ve SMMM sınav koçusun.
2 dakikalık Instagram Reels eğitim videoları üretiyorsun.
Her video 7 sahneden oluşur, akıcı Türkçe anlatım yapar, sınavda çıkan bilgilere odaklanır.

KURALLAR:
- Tüm çıktılar Türkçe.
- Sadece geçerli JSON döndür.
- voice_text uzunluğu kullanıcı promptundaki HECE BÜTÇESİ ve KARAKTER SINIRI
  talimatına göre belirlenir — bu talimatlardaki SAYI her zaman bağlayıcıdır.
  Aşağıdaki örnek JSON'daki voice_text metinleri hem alan yapısını hem de
  YAKLAŞIK hedef uzunluğu gösterir; onlardan çok daha kısa yazma.
- hook sahnesinde hook_text kısa ve çarpıcı olsun (maksimum 10 kelime, 2 satır).
- highlight_stat rakam veya yüzde içermeli (örn: "%73", "5 yıl", "3 gün").
- bullet_points maksimum 4 madde, her madde 8-12 kelime.
- common_mistake ve exam_tip 1-2 cümle.
- cta_text kanal adına yönlendirme içermeli: "@adimmusavir".
- Yasaklı ifadeler: "Teşekkür ederim", "Hoşçakalın", "İzlediğiniz için".
"""

_SCENE_SCHEMA = """
Storyboard JSON formatı (sahne sayısı prompt'taki talimata göre belirlenir).
ÖNEMLİ: Aşağıdaki voice_text ÖRNEKLERİ hem İÇERİK TÜRÜNÜ hem de HEDEF
UZUNLUĞU gösterir — model somut örnekleri taklit eder, bu yüzden buradaki
cümleler kısa/boş bırakılmadı. Kendi konunla değiştir ama YAKLAŞIK AYNI
UZUNLUKTA yaz; asıl bağlayıcı sayı prompt'taki HECE BÜTÇESİ / KARAKTER
SINIRI talimatıdır, bu örnekler değil.

{
  "scenes": [
    {
      "id": 1,
      "component": "ReelHookScene",
      "visual_source": "text_only",
      "hook_text": "Kısa çarpıcı kanca (2 satır, maks 10 kelime)",
      "highlight_stat": "Dikkat çeken rakam/yüzde",
      "voice_text": "SGS sınavına girenlerin yaklaşık yüzde yetmişi bu soruyu yanlış yapıyor. Sen de aynı hataya düşmeden önce bu kuralı birlikte netleştirelim."
    },
    {
      "id": 2,
      "component": "ReelConceptScene",
      "visual_source": "card",
      "title": "Neden bilmen gerekiyor?",
      "bullet_points": ["Madde 1", "Madde 2", "Madde 3"],
      "voice_text": "Bu konu her dönem sınavda karşına çıkıyor ve çoğu aday teorik bilgiyle pratik uygulamayı birbirine karıştırdığı için puan kaybediyor."
    },
    {
      "id": 3,
      "component": "ReelConceptScene",
      "visual_source": "card",
      "title": "Ana Kural / Birinci Bilgi",
      "bullet_points": ["Madde 1", "Madde 2", "Madde 3", "Madde 4"],
      "voice_text": "Kanunun ilgili maddesi net bir süre ve şart tanımlıyor. Bu süre dolmadan gerekli işlemi yapmazsan yetki belgen geçersiz sayılır ve görev yapamazsın."
    },
    {
      "id": 4,
      "component": "ReelConceptScene",
      "visual_source": "card",
      "title": "İkinci Bilgi / Örnek",
      "bullet_points": ["Madde 1", "Madde 2", "Madde 3"],
      "voice_text": "Örneğin bir aday süresini kaçırdığında yeniden başvuru sürecine girer; bu hem zaman hem de ek belge kaybı anlamına gelir, dikkatli ol."
    },
    {
      "id": 5,
      "component": "ReelMistakeScene",
      "visual_source": "card",
      "title": "Dikkat!",
      "common_mistake": "Sık yapılan hatanın 1-2 cümlelik açıklaması",
      "voice_text": "Adayların çoğu 'süre dolsa da görevime devam ederim' sanıyor. Bu tamamen yanlış — geçersiz belgeyle çalışmak kanuna aykırıdır ve cezai sonucu vardır."
    },
    {
      "id": 6,
      "component": "ReelExamTipScene",
      "visual_source": "card",
      "title": "Sınav İpucu",
      "exam_tip": "Sınava özel pratik ipucu — 1-2 cümle",
      "voice_text": "Soru kökünde süreyle ilgili bir ifade görürsen önce ilgili maddeyi hatırla, sonra şıklardaki sayılara değil kurala odaklanarak cevap ver."
    },
    {
      "id": 7,
      "component": "ReelCtaScene",
      "visual_source": "text_only",
      "title": "Özet",
      "bullet_points": ["Özet madde 1", "Özet madde 2", "Özet madde 3"],
      "cta_text": "Daha fazla SGS sorusu için @adimmusavir'i takip et!",
      "voice_text": "Özetle: süreyi takip et, belgeni zamanında yenile ve kuralı ezbere değil mantığıyla öğren. Daha fazla soru için @adimmusavir'i takip etmeyi unutma."
    }
  ]
}
"""

# segment_type → component adı eşlemesi (post-processing fallback)
_SEGMENT_COMPONENT: dict[str, str] = {
    "hook":    "ReelHookScene",
    "context": "ReelConceptScene",
    "content": "ReelConceptScene",
    "mistake": "ReelMistakeScene",
    "tip":     "ReelExamTipScene",
    "outro":   "ReelCtaScene",
}
_ALLOWED_COMPONENTS = set(_SEGMENT_COMPONENT.values()) | {
    "AccountCardScene", "JournalEntryScene", "TableScene",
    "RuleBoxScene", "CommonMistakeScene", "ReelExampleScene",
    "EducationalReelScene",
}


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
    budget_seconds: float | None = None,
    syllable_feedback: str | None = None,
    scene_count: int | None = None,
) -> dict:
    """
    EducationalReel120 composition için storyboard üretir.
    scene_count verilmezse ceil(budget_seconds / 8.0) ile hesaplanır.
    voice_text karakter sınırı üretim sonrası deterministik kontrol edilir ve
    aşılırsa 1 kez yeniden denenir — OpenAI structured outputs strict:true bile
    string maxLength'i şema seviyesinde zorlamıyor (bkz. CHARS_PER_SYLLABLE notu),
    o yüzden şemaya güvenmek yerine burada ölçülüyor.
    Döner: tam storyboard dict (video_type, scenes, brand vb.)
    """
    import math as _math
    from app.modules.content.pronunciation_dict import latex_to_spoken_turkish  # noqa: F401

    series_label = ""
    if content_series and content_series in SERIES_TITLE_TEMPLATES:
        series_label = f"İçerik serisi: {SERIES_TITLE_TEMPLATES[content_series].replace('{topic}', topic)}\n"

    desc_note = f"Ek bağlam / yönetmen notu: {description}\n" if description else ""

    min_chars: int | None = None
    max_chars: int | None = None
    budget_note = ""
    if budget_seconds is not None:
        _sc = scene_count if (scene_count and scene_count > 0) else _math.ceil(budget_seconds / 8.0)
        _sc = max(1, _sc)
        _total_syl = round(budget_seconds * TR_SPS)
        _syl_per_scene = round(_total_syl / _sc)
        _tolerance = max(3, round(_syl_per_scene * 0.15))
        # ±%15 — hem alt (kısa kalma) hem üst (aşma) sınırı somut karakter
        # sayısına çevirir. Yalnızca tavan vermek yetmiyordu: model tavanın
        # çok altında kalıp sabit ~155 hece üretmeye devam ediyordu.
        min_chars = round(_syl_per_scene * CHARS_PER_SYLLABLE * 0.85)
        max_chars = round(_syl_per_scene * CHARS_PER_SYLLABLE * 1.15)
        budget_note = (
            f"\nHECE BÜTÇESİ (ZORUNLU): Toplam {_total_syl} hece "
            f"({budget_seconds:.0f}s × {TR_SPS:.2f} hece/s, {_sc} sahne).\n"
            f"Her sahne voice_text'inde yaklaşık {_syl_per_scene} hece kullan "
            f"(±{_tolerance} tolerans, yani {_syl_per_scene - _tolerance}–{_syl_per_scene + _tolerance} arası).\n"
            f"Türkçede hece = metindeki ünlü harf sayısı (a,e,ı,i,o,ö,u,ü).\n"
            f"KARAKTER SINIRI (SERT): Her sahne voice_text'i EN AZ {min_chars}, "
            f"EN FAZLA {max_chars} karakter olmalı (boşluklar dahil). Bu aralığın "
            f"dışına çıkma — ne kısa kes ne uzat.\n"
        )
    else:
        _sc = scene_count if (scene_count and scene_count > 0) else 7

    _sc_min = _sc - 2
    _sc_max = _sc + 3

    def _attempt(extra_feedback: str) -> list[dict]:
        """Tek bir GPT üretim denemesi — prompt kur, çağır, sahneleri normalize et."""
        combined = f"{syllable_feedback or ''}\n{extra_feedback}".strip()
        feedback_note = f"\nDÜZELTME GEREKLİ (önceki üretimden): {combined}\n" if combined else ""

        prompt = f"""Aşağıdaki SGS konusu için EducationalReel120 storyboard üret.

Konu: {topic}
Ders / Alan: {subject}
Video başlığı: {title}
{series_label}{desc_note}{budget_note}{feedback_note}
{_SCENE_SCHEMA}

ÖNEMLİ: {_sc_min}–{_sc_max} sahne üret (ideal: {_sc}). Her sahnede voice_text zorunlu. Sadece JSON döndür.
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
            _scenes = data.get("scenes", [])
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
        _scenes = _norm(_scenes)

        # id'leri sırayla ata, component'i doğrula/düzelt
        _default_types = ["hook", "context", "content", "content", "mistake", "tip", "outro"]
        for i, s in enumerate(_scenes, 1):
            s["id"] = i
            # LLM bilinmeyen bileşen ürettiyse segment_type'dan türet
            if s.get("component") not in _ALLOWED_COMPONENTS:
                seg = s.get("segment_type") or (_default_types[i - 1] if i <= len(_default_types) else "content")
                s["component"] = _SEGMENT_COMPONENT.get(seg, "ReelConceptScene")
            # segment_type eksikse component'tan çıkar (reverse map)
            if not s.get("segment_type"):
                _rev = {v: k for k, v in _SEGMENT_COMPONENT.items()}
                s["segment_type"] = _rev.get(s["component"], "content")
            # voice_text eksikse basit fallback
            if not (s.get("voice_text") or "").strip():
                s["voice_text"] = s.get("hook_text") or s.get("title") or topic
        return _scenes

    scenes = _attempt("")

    # ── voice_text karakter aralığı — deterministik kontrol + 1 yeniden deneme ──
    # Şema seviyesinde zorlanamıyor (bkz. yukarıdaki not); sessizce geçilmiyor —
    # her deneme loglanır. Hem TAVAN (aşım) hem TABAN (kısa kalma) denetlenir —
    # yalnızca tavan kontrolü modelin tavanın çok altında (sabit ~155 hece)
    # takılıp kalmasını yakalayamıyordu. 2. denemede de aralık dışındaysa
    # downstream hece bütçesi kapısı (_check_syllable_budget / duration_validation_failed)
    # son savunma.
    if max_chars is not None and min_chars is not None:
        for attempt in (1, 2):
            out_of_range = [
                (s.get("id", i + 1), len(s.get("voice_text") or ""))
                for i, s in enumerate(scenes)
                if not (min_chars <= len(s.get("voice_text") or "") <= max_chars)
            ]
            if not out_of_range:
                logger.info(
                    "[voice-text-length] deneme=%d/2 tüm sahneler aralıkta (limit=%d-%d karakter)",
                    attempt, min_chars, max_chars,
                )
                break
            for scene_id, n in out_of_range:
                yon = "aşım" if n > max_chars else "kısa"
                sinir = max_chars if n > max_chars else min_chars
                pct = (n / sinir - 1) * 100
                logger.warning(
                    "[voice-text-length] deneme=%d/2 sahne=%s karakter=%d limit=%d-%d yön=%s sapma=%%%.0f",
                    attempt, scene_id, n, min_chars, max_chars, yon, pct,
                )
            if attempt == 1:
                too_long = [(sid, n) for sid, n in out_of_range if n > max_chars]
                too_short = [(sid, n) for sid, n in out_of_range if n < min_chars]
                parts = []
                if too_long:
                    parts.append(
                        "ÇOK UZUN: " + "; ".join(f"sahne {sid}: {n} karakter" for sid, n in too_long) +
                        f" — en fazla {max_chars} karaktere KISALT."
                    )
                if too_short:
                    parts.append(
                        "ÇOK KISA: " + "; ".join(f"sahne {sid}: {n} karakter" for sid, n in too_short) +
                        f" — en az {min_chars} karaktere UZAT (daha fazla ayrıntı/örnek ekle)."
                    )
                scenes = _attempt(
                    "Önceki üretimde şu sahnelerin voice_text'i karakter aralığının dışındaydı. "
                    + " ".join(parts)
                )
            else:
                logger.error(
                    "[voice-text-length] 2 denemede de karakter aralığı sağlanamadı — "
                    "downstream hece bütçesi kapısı son savunma."
                )

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
