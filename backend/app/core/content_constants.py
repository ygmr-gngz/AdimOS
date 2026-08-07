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
from app.core.generated_constants import TR_SPS, CHARS_PER_SYLLABLE, VISUAL_SURFACE_MINIMUMS  # noqa: F401

# reels_short sahne pacing — TEK KAYNAK (2026-08-07 öncesi video.py ve
# educational_reel_storyboard.py'de bağımsız olarak "8.0" hardcode edilmişti,
# aynı duplike-sabit hatası tekrar etmesin diye buraya taşındı).
# Ölçüm: 4 ardışık regen turunda model doğal olarak ~26 hece/sahne (~5.9sn,
# TR_SPS=4.42 ile) üretti, sahne sayısını zorlayınca değil. Sahne sayısını
# büyütmek (eski 8.0sn varsayımı) yerine sahne uzunluğunu sabit tutup sahne
# SAYISINI bütçeyle ölçeklemek gerekiyor — bkz. video.py _syllable_budget_params.
NATURAL_SCENE_SECONDS = 5.5


def scene_count_for_budget(budget_seconds: float) -> int:
    """budget_seconds için doğal sahne sayısı — round(budget / NATURAL_SCENE_SECONDS)."""
    return max(1, round(budget_seconds / NATURAL_SCENE_SECONDS))


def budget_params(budget_seconds: float, scene_count: int) -> tuple[int, int, int, int]:
    """
    TEK KAYNAK: hece bütçesi VE karakter sınırı (±%15) aynı çağrıdan gelir.

    Önceki hata: hece bütçesi kapısı (video.py _check_syllable_budget) ve
    karakter sınırı (educational_reel_storyboard.py prompt/deterministik
    kontrol) aynı formülü İKİ AYRI YERDE bağımsız hesaplıyordu — biri
    düzeltilmiş budget_seconds'tan, diğeri farklı bir scene_count/budget
    kombinasyonundan türeyip birbirinden sapabiliyordu (gözlemlenen:
    karakter sınırı 71-96 orijinal 60s'ten, hece bütçesi hedef_hece=315
    düzeltilmiş ~76s'ten — model karaktere tam uysa bile ~247 hece üretip
    315 hedefinin sistematik ~%25 altında kalıyordu). Artık ikisi de bu
    fonksiyonu çağırıyor; aynı (budget_seconds, scene_count) girdisi aynı
    çıktıyı garanti eder.

    Döner: (total_syl, syl_per_scene, min_chars, max_chars)
    """
    total_syl = round(budget_seconds * TR_SPS)
    syl_per_scene = round(total_syl / scene_count) if scene_count else 0
    chars = syl_per_scene * CHARS_PER_SYLLABLE
    return total_syl, syl_per_scene, round(chars * 0.85), round(chars * 1.15)
