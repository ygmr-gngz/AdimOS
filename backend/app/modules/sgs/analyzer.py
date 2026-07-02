"""
SGS PDF Soru Analiz Ajanı.

PDF metnini okur, tüm soruları çıkarır, SGS derslerine göre gruplar,
her soru için ders güven skoru (lesson_confidence) hesaplar,
ders başına video planı oluşturur.
"""
import json
import logging
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)
_client = OpenAI(api_key=settings.OPENAI_API_KEY)

_MAX_CHARS = 90_000
_COMPACT_THRESHOLD = 55_000  # Bu sınırın üstünde kompakt format kullan (explanation yok)

# SGS sınavındaki 17 ders — tek kaynak
SGS_LESSONS = [
    "Türkçe",
    "Matematik",
    "Tarih - Genel Kültür",
    "İngilizce",
    "Almanca",
    "Finansal Muhasebe",
    "Muhasebe Standartları",
    "Muhasebe Bilgi Sistemi",
    "Maliyet Muhasebesi",
    "Mali Tablolar Analizi",
    "Muhasebe Denetimi",
    "İktisat",
    "Maliye",
    "Meslek Hukuku",
    "İş ve Sosyal Güvenlik Hukuku",
    "Vergi Hukuku",
    "Ticaret Hukuku",
    "Borçlar Hukuku",
]

_LESSON_KEYWORDS = """
DERS SINIFLANDIRMA REHBERI (örnekler):

Türkçe: paragraf, cümle, sözcük, yazım, noktalama, anlam, anlatım bozukluğu, dil bilgisi, fiil, isim, sıfat, dil yanlışı, metinde anlam
Matematik: sayı, toplam, çarpım, bölme, oran, yüzde, olasılık, geometri, alan, çevre, denklem, küme, mantık, fonksiyon, permütasyon, kombinasyon, logaritma, istatistik
Tarih - Genel Kültür: tarih, coğrafya, Türkiye, Osmanlı, Cumhuriyet, siyaset, kültür, sanat, Atatürk, uygarlık, kurtuluş savaşı, inkılap
İngilizce: english, grammar, vocabulary, tense, sentence, meaning, reading, translation, word, in english
Almanca: deutsch, grammatik, vokabeln, satz, bedeutung, leseverstehen, übersetzung, wort, auf deutsch, almanca
Finansal Muhasebe: yevmiye, mizan, aktif, pasif, hesap, dönem sonu, stok, kasa, banka, amortisman, hesap planı, tek düzen, defter-i kebir
Muhasebe Standartları: TMS, TFRS, standart, muhasebe politikası, dipnot, konsolidasyon, ölçüm, gerçeğe uygun değer, finansal tablo
Muhasebe Bilgi Sistemi: bilgi sistemi, yazılım, muhasebe programı, veri, kayıt sistemi, otomasyon, elektronik defter
Maliyet Muhasebesi: maliyet, üretim maliyeti, direkt ilk madde, işçilik, genel üretim gideri, sipariş, safha, standart maliyet, fark analizi
Mali Tablolar Analizi: bilanço, gelir tablosu, rasyo, oran analizi, likidite, karlılık, finansman, cari oran, devir hızı, dikey analiz, yatay analiz, nakit akım
Muhasebe Denetimi: denetim, iç kontrol, iç denetim, bağımsız denetim, denetçi, denetim kanıtı, risk, örnekleme, rapor, hile
İktisat: arz, talep, piyasa, fiyat, enflasyon, deflasyon, faiz, para, bankacılık, büyüme, GSYH, denge, elastikiyet, monopol, oligopol
Maliye: bütçe, kamu geliri, kamu gideri, vergi teorisi, Türk vergi sistemi, maliye politikası, vergi yükü, borçlanma, kamu açığı
Meslek Hukuku: SMMM, YMM, staj, meslek odası, etik, disiplin, ruhsat, sorumluluk, mesleki
İş ve Sosyal Güvenlik Hukuku: işçi, işveren, iş sözleşmesi, kıdem tazminatı, ihbar, izin, SGK, prim, emeklilik, iş kazası, sigorta, sosyal güvenlik
Vergi Hukuku: vergi, gelir vergisi, kurumlar vergisi, KDV, stopaj, beyanname, tarh, tahakkuk, tahsil, vergi usul, KDVK, GVK, KVK
Ticaret Hukuku: tacir, ticaret sicili, işletme, şirket, anonim, limited, komandit, ticaret unvanı, ticari defter, kambiyo, çek, senet, poliçe
Borçlar Hukuku: borç, alacak, sözleşme, teklif, kabul, haksız fiil, sebepsiz zenginleşme, zamanaşımı, cayma, ibra, takas

KRİTİK EŞLEŞTİRME KURALLARI (yanlış sınıflandırmayı önler, MUTLAKA uy):
- "Denklemler", "Fonksiyonlar", "Geometri", "Kümeler", "Logaritma" → HER ZAMAN Matematik
- "Bilanço", "Gelir Tablosu", "Nakit Akım" → HER ZAMAN Mali Tablolar Analizi (Finansal Muhasebe DEĞİL)
- "Yevmiye", "Mizan", "Amortisman" → HER ZAMAN Finansal Muhasebe
- "Cumhuriyet Tarihi", "Atatürk İlkeleri", "İnkılap" → HER ZAMAN Tarih - Genel Kültür
- Matematik terimleri (denklem, küme, olasılık) → Türkçe DEĞİL, Matematik
"""


def _detect_language_from_filename(pdf_name: str) -> str | None:
    """Dosya adından dil tespiti: ingilizce/almanca PDF'leri yakalar."""
    n = pdf_name.lower().replace("İ", "i").replace("ı", "i")
    if any(k in n for k in ("ingilizce", "inglizce", "english", "_ing", "-ing", "ing_", "ing-")):
        return "İngilizce"
    if any(k in n for k in ("almanca", "german", "deutsch", "_alm", "-alm", "alm_", "alm-")):
        return "Almanca"
    return None


def analyze_sgs_pdf(pdf_text: str, pdf_name: str = "") -> dict:
    """
    PDF metni → yapılandırılmış soru analizi + video serisi planı.
    Büyük PDF'lerde (>_COMPACT_THRESHOLD) explanation/lesson_reason çıkarılır,
    token bütçesi korunur ve 16k output limiti içinde kalınır.
    """
    text_chunk = pdf_text[:_MAX_CHARS]
    is_large = len(text_chunk) > _COMPACT_THRESHOLD

    if len(pdf_text) > _MAX_CHARS:
        logger.warning(f"[sgs-analyzer] PDF çok uzun ({len(pdf_text)} karakter), ilk {_MAX_CHARS} karakter kullanılıyor")
    if is_large:
        logger.info(f"[sgs-analyzer] Büyük PDF ({len(text_chunk)} karakter) — kompakt format kullanılıyor")

    lessons_str = "\n".join(f"- {l}" for l in SGS_LESSONS)

    if is_large:
        question_example = """\
    {{
      "id": 1,
      "subject": "Finansal Muhasebe",
      "topic": "Bilanço",
      "year": "2023",
      "difficulty": "orta",
      "question_text": "Tam soru metni...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_option": "C",
      "lesson_confidence": 0.95
    }}"""
        extra_instructions = "NOT: Bu büyük bir PDF. explanation ve lesson_reason alanlarını YAZMA, token tasarrufu için."
    else:
        question_example = """\
    {{
      "id": 1,
      "subject": "Finansal Muhasebe",
      "topic": "Bilanço",
      "year": "2023",
      "difficulty": "orta",
      "question_text": "Tam soru metni...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_option": "C",
      "explanation": "C şıkkı doğrudur çünkü...",
      "lesson_confidence": 0.95,
      "lesson_reason": "Soruda bilanço, aktif, pasif kavramları geçiyor."
    }}"""
        extra_instructions = ""

    prompt = f"""Sen SGS (Staj ve Yeterlik Sınavı) sınav soruları uzmanısın.
Aşağıdaki PDF metni SGS çıkmış sorularını içeriyor.
{extra_instructions}

GÖREV:
1. Tüm soruları çıkar (soru metni + şıklar + doğru cevap)
2. Her soruyu SGS ders listesinden birine ata (SADECE aşağıdaki liste)
3. Her soru için lesson_confidence (0.0-1.0) ver
4. Aynı konudan soruları grupla, video serisi planı oluştur

SGS DERS LİSTESİ (SADECE bu 17 dersten birini kullan):
{lessons_str}

{_LESSON_KEYWORDS}

SINIFLANDIRMA KURALLARI:
- Sorudaki anahtar kelimeler ve kavramlar hangi derse işaret ediyor?
- Emin değilsen lesson_confidence < 0.6 olarak işaretle
- Güven skoru 0.6'nın altındaysa subject alanına "Belirsiz" yaz
- HİÇBİR ZAMAN kendi uydurduğun ders adı yazma, sadece yukarıdaki 17 dersten birini kullan

ZORLUK SEVİYELERİ:
- "kolay": kavram bilgisi yeterli
- "orta": kural + uygulama
- "zor": hesaplama veya çok kural

VİDEO PLANLAMA:
- Video başına en fazla 5 soru (ideal: 3-4)
- Aynı ders ve konudan sorular aynı videoda
- "Belirsiz" sorular video planına dahil edilmez

PDF METNİ:
{text_chunk}

Türkçe olarak yanıtla. SADECE JSON döndür:
{{
  "pdf_name": "{pdf_name}",
  "total_questions": 40,
  "subjects": [
    {{
      "name": "Finansal Muhasebe",
      "question_count": 10,
      "topics": ["Bilanço", "Yevmiye Defteri"]
    }}
  ],
  "questions": [
{question_example}
  ],
  "video_plan": [
    {{
      "video_number": 1,
      "title": "SGS Finansal Muhasebe: Bilanço Çıkmış Sorular",
      "topic": "Bilanço",
      "subject": "Finansal Muhasebe",
      "question_ids": [1, 5, 12],
      "estimated_duration": "8-10 dakika",
      "description": "Bilanço konusundan çıkmış 3 soru adım adım çözülüyor."
    }}
  ]
}}"""

    max_tokens = 16000 if is_large else 12000
    logger.info(f"[sgs-analyzer] analiz başladı: {pdf_name}, {len(text_chunk)} karakter, max_tokens={max_tokens}")

    try:
        r = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=max_tokens,
        )

        finish_reason = r.choices[0].finish_reason
        raw_content = r.choices[0].message.content or ""

        if finish_reason == "length":
            logger.error(
                f"[sgs-analyzer] HATA: max_tokens ({max_tokens}) aşıldı — "
                f"JSON kesildi. PDF: {pdf_name}, karakter: {len(text_chunk)}"
            )
            raise ValueError(
                f"PDF çok büyük veya çok fazla soru içeriyor ({len(text_chunk)} karakter). "
                f"Lütfen PDF'i bölerek tekrar yükleyin."
            )

        try:
            result = json.loads(raw_content)
        except json.JSONDecodeError as je:
            logger.error(f"[sgs-analyzer] JSON parse hatası: {je} — içerik: {raw_content[:200]}")
            raise ValueError("LLM yanıtı geçerli JSON değil. Lütfen tekrar deneyin.") from je

        # Dosya adından dil tespiti — AI'dan önce güvenilir
        forced_lang = _detect_language_from_filename(pdf_name)
        if forced_lang:
            logger.info(f"[sgs-analyzer] dosya adı dil tespiti: {pdf_name!r} → {forced_lang}")
            for q in result.get("questions", []):
                if q.get("subject") != forced_lang:
                    q["original_subject"] = q.get("subject", "")
                    q["subject"] = forced_lang
                    q["lesson_confidence"] = 1.0
                    q["lesson_reason"] = f"Dosya adı tespiti: {pdf_name}"
        else:
            # Güven skoru düşük sorularda subject'i "Belirsiz" yap
            for q in result.get("questions", []):
                conf = float(q.get("lesson_confidence", 1.0))
                if conf < 0.6 and q.get("subject") != "Belirsiz":
                    q["original_subject"] = q["subject"]
                    q["subject"] = "Belirsiz"

        logger.info(
            f"[sgs-analyzer] tamamlandı: {result.get('total_questions', '?')} soru, "
            f"{len(result.get('video_plan', []))} video planı, finish_reason={finish_reason}"
        )
        return result

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"[sgs-analyzer] beklenmedik hata: {e}", exc_info=True)
        raise RuntimeError(f"SGS analizi başarısız: {e}") from e
