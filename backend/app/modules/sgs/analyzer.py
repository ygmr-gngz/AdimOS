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

# SGS sınavındaki 17 ders — tek kaynak
SGS_LESSONS = [
    "Türkçe",
    "Matematik",
    "Tarih-Genel Kültür",
    "İngilizce",
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
Matematik: sayı, toplam, çarpım, bölme, oran, yüzde, olasılık, geometri, alan, çevre, denklem, küme, mantık, fonksiyon
Tarih-Genel Kültür: tarih, coğrafya, Türkiye, Osmanlı, Cumhuriyet, siyaset, kültür, sanat, Atatürk, uygarlık
İngilizce: english, grammar, vocabulary, tense, sentence, meaning, reading, translation, word
Finansal Muhasebe: bilanço, yevmiye, mizan, aktif, pasif, borç, alacak, hesap, dönem sonu, stok, kasa, banka, amortisman, gelir tablosu, hesap planı, tek düzen
Muhasebe Standartları: TMS, TFRS, standart, muhasebe politikası, dipnot, konsolidasyon, ölçüm, gerçeğe uygun değer, finansal tablo
Muhasebe Bilgi Sistemi: bilgi sistemi, yazılım, muhasebe programı, veri, kayıt sistemi, otomasyon, elektronik defter
Maliyet Muhasebesi: maliyet, üretim maliyeti, direkt ilk madde, işçilik, genel üretim gideri, sipariş, safha, standart maliyet, fark analizi
Mali Tablolar Analizi: rasyo, oran analizi, likidite, karlılık, finansman, cari oran, devir hızı, dikey analiz, yatay analiz, trend
Muhasebe Denetimi: denetim, iç kontrol, iç denetim, bağımsız denetim, denetçi, denetim kanıtı, risk, örnekleme, rapor, hile
İktisat: arz, talep, piyasa, fiyat, enflasyon, deflasyon, faiz, para, bankacılık, büyüme, GSYH, denge, elastikiyet, monopol, oligopol
Maliye: bütçe, kamu geliri, kamu gideri, vergi teorisi, Türk vergi sistemi, maliye politikası, vergi yükü, borçlanma, kamu açığı
Meslek Hukuku: SMMM, YMM, staj, meslek odası, etik, disiplin, ruhsat, sorumluluk, mesleki
İş ve Sosyal Güvenlik Hukuku: işçi, işveren, iş sözleşmesi, kıdem tazminatı, ihbar, izin, SGK, prim, emeklilik, iş kazası, sigorta, sosyal güvenlik
Vergi Hukuku: vergi, gelir vergisi, kurumlar vergisi, KDV, stopaj, beyanname, tarh, tahakkuk, tahsil, vergi usul, KDVK, GVK, KVK
Ticaret Hukuku: tacir, ticaret sicili, işletme, şirket, anonim, limited, komandit, ticaret unvanı, ticari defter, kambiyo, çek, senet, poliçe
Borçlar Hukuku: borç, alacak, sözleşme, teklif, kabul, haksız fiil, sebepsiz zenginleşme, zamanaşımı, cayma, ibra, takas
"""


def analyze_sgs_pdf(pdf_text: str, pdf_name: str = "") -> dict:
    """
    PDF metni → yapılandırılmış soru analizi + video serisi planı.
    Her soru için lesson_confidence (0.0-1.0) ve lesson_reason döner.
    Güven skoru 0.6'nın altındaysa subject = "Belirsiz" olarak işaretlenir.
    """
    text_chunk = pdf_text[:_MAX_CHARS]
    if len(pdf_text) > _MAX_CHARS:
        logger.warning(f"[sgs-analyzer] PDF çok uzun ({len(pdf_text)} karakter), ilk {_MAX_CHARS} karakter analiz ediliyor")

    lessons_str = "\n".join(f"- {l}" for l in SGS_LESSONS)

    prompt = f"""Sen SGS (Staj ve Yeterlik Sınavı) sınav soruları uzmanısın.
Aşağıdaki PDF metni SGS çıkmış sorularını içeriyor.

GÖREV:
1. Tüm soruları çıkar (soru metni + şıklar + doğru cevap)
2. Her soruyu SGS ders listesinden birine ata (SADECE aşağıdaki liste)
3. Her soru için lesson_confidence (0.0-1.0) ve lesson_reason ver
4. Aynı konudan soruları grupla, video serisi planı oluştur

SGS DERS LİSTESİ (SADECE bu 17 dersten birini kullan):
{lessons_str}

{_LESSON_KEYWORDS}

SINIFLANDIRMA KURALLARI:
- Sorudaki anahtar kelimeler ve kavramlar hangi derse işaret ediyor?
- Emin değilsen lesson_confidence < 0.6 olarak işaretle
- Güven skoru 0.6'nın altındaysa subject alanına "Belirsiz" yaz, gerçek tahminini lesson_reason'a ekle
- HİÇBİR ZAMAN kendi uydurduğun ders adı yazma, sadece yukarıdaki 17 dersten birini kullan
- Muhasebe sorusu Türkçe dersi olarak işaretlenemez; Türkçe sorusu muhasebe dersi olamaz

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
    }}
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

    logger.info(f"[sgs-analyzer] analiz başladı: {pdf_name}, {len(text_chunk)} karakter")
    try:
        r = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=8000,
        )
        result = json.loads(r.choices[0].message.content)

        # Güven skoru düşük sorularda subject'i "Belirsiz" yap
        for q in result.get("questions", []):
            conf = float(q.get("lesson_confidence", 1.0))
            if conf < 0.6 and q.get("subject") != "Belirsiz":
                q["original_subject"] = q["subject"]
                q["subject"] = "Belirsiz"

        logger.info(
            f"[sgs-analyzer] tamamlandı: {result.get('total_questions', '?')} soru, "
            f"{len(result.get('video_plan', []))} video planı"
        )
        return result
    except Exception as e:
        logger.error(f"[sgs-analyzer] hata: {e}", exc_info=True)
        raise RuntimeError(f"SGS analizi başarısız: {e}") from e
