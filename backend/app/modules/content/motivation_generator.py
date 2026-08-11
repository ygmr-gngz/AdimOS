"""
SGS/SMMM adayları için 120 saniye motivasyon video storyboard üreticisi.
Çıktı: component alanı dahil tam storyboard JSON.

B (SGS İçerik Bankası) — 2026-08-08: jenerik motivasyon metinleri ("Yalnız
değilsin", "Birçok öğrenci benzer sıkıntılar yaşıyor") herhangi bir sınav
videosu olabilirdi, SGS'ye özgü hiçbir şey yoktu (B.0). Bu dosya artık:
  - hedef kitleyi "SGS adayı" olarak zorunlu kılar (B.1)
  - her videoda >=2 somut SGS unsuru (ders/sınav gerçeği/zaman) ister (B.1)
  - jenerik ifadeleri yasaklar (B.1)
  - kapanışı sabit onaylı bankadan seçtirir, LLM uydurmaz (B.3)
  - kanca formüllerini SGS bağlamıyla yönlendirir (B.4)
  - adım sırası sızıntısını engeller (B.5 — önceden buradaydı, korunuyor)
"""
import logging
import math
import re
from app.core.llm_client import chat_json as llm_json
from app.core.content_bank_motivation import (
    CLOSING_BANK,
    HOOK_FORMULAS,
    SGS_COURSE_NAMES,
    SGS_EXAM_FACTS,
    SGS_TIME_PHRASES,
    GENERIC_BANNED_PHRASES,
)

logger = logging.getLogger(__name__)

# MotivationStepScene rozeti/etiketi step_number'dan (sahne indeksinden) türetilir —
# narration'a LLM'in kendi sıra ifadesini yazması rozetle senkron olmayabilir
# (gözlemlenen: rozet="1", etiket="ADIM 1", metin="Adım iki: ..."). Numaralandırma
# TAMAMEN bileşenin işi; metinde asla tekrarlanmamalı. (B.5)
_STEP_ORDINAL_RE = re.compile(
    r"(adım\s+(bir|iki|üç)\b)"
    r"|(\b(birinci|ikinci|üçüncü)\s+(adım|olarak)\b)"
    r"|(\b[123]\.\s*adım\b)",
    re.IGNORECASE,
)

# B.1 — "sınava X gün kala" biçimindeki zaman ifadesi sabit listeye girmez, regex gerekir.
_TIME_KALA_RE = re.compile(r"sınava\s+\d+\s+gün\s+kala", re.IGNORECASE)


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


def _all_text(scenes: list[dict]) -> str:
    parts = []
    for s in scenes:
        parts.append(s.get("narration") or "")
        parts.append(s.get("spoken_text") or "")
    return " ".join(parts)


def _find_sgs_elements(full_text: str) -> set[str]:
    """Metinde geçen benzersiz SGS unsurlarını döndürür (B.1: >= 2 zorunlu)."""
    lower = full_text.lower()
    found = {
        term for term in (*SGS_COURSE_NAMES, *SGS_EXAM_FACTS, *SGS_TIME_PHRASES)
        if term in lower
    }
    if _TIME_KALA_RE.search(lower):
        found.add("sınava X gün kala")
    return found


def _find_generic_phrases(full_text: str, sgs_elements: set[str]) -> list[str]:
    """B.1: yasak jenerik ifadeler. 'başarabilirsin' YALNIZCA somut bir SGS
    unsuruyla birlikte kullanılmadıysa ihlal sayılır (kural: 'tek başına yetmez')."""
    lower = full_text.lower()
    hits = []
    for phrase in GENERIC_BANNED_PHRASES:
        if phrase not in lower:
            continue
        if phrase == "başarabilirsin" and sgs_elements:
            continue
        hits.append(phrase)
    return hits


def _find_outro_scene(scenes: list[dict]) -> dict | None:
    for s in scenes:
        if s.get("component") == "MotivationOutroScene":
            return s
    return None


# Türkçe kadın sesi için 2.8 kelime/saniye
WORDS_PER_SECOND = 2.8


def word_budget(seconds: int) -> tuple[int, int]:
    lo = int(seconds * WORDS_PER_SECOND * 0.92)
    hi = int(seconds * WORDS_PER_SECOND * 1.08)
    return lo, hi


_SYSTEM_PROMPT = """Sen SGS (Staja Giriş Sınavı) ve SMMM adaylarının koçusun.
Adım Müşavir adına Türkçe motivasyon reels içeriği üretiyorsun.

Ton: Sıcak, samimi, destekleyici. Öğretmen değil, yol arkadaşı gibi konuşuyorsun.
Yasak: Yüzeysel klişe ("Pes etme!", "Sen yapabilirsin!"), reklam tonu, robotik okuma.
Her cümle gerçek bir SGS adayının aklından geçiyor olabilir.

HEDEF KİTLE (ZORUNLU): "öğrenci" DEĞİL — "SGS adayı" / "staja giriş sınavına
hazırlanan" de. Bu sınav genel bir sınav değil, SGS'dir; öyle davran."""

_GENERIC_PHRASES_BLOCK = "\n".join(
    f'  "{bad}" YASAK → {good}' for bad, good in GENERIC_BANNED_PHRASES.items()
)
_HOOK_FORMULAS_BLOCK = "\n".join(
    f"  {h['type']}: \"{h['example']}\"" for h in HOOK_FORMULAS
)
_CLOSING_BANK_BLOCK = "\n".join(
    f"  {i + 1}. \"{c}\"" for i, c in enumerate(CLOSING_BANK)
)
_SGS_TERMS_BLOCK = (
    "  ders adları: " + ", ".join(SGS_COURSE_NAMES) + "\n"
    "  sınav gerçeği: " + ", ".join(SGS_EXAM_FACTS) + "\n"
    "  zaman: " + ", ".join(SGS_TIME_PHRASES) + ", sınava X gün kala"
)

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
1. MotivationHookScene (4–5 sn) — Güçlü ve doğrudan kanca. "Merhaba" ile başlama.
   İlk 5 saniye, 8-14 kelime, TEK cümle. Aşağıdaki formül tiplerinden birini kullan:
{hook_formulas}
2. MotivationProblemScene (8–12 sn) — SGS adayının yaşadığı duyguyu/problemi somut tanımla.
3. MotivationEmpathyScene (10–15 sn) — Yalnız olmadığını hissettir. Destekleyici alıntı tarzı.
4. MotivationStepScene (5–7 sn) — Somut, uygulanabilir öneri #1. step_number=1 ekle.
5. MotivationStepScene (5–7 sn) — Farklı somut öneri #2. step_number=2 ekle.
6. MotivationStepScene (5–7 sn) — Farklı somut öneri #3. step_number=3 ekle.
7. MotivationFocusScene (8–10 sn) — Motive edici sonuç ve sınav odağı. Hedef hatırlatma.
8. MotivationOutroScene (5–8 sn) — Kapanış.

MotivationStepScene KURALI (ÖNEMLİ): Ekrandaki rozet (1/2/3) ve "ADIM N" etiketi
step_number alanından otomatik üretilir — narration/spoken_text içinde SIRA
İFADESİ KULLANMA: "Adım bir/iki/üç", "Birinci/İkinci/Üçüncü adım", "1. adım",
"İkinci olarak" gibi ifadeler YASAK. Metin doğrudan eylemle başlasın.
Yanlış: "İkinci adım: Her gün belirli saatte çalış."
Doğru: "Her gün belirli saatte çalış."

SGS UNSURU (ZORUNLU): Tüm video boyunca (narration/spoken_text toplamında) EN AZ
İKİ farklı somut SGS unsuru geçmeli. Aşağıdaki listeden seç, uydurma:
{sgs_terms}

YASAK JENERİK İFADELER (somut karşılığını kullan):
{generic_phrases}

KAPANIŞ (cta_text, ZORUNLU — MotivationOutroScene'e ekle): Aşağıdaki 8 kapanıştan
BİRİNİ HARFİYEN (değiştirmeden, kısaltmadan) seç ve cta_text alanına AYNEN yaz.
Kendi kapanışını UYDURMA:
{closing_bank}

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
cta_text alanını MotivationOutroScene sahnesine ekle (yukarıdaki 8 kapanıştan biri, HARFİYEN).
Tüm metinler Türkçe. spoken_text'te kısaltmalar açık yazılsın (KDV→ka de ve)."""


def generate_motivation_storyboard(
    topic: str,
    duration: int = 120,
    platform: str = "reels",
    job_id: str = "",
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
        hook_formulas=_HOOK_FORMULAS_BLOCK,
        sgs_terms=_SGS_TERMS_BLOCK,
        generic_phrases=_GENERIC_PHRASES_BLOCK,
        closing_bank=_CLOSING_BANK_BLOCK,
    )

    result: dict = {}
    scenes: list[dict] = []
    sgs_elements: set[str] = set()
    generic_hits: list[str] = []
    ordinal_leaks: list[str] = []
    cta_ok = False

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

        full_text = _all_text(scenes)
        sgs_elements = _find_sgs_elements(full_text)
        generic_hits = _find_generic_phrases(full_text, sgs_elements)
        ordinal_leaks = _find_step_ordinal_leak(scenes)
        outro = _find_outro_scene(scenes)
        cta_text = (outro or {}).get("cta_text") or ""
        cta_ok = cta_text.strip() in CLOSING_BANK

        problems: list[str] = []
        if len(sgs_elements) < 2:
            problems.append(
                f"SGS unsuru yetersiz ({len(sgs_elements)}/2) — bulunanlar: {sorted(sgs_elements)}. "
                f"Listeden en az 2 farklı somut unsur kullan."
            )
        if generic_hits:
            problems.append(f"Yasak jenerik ifade(ler): {generic_hits}. Somut karşılığını kullan.")
        if ordinal_leaks:
            problems.append(f"MotivationStepScene'de sıra ifadesi sızıntısı: {ordinal_leaks}.")
        if not cta_ok:
            problems.append(
                f"cta_text bankadan değil (üretilen: {cta_text!r}). "
                f"MotivationOutroScene.cta_text'i yukarıdaki 8 kapanıştan biriyle HARFİYEN değiştir."
            )

        if not problems:
            break
        if attempt == 1:
            logger.warning("[sgs-content] deneme=1/2 sorunlar: %s", problems)
            user_msg = user_msg + "\n\nŞEMA HATASI — DÜZELT:\n" + "\n".join(problems)
        else:
            logger.warning("[sgs-content] deneme=2/2 sonrası hâlâ sorunlu: %s", problems)

    # cta_text 2 denemede de bankadan gelmediyse deterministik düzeltme —
    # sessiz bırakılmıyor (loglanıyor), ama pazarlama uyumu (TÜRMOB) riski
    # taşıyan bir alanı uydurulmuş haliyle bırakmak "sessiz fallback"tan
    # daha kötü olurdu.
    outro = _find_outro_scene(scenes)
    if outro is not None and not cta_ok:
        forced = CLOSING_BANK[hash(topic) % len(CLOSING_BANK)]
        logger.warning(
            "[sgs-content] cta_text bankadan gelmedi, zorla düzeltildi: %r → %r",
            outro.get("cta_text"), forced,
        )
        outro["cta_text"] = forced
        cta_ok = True

    cta_bank_index = None
    if outro is not None:
        try:
            cta_bank_index = CLOSING_BANK.index(outro.get("cta_text", "")) + 1
        except ValueError:
            cta_bank_index = None

    sonuc = "GEÇTİ" if (len(sgs_elements) >= 2 and not generic_hits and not ordinal_leaks and cta_ok) else "KALDI"
    logger.info(
        "[sgs-content] job=%s sgs_unsuru=%d jenerik_ifade=%d sira_sizinti=%d cta=banka#%s %s",
        job_id[:8] if job_id else "-", len(sgs_elements), len(generic_hits), len(ordinal_leaks),
        cta_bank_index if cta_bank_index else "YOK", sonuc,
    )

    logger.info(
        "[motivation] storyboard uretildi: '%s' | %d sahne | kelime: %s",
        result.get("title"),
        len(scenes),
        result.get("total_word_count", "?"),
    )

    result["scenes"] = scenes
    return result
