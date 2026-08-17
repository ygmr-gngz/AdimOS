"""
Dil/hece bütçesi sabitleri (TR_SPS, CHARS_PER_SYLLABLE) — tek kaynak
shared/content-types.json'dur.

ÖNEMLİ: Bu modül shared/content-types.json'ı RUNTIME'DA OKUMAZ. Railway'de
backend'in Docker build context'i backend/ (Root Directory) — shared/
imajda yok, runtime'da açmaya çalışmak import-time crash'e yol açar (canlıda
yaşandı, bkz. postmortem). Bunun yerine backend/app/core/generated_constants.py
(git'e commitli, backend/scripts/generate_content_constants.py ile üretilir)
import edilir — remotion/src/generated/content-types.ts ile aynı desen.

shared/content-types.json değiştiğinde:
  python backend/scripts/generate_content_constants.py
  (CI'da doğrulama: --check bayrağıyla)
"""
from app.core.generated_constants import (  # noqa: F401
    TR_SPS, CHARS_PER_SYLLABLE, VISUAL_SURFACE_MINIMUMS, TYPE_DURATIONS, NATURAL_SCENE_SECONDS,
)

# Sahne pacing — TEK KAYNAK, TÜR BAZLI (2026-08-08). content-types.json'daki
# NATURAL_SCENE_SECONDS[content_type]'tan gelir; kod içinde tür bazlı if YAZILMAZ.
#
# 2026-08-07 postmortem: reels_short/educational_reel_storyboard.py'de bağımsız
# olarak "8.0" hardcode edilmişti (duplike sabit) — TEK bir global sabite taşındı.
# 2026-08-08 postmortem: o TEK global sabit (5.5, yalnızca reels için ölçülmüştü)
# motivasyona da ÖDÜNÇ verildi, hiç doğrulanmadan — ölçünce motivasyon sahnesinin
# doğal uzunluğunun (~4.0sn) reels karttan (~5.5sn) yapısal olarak farklı olduğu
# görüldü (kart görselle anlatır, motivasyon sahnesi duyguyu+bağlamı+adımı yalnızca
# sözle taşır). Artık her content_type kendi ölçülen değerini kullanıyor.


def scene_count_for_budget(budget_seconds: float, content_type: str) -> int:
    """
    budget_seconds için doğal sahne sayısı — round(budget / NATURAL_SCENE_SECONDS[content_type]).
    content_type ZORUNLU (varsayılan/sessiz fallback yok) — NATURAL_SCENE_SECONDS'ta
    tanımlı olmayan bir tür geçilirse KeyError ile açıkça patlar.
    """
    return max(1, round(budget_seconds / NATURAL_SCENE_SECONDS[content_type]))


def budget_params(budget_seconds: float, scene_count: int, content_type: str) -> tuple[int, int, int, int]:
    """
    TEK KAYNAK: hece bütçesi VE karakter sınırı (±%15) aynı çağrıdan gelir.

    Önceki hata (2026-08-07): hece bütçesi kapısı (video.py _check_syllable_budget)
    ve karakter sınırı (educational_reel_storyboard.py prompt/deterministik
    kontrol) aynı formülü İKİ AYRI YERDE bağımsız hesaplıyordu. Artık ikisi de
    bu fonksiyonu çağırıyor; aynı girdi aynı çıktıyı garanti eder.

    İkinci hata (2026-08-08): syl_per_scene ÖNCEDEN total_syl/scene_count olarak
    türetiliyordu (total_syl = budget_seconds*TR_SPS, scene_count'tan bağımsız).
    Bu, scene_count HER ZAMAN scene_count_for_budget(budget_seconds, content_type)
    ile aynıyken doğru sonuç veriyordu — ama motivasyonda min adım sayısı (2)
    scene_count'u bazen bu "doğal" değerin ÜZERİNE zorluyor (kısa bütçelerde sabit
    min 2 adım=7). O durumda AYNI total_syl'i daha büyük bir scene_count'a bölmek
    sahne başı hedefi yapay olarak düşürüyordu (28 hesaplandı, model tutarlı
    biçimde 37-39 üretti — 3 turda da aynı yönde, %32/%39/%38 sapma; rastgele
    değil, formül hatasıydı). Şimdi TERSİ: syl_per_scene DOĞRUDAN ölçülen
    NATURAL_SCENE_SECONDS[content_type] × TR_SPS'ten geliyor (birincil, ölçülen
    değer), total_syl bundan TÜRETİLİYOR (syl_per_scene × scene_count) — scene_count
    "doğal" değerinden sapsa bile sahne başı hedef her zaman ölçülenle tutarlı kalır.

    Döner: (total_syl, syl_per_scene, min_chars, max_chars)
    """
    syl_per_scene = round(NATURAL_SCENE_SECONDS[content_type] * TR_SPS)
    total_syl = syl_per_scene * scene_count
    chars = syl_per_scene * CHARS_PER_SYLLABLE
    return total_syl, syl_per_scene, round(chars * 0.85), round(chars * 1.15)
