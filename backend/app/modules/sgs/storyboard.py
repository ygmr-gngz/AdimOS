"""
SGS Çok Sorulu Video Storyboard Üretici.

Konu başına 3-5 soru akışı:
  intro → concept → [soru → analiz → cevap → ipucu] × N → özet → cta
"""
import json
import logging
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)
_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_sgs_topic_storyboard(
    title: str,
    topic: str,
    subject: str,
    questions: list[dict],
) -> dict:
    """
    SGS konu videosu için sahne bazlı storyboard üretir.

    questions: [{question_text, options[], correct_option, explanation, difficulty, year?}]
    """
    q_json = json.dumps(questions, ensure_ascii=False, indent=2)

    # Soru sayısına göre per-soru akış planı
    per_q_flows = []
    for i, q in enumerate(questions, 1):
        diff = q.get("difficulty", "orta")
        year = q.get("year", "")
        year_note = f" ({year} çıkmış)" if year else ""
        if diff == "zor":
            per_q_flows.append(f"Soru {i}{year_note} → şık analizi → doğru cevap → püf nokta")
        else:
            per_q_flows.append(f"Soru {i}{year_note} → doğru cevap → kısa not")
    flows_text = "\n".join(per_q_flows)

    prompt = f"""Sen SGS sınav videoları hazırlayan bir eğitim içerik uzmanısın.

Aşağıdaki SGS soru grubunu konu anlatımlı çözüm videosu olarak hazırla.

VİDEO BİLGİSİ:
Başlık: {title}
Konu: {topic}
Ders: {subject}
Soru Sayısı: {len(questions)}

SORU VERİSİ:
{q_json}

SAHNE AKIŞI (bu sırayı takip et):
1. intro — Video başlığı ve "Bu videoda ne öğreneceksiniz"
2. concept — Bu konunun temel kuralları (sınav için ne bilinmesi gerekiyor, 3-5 madde)
{flows_text}
Son-1. summary — Tüm soruların özet tablosu
Son. cta — Abone çağrısı

PER-SORU SAHNE KURALLARI:
- Zor soru → 3 sahne: question + option_analysis + answer + exam_tip (4 sahne)
- Normal soru → 2 sahne: question + answer (+ exam_tip varsa 3)
- question sahnesi: question_text, options[] ZORUNLU
- option_analysis: options[], correct_option ZORUNLU, display_lines neden yanlış açıklamalı
- answer: options[], correct_option, explanation ZORUNLU
- exam_tip: tip alanı — sınavda dikkat noktası (max 120 karakter, öz)

GENEL KURALLAR:
- TÜM METİNLER TÜRKÇE OLMALIDIR
- narration: doğal konuşma Türkçesi, TTS için
- display_lines: ekranda görünür, max 5 satır, her satır max 50 karakter
- summary sahnesinin rows[] alanı: her soru için {{label: "Soru N", value: "Doğru: X — kısa açıklama"}}
- Sadece JSON döndür

JSON FORMATI:
{{
  "title": "{title}",
  "description": "YouTube açıklaması (hashtag dahil, 500 karakter)",
  "tags": ["sgs", "çıkmış sorular", "{subject.lower()}", "sgs sınavı"],
  "scenes": [
    {{
      "type": "intro",
      "title": "Giriş",
      "narration": "Merhaba! Bu videoda {topic} konusundan {len(questions)} soru çözüyoruz.",
      "display_lines": ["{title[:45]}", "{len(questions)} Soru Çözümü"]
    }},
    {{
      "type": "concept",
      "title": "Temel Kurallar",
      "narration": "Sorulara geçmeden önce bu konuda bilmeniz gereken temel kuralları özetleyelim.",
      "display_lines": ["1. Birinci kural", "2. İkinci kural", "3. Üçüncü kural"]
    }},
    ... (her soru için sahneler) ...
    {{
      "type": "summary",
      "title": "Özet",
      "narration": "Bugün çözdüğümüz soruları özetleyelim.",
      "rows": [
        {{"label": "Soru 1", "value": "Doğru: X — kısa açıklama"}},
        {{"label": "Soru 2", "value": "Doğru: Y — kısa açıklama"}}
      ]
    }},
    {{
      "type": "cta",
      "title": "Son",
      "narration": "Videoyu beğendiyseniz abone olmayı unutmayın. SGS çıkmış sorular için Adım Müşavir.",
      "display_lines": []
    }}
  ]
}}"""

    logger.info(f"[sgs-storyboard] storyboard üretiliyor: {len(questions)} soru, konu={topic}")
    try:
        r = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=6000,
        )
        result = json.loads(r.choices[0].message.content)
        logger.info(f"[sgs-storyboard] tamamlandı: {len(result.get('scenes', []))} sahne")
        return result
    except Exception as e:
        logger.error(f"[sgs-storyboard] hata: {e}", exc_info=True)
        raise RuntimeError(f"SGS storyboard üretimi başarısız: {e}") from e
