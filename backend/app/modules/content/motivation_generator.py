"""
SGS/SMMM adayları için 120 saniye motivasyon video storyboard üreticisi.
Çıktı: component alanı dahil tam storyboard JSON.
"""
import logging
import math
import re
from app.core.llm_client import chat_json as llm_json

logger = logging.getLogger(__name__)

# MotivationStepScene rozeti/etiketi step_number'dan (sahne indeksinden) türetilir —
# narration'a LLM'in kendi sıra ifadesini yazması rozetle senkron olmayabilir
# (gözlemlenen: rozet="1", etiket="ADIM 1", metin="Adım iki: ..."). Numaralandırma
# TAMAMEN bileşenin işi; metinde asla tekrarlanmamalı.
_STEP_ORDINAL_RE = re.compile(
    r"(adım\s+(bir|iki|üç)\b)"
    r"|(\b(birinci|ikinci|üçüncü)\s+(adım|olarak)\b)"
    r"|(\b[123]\.\s*adım\b)",
    re.IGNORECASE,
)


def _find_step_ordinal_leak(scenes: list[dict]) -> list[str]:
    """MotivationStepScene narration/spoken_text'inde sıra ifadesi sızıntısı var mı?"""
    hits = []
    for s in scenes:
        if s.get("component") != "MotivationStepScene":
            continue
        for field in ("narration", "spoken_text"):
            text = s.get(field) or ""
            if _STEP_ORDINAL_RE.search(text):
                hits.append(f"{s.get('id', '?')}.{field}: '{text[:60]}'")
    return hits

# Türkçe kadın sesi için 2.8 kelime/saniye
WORDS_PER_SECOND = 2.8


def word_budget(seconds: int) -> tuple[int, int]:
    lo = int(seconds * WORDS_PER_SECOND * 0.92)
    hi = int(seconds * WORDS_PER_SECOND * 1.08)
    return lo, hi


# SGS/SMMM'e özgü somut motivasyon konuları
_CONTEXT_EXAMPLES = [
    "çalışma programı bozulduğunda geri dönmek",
    "denemelerde düşük netle baş etmek",
    "uzun konu listesi karşısında plan yapmak",
    "son ay tekrar düzeni",
    "her gün soru çözme alışkanlığı",
    "çalışırken dikkat dağılması",
    "ilk kez girenlerin sınav kaygısı",
]

_SYSTEM_PROMPT = """Sen SGS (Staja Giriş Sınavı) ve SMMM adaylarının koçusun.
Adım Müşavir adına Türkçe motivasyon reels içeriği üretiyorsun.

Ton: Sıcak, samimi, destekleyici. Öğretmen değil, yol arkadaşı gibi konuşuyorsun.
Yasak: Yüzeysel klişe ("Pes etme!", "Sen yapabilirsin!"), reklam tonu, robotik okuma.
Her cümle gerçek bir öğrencinin aklından geçiyor olabilir."""

_USER_TEMPLATE = """Konu: {topic}
Hedef süre: {duration} saniye
Kelime bütçesi: {words_lo}–{words_hi} kelime (toplam tüm narration alanları)
Sahne sayısı: {scene_count} sahne, ortalama {avg_sec:.1f} sn/sahne

Aşağıdaki sahne şablonunu AYNEN uygula. Her sahne için:
- component: tam adı (değiştirme)
- title: ekranda büyük gösterilen kısa başlık (max 8 kelime)
- narration: seslendirilecek Türkçe metin (ekran gösterimi için)
- spoken_text: TTS'e gidecek kelime bütçesine uygun metin (narration ile aynı olabilir)
- image_search_query: arka plan fotoğrafı için İngilizce arama terimi

SAHNE ŞABLONU:
1. MotivationHookScene (4–5 sn) — Güçlü ve doğrudan kanca. "Merhaba" ile başlama. İlk 2 cümlede konu netleşsin.
2. MotivationProblemScene (8–12 sn) — Öğrencinin yaşadığı duyguyu/problemi somut tanımla.
3. MotivationEmpathyScene (10–15 sn) — Yalnız olmadığını hissettir. Destekleyici alıntı tarzı.
4. MotivationStepScene (5–7 sn) — Somut, uygulanabilir öneri #1. step_number=1 ekle.
5. MotivationStepScene (5–7 sn) — Farklı somut öneri #2. step_number=2 ekle.
6. MotivationStepScene (5–7 sn) — Farklı somut öneri #3. step_number=3 ekle.
7. MotivationFocusScene (8–10 sn) — Motive edici sonuç ve sınav odağı. Hedef hatırlatma.
8. MotivationOutroScene (5–8 sn) — Kapanış. cta_text: kısa çağrı + kanal yönlendirmesi.

MotivationStepScene KURALI (ÖNEMLİ): Ekrandaki rozet (1/2/3) ve "ADIM N" etiketi
step_number alanından otomatik üretilir — narration/spoken_text içinde SIRA
İFADESİ KULLANMA: "Adım bir/iki/üç", "Birinci/İkinci/Üçüncü adım", "1. adım",
"İkinci olarak" gibi ifadeler YASAK. Metin doğrudan eylemle başlasın.
Yanlış: "İkinci adım: Her gün belirli saatte çalış."
Doğru: "Her gün belirli saatte çalış."

JSON formatı (bu şemayı AYNEN kullan):
{{
  "title": "Video başlığı (max 60 karakter, Türkçe)",
  "description": "Açıklama (max 120 karakter)",
  "hashtags": ["#sgs", "#smmm", "#motivasyon", "#adimmusavir"],
  "total_word_count": <toplam kelime sayısı>,
  "scenes": [
    {{
      "id": "scene_01",
      "component": "MotivationHookScene",
      "title": "Başlık metni",
      "narration": "Seslendirilecek metin. Tam cümle, noktalama ile.",
      "spoken_text": "TTS versiyonu — rakamlar Türkçe yazılı.",
      "image_search_query": "student studying motivation desk"
    }}
  ]
}}

step_number alanını MotivationStepScene sahnelerine ekle (1, 2, 3).
step_title alanını MotivationStepScene sahnelerine ekle (max 6 kelime, adımın özeti).
cta_text alanını MotivationOutroScene sahnesine ekle.
Tüm metinler Türkçe. spoken_text'te kısaltmalar açık yazılsın (KDV→ka de ve)."""


def generate_motivation_storyboard(
    topic: str,
    duration: int = 120,
    platform: str = "reels",
) -> dict:
    words_lo, words_hi = word_budget(duration)
    scene_count = max(8, min(20, math.ceil(duration / 6)))
    avg_sec = duration / scene_count

    user_msg = _USER_TEMPLATE.format(
        topic=topic,
        duration=duration,
        words_lo=words_lo,
        words_hi=words_hi,
        scene_count=scene_count,
        avg_sec=avg_sec,
    )

    result: dict = {}
    scenes: list[dict] = []
    for attempt in (1, 2):
        result = llm_json(
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.82,
            max_tokens=3000,
            caller="motivation_generator",
        )

        scenes = result.get("scenes", [])
        # component alanı yoksa eski tip sahneye fallback
        for i, scene in enumerate(scenes):
            if not scene.get("component"):
                scene["component"] = "MotivationScene"
            if not scene.get("id"):
                scene["id"] = f"scene_{i + 1:02d}"

        leaks = _find_step_ordinal_leak(scenes)
        if not leaks:
            break
        if attempt == 1:
            logger.warning(
                "[motivation] adım sırası ifadesi sızıntısı (deneme %d/2), yeniden isteniyor: %s",
                attempt, leaks,
            )
            user_msg = user_msg + (
                "\n\nŞEMA HATASI — DÜZELT: Aşağıdaki MotivationStepScene metinlerinde "
                "yasak sıra ifadesi var (rozet zaten numaralandırıyor, metinde tekrar "
                "YASAK). Bu sahneleri doğrudan eylemle başlayacak şekilde YENİDEN yaz:\n"
                + "\n".join(leaks)
            )
        else:
            logger.error(
                "[motivation] 2 deneme sonrası hâlâ adım sırası ifadesi sızıntısı var — "
                "devam edildi (video durdurulmadı): %s", leaks,
            )

    logger.info(
        "[motivation] storyboard uretildi: '%s' | %d sahne | kelime: %s",
        result.get("title"),
        len(scenes),
        result.get("total_word_count", "?"),
    )

    result["scenes"] = scenes
    return result
