"""
SGS Çok Sorulu Video Storyboard Üretici — Hoca Tarzı, Detaylı Çözüm.

Her soru için 6 sahne:
  soru_okuma → adim_adim_cozum → sik_analizi → dogru_cevap → tuzak_uyarisi → pratik_bilgi

Hedef toplam süre: 20-25 dakika (5 soru)
"""
import json
import logging
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)
_client = OpenAI(api_key=settings.OPENAI_API_KEY)

_SYSTEM = """Sen Türkiye'nin en deneyimli SGS (Serbest Muhasebeci Mali Müşavirlik) eğitmenlerinden birisin.
20 yıldır bu sınavı hazırlıyorsun ve öğrencilerinin büyük çoğunluğu sınavı geçiyor.
Anlatım tarzın: sıcak, güven veren, net. Karmaşık konuları sade Türkçeyle açıklıyorsun.
Sınavda tekrar eden tuzaklara ve püf noktalara özellikle dikkat çekiyorsun.
Öğrencine "Sen bunu yapabilirsin, bu soruyu bir daha yanlış yapmayacaksın" hissini veriyorsun.
Tüm çıktılar Türkçe olacak."""


def _build_question_block(i: int, q: dict) -> str:
    """Tek soru için prompt bloğu oluşturur."""
    diff = q.get("difficulty", "orta")
    year = q.get("year", "")
    year_note = f" ({year} yılı çıkmış)" if year else ""
    explanation = q.get("explanation", "")
    correct = q.get("correct_option", "A")

    lines = [
        f"SORU {i}{year_note} | Zorluk: {diff}",
        f"Soru Metni: {q.get('question_text', '')}",
        f"Şıklar: {json.dumps(q.get('options', []), ensure_ascii=False)}",
        f"Doğru Cevap: {correct}",
    ]
    if explanation:
        lines.append(f"Açıklama: {explanation}")
    return "\n".join(lines)


def generate_sgs_topic_storyboard(
    title: str,
    topic: str,
    subject: str,
    questions: list[dict],
) -> dict:
    """
    SGS konu videosu için hoca tarzı detaylı storyboard üretir.

    Her soru için zorunlu 6 sahne:
      question → concept (adım adım) → option_analysis → answer → exam_tip (tuzak) → content (pratik)
    """
    q_count = len(questions)
    total_target = q_count * 4    # soru başı 4 dakika hedef
    q_blocks = "\n\n".join(_build_question_block(i + 1, q) for i, q in enumerate(questions))

    prompt = f"""Aşağıdaki {q_count} SGS sorusu için profesyonel eğitim videosu storyboard'u oluştur.

VIDEO BİLGİLERİ:
- Başlık: {title}
- Konu: {topic}
- Ders: {subject}
- Soru Sayısı: {q_count}
- Hedef Süre: ~{total_target} dakika

SORULAR:
{q_blocks}

════════════════════════════════════════
SAHNE YAPISI — BU SIRAYA UYULACAK
════════════════════════════════════════

1. "intro" sahnesi (1 adet):
   - Başlık + "Bu videoda ne çözüyoruz" + soru sayısı
   - narration: Sıcak karşılama, konuyu tanıt, izleyiciye güven ver (80-100 kelime)

2. "concept" sahnesi — KONU GİRİŞİ (1 adet):
   - {topic} konusunda sınav için BİLİNMESİ GEREKEN temel kurallar (4-6 madde)
   - narration: "Bu konudan her sınav döneminde mutlaka soru çıkıyor..." tarzı giriş (120-150 kelime)
   - display_lines: Her madde max 45 karakter, numaralı

3. HER SORU İÇİN 6 SAHNE (soru 1'den {q_count}'e kadar sırayla):

   SAHNE A — "question" (Soru Okuma):
   - question_text: Soruyu kelime kelime, net oku
   - options: Tüm şıkları listele
   - narration: Soruyu yüksek sesle oku, "Şimdi bu soruya dikkatli bakalım" + ilk izlenim notu (80-100 kelime)
   - duration: 10.0

   SAHNE B — "concept" (Adım Adım Çözüm):
   - title: "Adım Adım Çözüm — Soru {{N}}"
   - display_lines: Çözüm adımları (1. ..., 2. ..., 3. ...) max 5 adım
   - narration: Soruyu nasıl çözdüğünü adım adım anlat. Hangi bilgiyi kullandın, neden bu yola gittin. Öğrenci aklında canlandırabilsin. (150-200 kelime)
   - duration: 15.0

   SAHNE C — "option_analysis" (Şık Analizi):
   - options: Tüm şıkları listele
   - correct_option: Doğru şık harfi
   - display_lines: Her YANLIŞ şık için neden yanlış (max 2 satır/şık)
   - narration: Her yanlış şığı tek tek ele al. "A şıkkı neden yanlış? Çünkü..." formatında. Öğrencinin zihnindeki yanlış anlamayı düzelt. (120-150 kelime)
   - duration: 12.0

   SAHNE D — "answer" (Doğru Cevap):
   - options: Tüm şıkları listele
   - correct_option: Doğru şık harfi
   - explanation: Neden doğru olduğunun tam açıklaması
   - narration: Doğru cevabı açıkla. Neden doğru? Hangi kanun maddesi, hangi kural? Somut bağlantı kur. (100-130 kelime)
   - duration: 10.0

   SAHNE E — "exam_tip" (Tuzak Uyarısı):
   - tip: "⚠️ TUZAK: ..." veya "DİKKAT: ..." formatında, max 80 karakter
   - narration: Bu sorunun tuzağını, sınavda hangi hataların yapıldığını anlat. "Bu soruyu yanlış yapan öğrencilerin %80'i şunu düşünüyor, ama..." (80-100 kelime)
   - duration: 7.0

   SAHNE F — "content" (Pratik Bilgi):
   - title: "Pratik Bilgi — {topic}"
   - display_lines: 3-4 pratik bilgi maddesi, max 45 karakter/madde
   - narration: Bu konuyla ilgili sınavda faydalı pratik bilgiler. Ezber değil, anlayarak öğrenme. (80-100 kelime)
   - duration: 8.0

4. "summary" sahnesi (1 adet, EN SONDA):
   - title: "{q_count} Sorunun Özeti"
   - rows: Her soru için {{label: "Soru N", value: "Doğru: X — bir satır açıklama"}}
   - narration: Tüm soruları özetle. "Bugün öğrendikleriniz..." (60-80 kelime)

5. "cta" sahnesi (1 adet, EN SON):
   - narration: Abone çağrısı, gelecek içerik. Sıcak kapanış. (40-50 kelime)

════════════════════════════════════════
ZORUNLU KURALLAR
════════════════════════════════════════
- Tüm narration'lar TÜRKÇE, doğal konuşma dili
- display_lines: Her satır max 45 karakter, max 5 satır
- concept sahnesi display_lines numaralı olacak: "1. ...", "2. ...", vb.
- question sahnesi: question_text EKSIKSIZ kopyalanacak
- option_analysis ve answer sahnesinde options[] EKSIKSIZ kopyalanacak
- exam_tip sahnesi: tip alanı "⚠️" ile başlayacak
- Toplam sahne sayısı: 2 + ({q_count} × 6) + 2 = {2 + q_count * 6 + 2}
- Sadece JSON döndür, başka hiçbir şey yok

JSON FORMATI:
{{
  "title": "{title}",
  "description": "YouTube açıklaması, 400-500 karakter, hashtag ile biter",
  "tags": ["sgs", "çıkmış sorular", "{subject.lower()}", "{topic.lower()}", "sgs sınavı"],
  "estimated_duration_minutes": {total_target},
  "scenes": [
    {{
      "type": "intro",
      "title": "{title[:50]}",
      "narration": "...",
      "display_lines": ["{title[:45]}", "{q_count} Soru Çözümü", "{subject}"]
    }},
    {{
      "type": "concept",
      "title": "Konuya Giriş: {topic}",
      "narration": "...",
      "display_lines": ["1. Birinci kural...", "2. İkinci kural...", "3. Üçüncü kural..."]
    }},
    ... (her soru için 6 sahne: A, B, C, D, E, F) ...
    {{
      "type": "summary",
      "title": "Bugün Neler Çözdük?",
      "narration": "...",
      "rows": [{{"label": "Soru 1", "value": "Doğru: A — özet"}}]
    }},
    {{
      "type": "cta",
      "title": "Son",
      "narration": "...",
      "display_lines": []
    }}
  ]
}}"""

    logger.info(f"[sgs-storyboard] storyboard üretiliyor: {q_count} soru, konu={topic}, hedef={total_target}dk")
    try:
        r = _client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=12000,
        )
        result = json.loads(r.choices[0].message.content)
        scene_count = len(result.get("scenes", []))
        expected = 2 + q_count * 6 + 2
        logger.info(f"[sgs-storyboard] tamamlandı: {scene_count} sahne (beklenen ~{expected})")
        return result
    except Exception as e:
        err_str = str(e)
        logger.error(f"[sgs-storyboard] hata: {e}", exc_info=True)
        if "429" in err_str or "quota" in err_str.lower() or "insufficient_quota" in err_str:
            raise RuntimeError(
                "OpenAI API kredisi tükendi (429 insufficient_quota). "
                "platform.openai.com/account/billing adresinden kredi ekleyin, "
                "ardından videoyu yeniden deneyin."
            ) from e
        raise RuntimeError(f"SGS storyboard üretimi başarısız: {e}") from e
