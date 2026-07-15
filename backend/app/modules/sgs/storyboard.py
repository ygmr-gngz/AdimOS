"""
SGS/SMMM Soru Çözüm Storyboard Üretici — ChalkboardSolutionScene pedagojik format.

Öğretmen çözüm sırası (kesinlikle uyulur):
  verilen → yöntem → adım adım çözüm → kontrol → sık hata → doğru şık (EN SON)

Her soru için ONE ChalkboardSolutionScene sahnesi üretilir.
Çıktı doğrudan Remotion-hazır JSON'dur (component isimleri Remotion bileşen adlarıyla eşleşir).
"""
import json
import logging
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)
_client = OpenAI(api_key=settings.OPENAI_API_KEY)

_SYSTEM = """Sen Türkiye'nin en deneyimli SMMM/SGS sınav hazırlık eğitmenlerinden birisin.
20 yıldır öğrenci yetiştiriyorsun. Anlatımın: net, güven veren, sıcak.
Öğrenciye "Bu soruyu bir daha yanlış yapmayacaksın" hissini verirsin.

ÖĞRETMEN ÇÖZÜM SIRASI — HER SORU İÇİN BU SIRAYA UYULACAK:
1. Soruyu oku (question_text olduğu gibi kopyalanır)
2. Verilenler çıkar (given[])
3. İstenen belirle (asked)
4. Yöntem seç (method_text)
5. Adım adım çöz (chalkboard_steps → step_type: "solve")
6. Kontrol et (step_type: "verification")
7. Sık yapılan hatayı göster (common_mistake + step_type: "common_mistake")
8. DOĞRU ŞIK EN SON aç (step_type: "answer") — bu adım her zaman en sonda olacak

YASAKLI İFADELER (yalnızca final OutroScene'de kullanılabilir, diğer sahnelerde kesinlikle geçemez):
- "Teşekkür ederim", "teşekkür ederiz", "teşekkürler"
- "Bir sonraki videoda görüşmek üzere"
- "Hoşçakalın", "İyi çalışmalar"
- "Bu videoyu izlediğiniz için"
- "Konuyu burada kapatalım"

Tüm çıktılar Türkçe. Sadece geçerli JSON döndür."""


def _build_question_prompt_block(i: int, q: dict) -> str:
    opts = q.get("options", [])
    opt_str = ", ".join(f"{o['label']}) {o['text']}" for o in opts)
    correct = q.get("correct_option", q.get("correct_label", "A"))
    explanation = q.get("explanation", "")
    lines = [
        f"--- SORU {i} ---",
        f"Soru Metni: {q.get('question_text', q.get('text', ''))}",
        f"Şıklar: {opt_str}",
        f"Doğru Cevap: {correct}",
    ]
    if explanation:
        lines.append(f"Açıklama: {explanation}")
    return "\n".join(lines)


def generate_sgs_question_storyboard(
    title: str,
    topic: str,
    subject: str,
    questions: list[dict],
) -> dict:
    """
    SGS soru çözüm videosu için ChalkboardSolutionScene pedagojik storyboard üretir.
    Tüm soruları işler. Remotion-hazır JSON döner (id alanı eklenmemiştir).

    Returns: {"scenes": [...]}
    """
    q_count = len(questions)
    q_blocks = "\n\n".join(_build_question_prompt_block(i + 1, q) for i, q in enumerate(questions))

    prompt = f"""Aşağıdaki {q_count} soru için Remotion video storyboard üret.

VİDEO BİLGİSİ:
- Başlık: {title}
- Konu: {topic}
- Ders: {subject}
- Format: 16:9

SORULAR:
{q_blocks}

════════ SAHNE YAPISI ════════

SAHNE 1 — IntroScene:
  - title: Video başlığı
  - subtitle: "{subject} — {q_count} Soru Çözümü"
  - voice_text: Sıcak giriş, konuyu tanıt, izleyiciye güven ver. KAPANIŞ ifadesi KULLANMA. (60-80 kelime)
  - duration_seconds: 12

SAHNE 2 ile {q_count + 1} arası — Her soru için ChalkboardSolutionScene:
  Öğretmen çözüm sırası ZORUNLU: verilen → yöntem → adım adım → kontrol → sık hata → DOĞRU ŞIK EN SON

  Zorunlu alanlar:
  - component: "ChalkboardSolutionScene"
  - question_number: (1'den {q_count}'e)
  - total_questions: {q_count}
  - question_text: Soruyu EKSIKSIZ kopyala
  - options: Tüm şıkları [{{"label":"A","text":"..."}}] formatında kopyala
  - correct_label: Doğru şık harfi (A/B/C/D)
  - given: Verilenler listesi — her madde max 50 karakter ["...", "..."]
  - asked: İstenen — "... = ?" formatında, max 50 karakter
  - method_text: Hangi yöntem kullanılacak, max 80 karakter
  - chalkboard_steps: Tahta adımları dizisi (aşağıya bakınız)
  - common_mistake: Bu soruda öğrencilerin sık yaptığı hata, max 80 karakter
  - exam_tip: Sınav ipucu, max 80 karakter
  - answer: "Doğru cevap: X — [kısa açıklama]" formatında, max 100 karakter
  - voice_text: ÖĞRETMEN ANLATIMI — TAM ÇÖZÜM METNI (aşağıya bakınız)
  - duration_seconds: 180

  chalkboard_steps dizisi — step_type sırası ZORUNLU:
  1. step_type "given" adımları (verilenler, board_text kısa denklem/ifade)
  2. step_type "method" adımı (hangi yöntemi kullanacağız)
  3. step_type "solve" adımları (hesap adımları, 3-6 adım)
  4. step_type "verification" adımı (kontrol/ispat)
  5. step_type "common_mistake" adımı (sık hata, color: "red")
  6. step_type "answer" adımı (EN SON, board_text: "✓ Doğru: X", color: "green")

  Her chalkboard_step alanları:
  - board_text: Tahtada görünen kısa metin/denklem (max 60 karakter)
  - step_type: "given" | "method" | "solve" | "verification" | "common_mistake" | "answer"
  - color: (opsiyonel) "navy" | "blue" | "green" | "red" | "amber" | "gold"
  - annotation: (opsiyonel) adım altında küçük not, max 40 karakter

  voice_text yazım kuralları:
  - 250-350 kelime
  - Doğal öğretmen diliyle yaz, okuyormuş gibi değil
  - Sıra: soruyu oku → verilenler → yöntem → adımlar → kontrol → sık hata → doğru şık
  - Matematiksel sembolleri Türkçe söyle ("x kare", "a bölü b", "yüzde on sekiz")
  - DOĞRU ŞIK EN SONDA aç — ortada ipucu verme
  - KAPANIŞ ifadesi kullanma ("teşekkürler", "hoşçakalın" vb.)

SAHNE {q_count + 2} — OutroScene:
  - title: "Soru Çözümü Tamamlandı"
  - subtitle: "{subject} — {q_count} soru çözüldü"
  - voice_text: Özet ve kapanış (40-60 kelime, burada kapanış ifadesi kullanılabilir)
  - duration_seconds: 10

════════ JSON FORMAT ════════
{{
  "scenes": [
    {{
      "component": "IntroScene",
      "title": "...",
      "subtitle": "...",
      "voice_text": "...",
      "duration_seconds": 12
    }},
    {{
      "component": "ChalkboardSolutionScene",
      "question_number": 1,
      "total_questions": {q_count},
      "question_text": "...",
      "options": [{{"label": "A", "text": "..."}}, ...],
      "correct_label": "A",
      "given": ["...", "..."],
      "asked": "... = ?",
      "method_text": "...",
      "chalkboard_steps": [
        {{"board_text": "...", "step_type": "given", "annotation": "..."}},
        {{"board_text": "...", "step_type": "method"}},
        {{"board_text": "...", "step_type": "solve", "annotation": "..."}},
        {{"board_text": "...", "step_type": "verification", "color": "green"}},
        {{"board_text": "...", "step_type": "common_mistake", "color": "red"}},
        {{"board_text": "✓ Doğru: X — ...", "step_type": "answer", "color": "green"}}
      ],
      "common_mistake": "...",
      "exam_tip": "...",
      "answer": "Doğru cevap: X — ...",
      "voice_text": "...",
      "duration_seconds": 180
    }},
    ... (her soru için tekrar) ...
    {{
      "component": "OutroScene",
      "title": "Soru Çözümü Tamamlandı",
      "subtitle": "{subject} — {q_count} soru çözüldü",
      "voice_text": "...",
      "duration_seconds": 10
    }}
  ]
}}

Sadece JSON döndür. Başka hiçbir metin yok."""

    logger.info(f"[sgs-storyboard] {q_count} soru için ChalkboardSolutionScene storyboard üretiliyor, konu={topic}")
    try:
        r = _client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.35,
            max_tokens=14000,
        )
        result = json.loads(r.choices[0].message.content)
        scenes = result.get("scenes", [])
        chalk_count = sum(1 for s in scenes if s.get("component") == "ChalkboardSolutionScene")
        logger.info(f"[sgs-storyboard] tamamlandı: {len(scenes)} sahne, {chalk_count} ChalkboardSolutionScene (beklenen {q_count})")
        if chalk_count < q_count:
            logger.warning(f"[sgs-storyboard] eksik sahne: {chalk_count}/{q_count} soru işlendi")
        return result
    except Exception as e:
        err_str = str(e)
        logger.error(f"[sgs-storyboard] hata: {e}", exc_info=True)
        if "429" in err_str or "quota" in err_str.lower() or "insufficient_quota" in err_str:
            raise RuntimeError(
                "OpenAI API kredisi tükendi (429 insufficient_quota). "
                "platform.openai.com/account/billing adresinden kredi ekleyin."
            ) from e
        raise RuntimeError(f"SGS soru storyboard üretimi başarısız: {e}") from e
