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
from app.core.generated_constants import TR_SPS, CHARS_PER_SYLLABLE  # noqa: F401
