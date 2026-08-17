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
import re
from app.core.llm_client import chat_json as llm_json
from app.core.content_constants import scene_count_for_budget, budget_params, TR_SPS, CHARS_PER_SYLLABLE
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


def _voice_text(scene: dict) -> str:
    """Pipeline'ın TTS'e göndereceği tek metni döndürür.

    Yeni motivasyon storyboard'larında kaynak alan ``narration``. ``spoken_text``
    eski kayıtları okuyabilmek için yalnızca geriye dönük yedektir; iki alan asla
    birleştirilmez. video.py'nin ``voice_text = narration or spoken_text``
    sözleşmesiyle birebirdir.
    """
    return (scene.get("voice_text") or scene.get("narration") or scene.get("spoken_text") or "").strip()


def _find_step_ordinal_leak(scenes: list[dict]) -> list[str]:
    """MotivationStepScene'in gerçek TTS metninde sıra ifadesi sızıntısı var mı?"""
    hits = []
    for s in scenes:
        if s.get("component") != "MotivationStepScene":
            continue
        text = _voice_text(s)
        if _STEP_ORDINAL_RE.search(text):
            hits.append(f"{s.get('id', '?')}.voice_text: '{text[:60]}'")
    return hits


def _all_text(scenes: list[dict]) -> str:
    """SGS ve hece kontrolleri için gerçek TTS metinlerinin birleşimi."""
    return " ".join(filter(None, (_voice_text(s) for s in scenes)))


# video.py._syllable_count ile aynı mantık — oradan import edilmiyor çünkü video.py
# zaten bu modülü import ediyor (döngüsel import olurdu). Türkçe ünlü kümesi
# değişmeyeceği için kontrollü, gerekçeli bir tekrar (bkz. parseTurkishAmount
# Python/TS tekrarı, aynı sınıf gerekçe).
_TR_VOWELS = frozenset("aeıioöuüAEIİOÖUÜ")


def _syllable_count(text: str) -> int:
    return sum(1 for ch in text if ch in _TR_VOWELS)


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
{budget_note}
Sahne sayısı: {scene_count} sahne, ortalama {avg_sec:.1f} sn/sahne

Aşağıdaki sahne şablonunu AYNEN uygula. Her sahne için:
- component: tam adı (değiştirme)
- title: ekranda büyük gösterilen kısa başlık (max 8 kelime)
- narration: seslendirilecek Türkçe metin (ekran gösterimi için)
- image_search_query: arka plan fotoğrafı için İngilizce arama terimi

SAHNE ŞABLONU ({scene_count} sahne — akış hook → problem → empati → {step_count} adım → odak → outro):
Hook DIŞINDAKİ her sahne yaklaşık {syl_per_scene} hece içermeli (bkz. HECE BÜTÇESİ) —
sahne türüne göre "kısa/uzun sahne" diye ayrı bir süre varsayma, hepsi eşit ağırlıkta.
1. MotivationHookScene — Güçlü ve doğrudan kanca. "Merhaba" ile başlama. Kasıtlı olarak
   diğer sahnelerden KISA: 8-14 kelime, TEK cümle. Aşağıdaki formül tiplerinden birini kullan:
{hook_formulas}
2. MotivationProblemScene — SGS adayının yaşadığı duyguyu/problemi somut tanımla.
3. MotivationEmpathyScene — Yalnız olmadığını hissettir. Destekleyici alıntı tarzı.
{step_scenes}
{focus_num}. MotivationFocusScene — Motive edici sonuç ve sınav odağı. Hedef hatırlatma.
{outro_num}. MotivationOutroScene — Kapanış.

MotivationStepScene KURALI (ÖNEMLİ): Ekrandaki rozet (1/2/3) ve "ADIM N" etiketi
step_number alanından otomatik üretilir — narration içinde SIRA
İFADESİ KULLANMA: "Adım bir/iki/üç", "Birinci/İkinci/Üçüncü adım", "1. adım",
"İkinci olarak" gibi ifadeler YASAK. Metin doğrudan eylemle başlasın.
Yanlış: "İkinci adım: Her gün belirli saatte çalış."
Doğru: "Her gün belirli saatte çalış."

SGS UNSURU (ZORUNLU): Tüm video boyunca seslendirilecek narration metninde EN AZ
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
      "image_search_query": "student studying motivation desk"
    }}
  ]
}}

step_number alanını MotivationStepScene sahnelerine ekle (1'den {step_count}'e kadar sırayla).
step_title alanını MotivationStepScene sahnelerine ekle (max 6 kelime, adımın özeti).
cta_text alanını MotivationOutroScene sahnesine ekle (yukarıdaki 8 kapanıştan biri, HARFİYEN).
Tüm metinler Türkçe. TTS telaffuz normalizasyonu pipeline'da merkezi olarak uygulanır;
ayrı spoken_text alanı üretme."""


def _build_step_scenes_block(step_count: int) -> str:
    lines = []
    for i in range(1, step_count + 1):
        n = 3 + i   # sahne no: 1 hook, 2 problem, 3 empati, 4..= adımlar
        lines.append(
            f"{n}. MotivationStepScene — Somut, uygulanabilir öneri #{i}. step_number={i} ekle."
        )
    return "\n".join(lines)


def generate_motivation_storyboard(
    topic: str,
    duration: int = 120,
    platform: str = "reels",
    job_id: str = "",
    correction_hint: str | None = None,
) -> dict:
    # 2026-08-08 — iki birleşik bulgu, aynı kök sorunun parçası:
    #
    # 1) Sahne sayısı 8'de SABİTTİ. Süre düzeltme turlarında bütçe büyüdükçe
    #    (ölçülen 32.2s → sönümlü hedef 80.7s) hece hedefi de büyüyordu ama
    #    sahne sayısı sabit kalınca sahne başına hedef modelin doğal sınırının
    #    çok üzerine çıktı — model 3 turda da hep başarısız oldu (undershoot).
    #    reels'te aynı sınıf hata scene_count_for_budget (NATURAL_SCENE_SECONDS)
    #    ile çözülmüştü; aynı mekanizma burada da uygulanıyor. Sabit 5 sahne
    #    (hook/problem/empati/odak/outro) + bütçeyle büyüyen sayıda
    #    MotivationStepScene — akış yapısı korunuyor, yalnızca adım sayısı
    #    değişiyor (MotivationStepScene zaten çoğaltılabilir bir bileşen).
    #
    # 2) Sahne sayısı düzeltildikten SONRA da ikinci, bağımsız bir uyumsuzluk
    #    ortaya çıktı: bu dosyanın kendi WORDS_PER_SECOND=2.8 (kelime bazlı)
    #    bütçesi, reels'te bu oturumda ölçülüp kalibre edilen TR_SPS=4.42
    #    (hece bazlı) ile çelişiyordu — ima ettiği hız ~7.56 hece/sn, gerçek
    #    ölçülenin (4.42) neredeyse iki katı. Sonuç: model kendi word_budget
    #    hedefini tam tutturuyordu (233/208-244 kelime) ama bu içerik reels'in
    #    kullandığı GENEL hece kapısına göre %75 FAZLAYDI (628/358 hece) —
    #    aynı iki-farklı-kaynak sınıfı hata (beş süre tablosu, iki registry
    #    postmortemleriyle aynı desen). Kelime birimi zaten Türkçe için yanlış
    #    ölçüydü ("ev"=1 hece, "değerlendirilebileceği"=9 hece). WORDS_PER_SECOND/
    #    word_budget tamamen kaldırıldı, motivasyon da reels'in kullandığı AYNI
    #    budget_params()/TR_SPS hece sistemini kullanıyor artık.
    # step_count'un alt sınırı scene_count_for_budget'ın hesapladığından daha
    # büyük bir toplam sahne sayısı zorlayabilir (kısa bütçelerde — örn. 45s/8.5=5,
    # ama 5 sabit sahne + min adım ≥ taban). scene_count bu noktadan SONRA gerçek
    # toplama göre YENİDEN hesaplanmalı — aksi halde hece bütçesi (ve promptun
    # kendisi) yanlış sahne sayısına göre kurulur (2026-08-08, 1. bulgu).
    #
    # 2026-08-08, 2. bulgu — "ölü bölge": taban=2 iken 45-62 saniye ARALIĞININ
    # TAMAMI aynı toplama (7) yuvarlanıyordu (45/8.5≈5→tabanla 7; 57.7/8.5≈7→zaten
    # 7) — süre düzeltme turunun TEK kaldıracı (sahne sayısı) bu ~17sn'lik aralıkta
    # tamamen işlevsizdi (ölçülen canlı arıza: 45→57.7 düzeltmesinde hedef_hece
    # 266'da sabit kaldı, model %56/%45 altında kaldı). Kontrollü deney (sabit 7
    # sahne, sahne-başı hedefi 38→50→65 arası değiştirerek): gerçek çıktı
    # 35.6→36.0→44.1 — SAPTANMIŞ ORANTISIZ tepki (hedef %71 arttı, çıktı %24
    # arttı) — modelin ~35-44 hece/sahne civarında doğal bir tavanı var, hedefi
    # yükseltmek güvenilir bir çözüm değil. Taban 2→1 indirilince doğal yuvarlama
    # aralıkları normale döndü (her biri ~8.5sn genişliğinde, taban tarafından
    # yapay olarak genişletilmiyor) — 45→57.7 artık 6→7 sahneye karşılık geliyor,
    # kaldıraç tekrar çalışıyor.
    step_count = max(1, scene_count_for_budget(duration, "motivasyon") - 5)
    scene_count = step_count + 5
    avg_sec = duration / scene_count

    total_syl, syl_per_scene, min_chars, max_chars = budget_params(duration, scene_count, "motivasyon")
    tolerance = max(3, round(syl_per_scene * 0.15))
    target_chars = round(syl_per_scene * CHARS_PER_SYLLABLE)
    budget_note = (
        f"HECE BÜTÇESİ (ZORUNLU): Toplam {total_syl} hece "
        f"({duration:.0f}s × {TR_SPS:.2f} hece/s, {scene_count} sahne).\n"
        f"Her sahnenin narration metninde yaklaşık {syl_per_scene} hece kullan "
        f"(±{tolerance} tolerans, yani {syl_per_scene - tolerance}–{syl_per_scene + tolerance} arası).\n"
        f"Türkçede hece = metindeki ünlü harf sayısı (a,e,ı,i,o,ö,u,ü).\n"
        f"KARAKTER UZUNLUĞU: Her sahne metni YAKLAŞIK {target_chars} karakter olmalı "
        f"(boşluklar dahil, {min_chars}-{max_chars} arası kabul edilir ama HEDEF {target_chars})."
    )

    user_msg = _USER_TEMPLATE.format(
        topic=topic,
        duration=duration,
        budget_note=budget_note,
        scene_count=scene_count,
        syl_per_scene=syl_per_scene,
        step_count=step_count,
        step_scenes=_build_step_scenes_block(step_count),
        focus_num=step_count + 4,
        outro_num=step_count + 5,
        avg_sec=avg_sec,
        hook_formulas=_HOOK_FORMULAS_BLOCK,
        sgs_terms=_SGS_TERMS_BLOCK,
        generic_phrases=_GENERIC_PHRASES_BLOCK,
        closing_bank=_CLOSING_BANK_BLOCK,
    )
    if correction_hint:
        # Süre düzeltme turundan gelen geri bildirim (video.py _check_syllable_budget) —
        # ÖNCEDEN buraya hiç ulaşmıyordu: _generate_storyboard_for_regen motivasyon
        # dalı correction_hint'i alıyordu ama generate_motivation_storyboard'a hiç
        # geçirmiyordu, retry turları kör tekrar üretim yapıyordu (aynı sapma
        # tekrarlanıyordu: tur1 %-51, tur2 %-58 — düzelmiyor, rastgele dalgalanıyordu).
        user_msg += f"\n\nÖNEMLİ DÜZELTME (önceki üretimden): {correction_hint}"

    logger.info(
        "[motivation-prompt] job=%s duration=%ss hedef_sahne=%d adim_sahnesi=%d "
        "hedef_hece=%d sahne_basi_hece=%d correction_hint=%s prompt_uzunluk=%d",
        job_id[:8] if job_id else "-", duration, scene_count, step_count,
        total_syl, syl_per_scene, bool(correction_hint), len(user_msg),
    )
    # 2026-08-08: DEBUG seviyesi canlıda muhtemelen kapalı — tam metin hiç loglanmıyordu.
    # INFO'ya çekildi ama şişmesin diye 3 parçaya ayrıldı: (1) HECE BÜTÇESİ bölümü ve
    # (2) correction_hint HER ZAMAN TAM logланır (kesilmez — kritik olan tam olarak bunlar,
    # sırayla/çelişerek mi gidiyorlar görmek için), (3) promptun geri kalanından yalnızca
    # ilk 1500 karakterlik önizleme.
    logger.info("[motivation-prompt] hece_butcesi_bolumu:\n%s", budget_note)
    if correction_hint:
        logger.info("[motivation-prompt] correction_hint_tam:\n%s", correction_hint)
    logger.info("[motivation-prompt] onizleme_ilk_1500:\n%s", user_msg[:1500])

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
            # 2026-08-08: 0.82 → 0.5. Doğallık kelime seçiminden değil içerik
            # bankasından geliyor (SGS bağlamı, somut adım, gerçek duygu) —
            # yüksek sıcaklık burada doğallık değil uzunluk kumarı üretiyordu
            # (aynı 60s hedefte 3 denemede sapma +45%/+54%/+65% ölçüldü).
            temperature=0.5,
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

        # 2026-08-09 — kullanıcı hipotezi: sgs-content düzeltme turu (aşağıda,
        # SGS unsuru/cta için modele geri besleme) metni kısaltıyor olabilir,
        # ve bu kısalmış metin SONRA (bu fonksiyonun dışında, video.py
        # _check_syllable_budget'ta) hece bütçesine göre ölçülüyor — iki
        # zincir birbirinden habersiz. Bunu doğrudan ölçmek için her deneme
        # sonunda hece sayısı loglanıyor — deneme 1→2 arası düşüş varsa
        # (SGS/cta düzeltmesi TAM OLARAK bunu yapıyorsa) burada görünür.
        _attempt_syl = _syllable_count(full_text)
        logger.info(
            "[motivation-attempt] job=%s deneme=%d/2 hece=%d hedef_hece=%d sgs_sayisi=%d cta_ok=%s",
            job_id[:8] if job_id else "-", attempt, _attempt_syl, total_syl, len(sgs_elements), cta_ok,
        )

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
