"""
SGS PDF Soru Analiz Ajanı.

PDF metnini okur, tüm soruları çıkarır, konuya göre gruplar,
konu başına ideal video planı oluşturur.
"""
import json
import logging
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)
_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# GPT'ye göndereceğimiz max metin (token sınırı için)
_MAX_CHARS = 90_000


def analyze_sgs_pdf(pdf_text: str, pdf_name: str = "") -> dict:
    """
    PDF metni → yapılandırılmış soru analizi + video serisi planı.

    Döndürür:
    {
      pdf_name, total_questions,
      subjects: [{name, question_count, topics[]}],
      questions: [{id, subject, topic, year, difficulty, question_text, options[], correct_option, explanation}],
      video_plan: [{video_number, title, topic, subject, question_ids[], estimated_duration, description}]
    }
    """
    text_chunk = pdf_text[:_MAX_CHARS]
    if len(pdf_text) > _MAX_CHARS:
        logger.warning(f"[sgs-analyzer] PDF çok uzun ({len(pdf_text)} karakter), ilk {_MAX_CHARS} karakter analiz ediliyor")

    prompt = f"""Sen SGS (Serbest Girişimci Sertifikası) sınav soruları uzmanısın.

Aşağıdaki PDF metni SGS çıkmış sorularını içeriyor.

GÖREV:
1. Tüm soruları çıkar (soru metni + şıklar + doğru cevap varsa)
2. Her soruyu konusuna, dersine ve zorluk seviyesine göre sınıflandır
3. Aynı konudan soruları grupla
4. Her konu grubu için video serisi planı oluştur

VİDEO PLANLAMA KURALLARI:
- Video başına en fazla 5 soru (ideal: 3-4)
- Aynı konudan sorular aynı videoda olmalı
- Farklı konu → farklı video
- Çok az soru varsa (1-2) → komşu konuyla birleştir
- Video süresi tahmini: soru başına ~2-3 dk

ZORLUK SEVİYELERİ:
- "kolay": kavram bilgisi yeterli
- "orta": kural + uygulama
- "zor": çok kural + detay veya hesaplama

DERSLERE ÖRNEKLER (SGS sınav dersleri):
- Ticaret Hukuku, İş Hukuku, Vergi Hukuku, Muhasebe,
  SGK/Sosyal Güvenlik, İdare Hukuku, Medeni Hukuk,
  Borçlar Hukuku, Serbest Muhasebecilik Mevzuatı

PDF METNİ:
{text_chunk}

Türkçe olarak yanıtla. Sadece JSON döndür:
{{
  "pdf_name": "{pdf_name}",
  "total_questions": 40,
  "subjects": [
    {{
      "name": "Ticaret Hukuku",
      "question_count": 8,
      "topics": ["Tacir ve İşletme", "Ticaret Unvanı", "Şirket Türleri"]
    }}
  ],
  "questions": [
    {{
      "id": 1,
      "subject": "Ticaret Hukuku",
      "topic": "Tacir ve Tacir Yardımcıları",
      "year": "2023",
      "difficulty": "orta",
      "question_text": "Tam soru metni burada...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_option": "C",
      "explanation": "C şıkkı doğrudur çünkü..."
    }}
  ],
  "video_plan": [
    {{
      "video_number": 1,
      "title": "SGS Ticaret Hukuku: Tacir ve Tacir Yardımcıları Çıkmış Sorular",
      "topic": "Tacir ve Tacir Yardımcıları",
      "subject": "Ticaret Hukuku",
      "question_ids": [1, 5, 12],
      "estimated_duration": "8-10 dakika",
      "description": "Bu videoda tacir tanımı ve tacir yardımcıları konusundan çıkmış 3 soru adım adım çözülüyor."
    }}
  ]
}}"""

    logger.info(f"[sgs-analyzer] analiz başladı: {pdf_name}, {len(text_chunk)} karakter")
    try:
        r = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=8000,
        )
        result = json.loads(r.choices[0].message.content)
        logger.info(f"[sgs-analyzer] tamamlandı: {result.get('total_questions', '?')} soru, {len(result.get('video_plan', []))} video planı")
        return result
    except Exception as e:
        logger.error(f"[sgs-analyzer] hata: {e}", exc_info=True)
        raise RuntimeError(f"SGS analizi başarısız: {e}") from e
