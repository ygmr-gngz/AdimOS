"""
Unicode dogrulama - bozuk karakter, mojibake, encoding hatasi tespiti.
Bu karakterlerden biri herhangi bir metin alaninda varsa render durur.
"""
import unicodedata
import re

# Turkce karakterlerin Latin-1 ile yanlis decode edilmesi durumu (mojibake)
# Her pattern: (yanlis_bytes_utf8_gorunumu, aciklama)
_MOJIBAKE_SEQUENCES = [
    "Ä±",   # i -> Ai (Latin-1 bozulmasi)
    "Å",   # s -> As
    "Ã§",   # c -> Ac
    "Ã¼",   # u -> Au
    "Ã¶",   # o -> Ao
    "Ä",   # g -> Ag
    "Ã",   # C -> AC
    "Ã",   # U -> AU
    "Ä°",   # I -> AI
]

_REPLACEMENT_CHAR = "�"  # U+FFFD replacement character
_EMPTY_BOX_CHAR   = "□"  # U+25A1 white square

_MOJIBAKE_RE = re.compile("|".join(re.escape(s) for s in _MOJIBAKE_SEQUENCES))


def validate_unicode(text: str, field_name: str = "text") -> list[str]:
    """
    Metin alaninda bozuk karakter var mi kontrol eder.
    Returns: hata mesajlari listesi - bossa OK.
    """
    errors = []

    if _REPLACEMENT_CHAR in text:
        errors.append(f"{field_name}: U+FFFD degistirme karakteri iceriyor")

    if _EMPTY_BOX_CHAR in text:
        errors.append(f"{field_name}: U+25A1 bos kare karakteri iceriyor (encoding bozuklugu?)")

    if _MOJIBAKE_RE.search(text):
        sample = _MOJIBAKE_RE.search(text).group()
        errors.append(
            f"{field_name}: mojibake tespit edildi ('{sample}') — UTF-8 decode hatasi"
        )

    return errors


def validate_storyboard_unicode(storyboard: dict) -> list[str]:
    """
    Tum sahne metin alanlarinda unicode dogrulama yapar.
    Returns: hata mesajlari listesi.
    """
    errors = []
    text_fields = [
        "voice_text", "narration", "spoken_text", "title", "subtitle",
        "message", "hook_text", "cta_text", "exam_tip", "common_mistake",
        "definition", "key_point", "explanation",
    ]

    for i, scene in enumerate(storyboard.get("scenes", [])):
        sid = scene.get("id", i + 1)
        for field in text_fields:
            val = scene.get(field)
            if isinstance(val, str):
                errs = validate_unicode(val, f"scene[{sid}].{field}")
                errors.extend(errs)
        for bp in scene.get("bullet_points", []):
            if isinstance(bp, str):
                errors.extend(validate_unicode(bp, f"scene[{sid}].bullet_points"))

    return errors


def nfc_normalize_storyboard(storyboard: dict) -> dict:
    """
    Tum string alanlarina NFC normalizasyonu uygular.
    Storyboard dict'ini mutate eder ve dondurur.
    """
    def _nfc(val):
        if isinstance(val, str):
            return unicodedata.normalize("NFC", val)
        if isinstance(val, dict):
            return {k: _nfc(v) for k, v in val.items()}
        if isinstance(val, list):
            return [_nfc(x) for x in val]
        return val

    return _nfc(storyboard)
