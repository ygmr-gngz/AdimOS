"""
shared/content-types.json'daki "constants" bölümünü okur.

Dil/hece bütçesi sabitleri (TR_SPS, CHARS_PER_SYLLABLE) burada tek kaynaktan
gelir — video.py ve educational_reel_storyboard.py'de ayrı ayrı hardcode
edilmiş, birbirinden bağımsız sürüklenebilen kopyalar yerine.
"""
import json
from functools import lru_cache
from pathlib import Path

_SHARED_JSON = Path(__file__).resolve().parents[3] / "shared" / "content-types.json"


@lru_cache(maxsize=1)
def _load_constants() -> dict:
    with open(_SHARED_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("constants", {})


def get_constant(name: str, default: float) -> float:
    """shared/content-types.json → constants[name]; yoksa default (loglanmaz — çağıran karar verir)."""
    return float(_load_constants().get(name, default))


TR_SPS: float = get_constant("TR_SPS", 4.8)
CHARS_PER_SYLLABLE: float = get_constant("CHARS_PER_SYLLABLE", 2.7)
