"""
Türkçe TTS normalizasyonu — muhasebe/SGS içeriği için.

tr_speech_normalize(text) → spoken_text (TTS girdisi)
  - Hesap kodları: 153 → "yüz elli üç,"
  - Para: 1.250,50 TL → "bin iki yüz elli lira elli kuruş"
  - Kısaltmalar: KDV → "ka de ve"
  - plain_text değişmez; bu fonksiyon sadece spoken_text üretir.

Sıra önemlidir — daha önce gelen kural sonraki kuralı etkiler.
"""
import re
import unicodedata

try:
    from num2words import num2words as _num2words
    _HAS_NUM2WORDS = True
except ImportError:
    _HAS_NUM2WORDS = False


# ── Muhasebe kısaltmaları ─────────────────────────────────────

_ABBR: list[tuple[str, str]] = [
    (r"\bKDV\b",   "ka de ve"),
    (r"\bÖTV\b",   "ö te ve"),
    (r"\bVUK\b",   "vergi usul kanunu"),
    (r"\bTTK\b",   "türk ticaret kanunu"),
    (r"\bGVK\b",   "ge ve ka"),
    (r"\bKVK\b",   "ke ve ka"),
    (r"\bSMMM\b",  "es em em em"),
    (r"\bYMM\b",   "ye em em"),
    (r"\bSGK\b",   "es ge ka"),
    (r"\bSSK\b",   "es es ka"),
    (r"\bSGS\b",   "es ge es"),
    (r"\bBAĞ-KUR\b", "bağ kur"),
    (r"\bTMS\b",   "te em es"),
    (r"\bTFRS\b",  "te fe re es"),
    (r"\bUMS\b",   "u em es"),
    (r"\bIFRS\b",  "ı fe re es"),
    (r"\bSMBK\b",  "es em be ka"),
    (r"\bBSMV\b",  "be es em ve"),
    (r"\bA\.Ş\.\b", "anonim şirket"),
    (r"\bLtd\.\b",  "limited"),
    (r"\bvb\.\b",   "ve benzeri"),
    (r"\bvs\.\b",   "vesaire"),
]

_ABBR_COMPILED = [(re.compile(p, re.IGNORECASE), r) for p, r in _ABBR]


# ── Para birimi ───────────────────────────────────────────────

_TL_RE = re.compile(
    r"(\d{1,3}(?:\.\d{3})*),(\d{2})\s*(?:TL|₺)",
    re.IGNORECASE,
)
_TL_SIMPLE = re.compile(r"(\d+(?:\.\d{3})*)\s*(?:TL|₺)", re.IGNORECASE)
_PERCENT_RE = re.compile(r"%\s*(\d+(?:[,.]\d+)?)")


def _int_tr(n: int) -> str:
    if _HAS_NUM2WORDS:
        try:
            return _num2words(n, lang="tr")
        except Exception:
            pass
    return str(n)


def _money_replace(m: re.Match) -> str:
    lira_str = m.group(1).replace(".", "")
    kurus_str = m.group(2)
    lira = int(lira_str)
    kurus = int(kurus_str)
    result = f"{_int_tr(lira)} lira"
    if kurus > 0:
        result += f" {_int_tr(kurus)} kuruş"
    return result


def _money_simple_replace(m: re.Match) -> str:
    val_str = m.group(1).replace(".", "")
    return f"{_int_tr(int(val_str))} lira"


def _percent_replace(m: re.Match) -> str:
    return f"yüzde {m.group(1).replace(',', '.').rstrip('0').rstrip('.')}"


# ── Hesap kodu ────────────────────────────────────────────────
# "153 Ticari Mallar" → "yüz elli üç, ticari mallar"
_ACCT_RE = re.compile(r"\b([1-7]\d{2})\b\s+([A-ZÇĞİÖŞÜa-zçğışöşü])")


def _acct_replace(m: re.Match) -> str:
    code = int(m.group(1))
    rest = m.group(2)
    return f"{_int_tr(code)}, {rest}"


# ── Yüzde işareti (pronunciation_dict ile çakışmayı önlemek için pozitif lookbehind) ─
_PCT2_RE = re.compile(r"(?<!\w)%(\d)")


def _pct2_replace(m: re.Match) -> str:
    return f"yüzde {m.group(1)}"


def tr_speech_normalize(text: str) -> str:
    """
    TTS girdisi için Türkçe metin normalizasyonu.
    plain_text'i DEĞİŞTİRMEZ — sadece spoken_text üretimi için çağrılır.
    """
    if not text:
        return text

    # NFC normalizasyon
    text = unicodedata.normalize("NFC", text)

    # Para birimi (önce lira+kuruş, sonra sadece lira)
    text = _TL_RE.sub(_money_replace, text)
    text = _TL_SIMPLE.sub(_money_simple_replace, text)

    # Yüzde
    text = _PERCENT_RE.sub(_percent_replace, text)
    text = _PCT2_RE.sub(_pct2_replace, text)

    # Hesap kodları (3 haneli + harf)
    text = _ACCT_RE.sub(_acct_replace, text)

    # Kısaltmalar
    for pattern, replacement in _ABBR_COMPILED:
        text = pattern.sub(replacement, text)

    # Çok boşluk temizle
    text = re.sub(r" {2,}", " ", text).strip()

    return text
