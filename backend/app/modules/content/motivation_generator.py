"""
SGS/SMMM adayları için 120 saniye motivasyon video storyboard üreticisi.
Çıktı: component alanı dahil tam storyboard JSON.
"""
import logging
import math
from app.core.llm_client import chat_json as llm_json

logger = logging.getLogger(__name__)

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
- duration_seconds: önerilen sahne süresi (gerçek ses süresi + 0.5 sn)
- image_search_query: arka plan fotoğrafı için İngilizce arama terimi

SAHNE ŞABLONU:
1. MotivationHookScene (4–5 sn) — Güçlü ve doğrudan kanca. "Merhaba" ile başlama. İlk 2 cümlede konu netleşsin.
2. MotivationProblemScene (8–12 sn) — Öğrencinin yaşadığı duyguyu/problemi somut tanımla.
3. MotivationEmpathyScene (10–15 sn) — Yalnız olmadığını hissettir. Destekleyici alıntı tarzı.
4. MotivationStepScene (5–7 sn) — Adım 1: somut, uygulanabilir öneri. step_number=1 ekle.
5. MotivationStepScene (5–7 sn) — Adım 2: farklı somut öneri. step_number=2 ekle.
6. MotivationStepScene (5–7 sn) — Adım 3: farklı somut öneri. step_number=3 ekle.
7. MotivationFocusScene (8–10 sn) — Motive edici sonuç ve sınav odağı. Hedef hatırlatma.
8. MotivationOutroScene (5–8 sn) — Kapanış. cta_text: kısa çağrı + kanal yönlendirmesi.

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
      "duration_seconds": 5,
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

    result = llm_json(
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _USER_TEMPLATE.format(
                topic=topic,
                duration=duration,
                words_lo=words_lo,
                words_hi=words_hi,
                scene_count=scene_count,
                avg_sec=avg_sec,
            )},
        ],
        temperature=0.82,
        max_tokens=3000,
        caller="motivation_generator",
    )

    scenes = result.get("scenes", [])
    logger.info(
        "[motivation] storyboard uretildi: '%s' | %d sahne | kelime: %s",
        result.get("title"),
        len(scenes),
        result.get("total_word_count", "?"),
    )

    # component alanı yoksa eski tip sahneye fallback
    for i, scene in enumerate(scenes):
        if not scene.get("component"):
            scene["component"] = "MotivationScene"
        if not scene.get("id"):
            scene["id"] = f"scene_{i + 1:02d}"

    result["scenes"] = scenes
    return result
