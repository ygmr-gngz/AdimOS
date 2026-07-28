"""
Unicode doğrulama — bozuk karakter, mojibake, encoding hatası tespiti.
Bu karakterlerden biri herhangi bir metin alanında varsa render durur.
"""
import unicodedata
import re

_BAD_CHARS = frozenset("□�Ä±ÅÃ§Ã¼Ã¶Ä")

_MOJIBAKE_RE = re.compile(
    r"Ä±|ÅŸ|Ã§|Ã¼|Ã¶|ÄŸ|Ã‡|Ãœ|Ä°|Â·|â€™|â€"|â€œ|â€\x9d"
)

_REPLACEMENT_CHAR = "�"  # □


def validate_unicode(text: str, field_name: str = "text") -> list[str]:
    """
    Metin alanında bozuk karakter var mı kontrol eder.
    Returns: hata mesajları listesi — boşsa OK.
    """
    errors = []

    if _REPLACEMENT_CHAR in text:
        errors.append(f"{field_name}: U+FFFD değiştirme karakteri içeriyor")

    if "□" in text:
        errors.append(f"{field_name}: U+25A1 boş kare karakteri içeriyor (encoding bozukluğu?)")

    if _MOJIBAKE_RE.search(text):
        sample = _MOJIBAKE_RE.search(text).group()
        errors.append(f"{field_name}: mojibake tespit edildi ('{sample}') — UTF-8 decode hatası")

    return errors


def validate_storyboard_unicode(storyboard: dict) -> list[str]:
    """
    Tüm sahne metin alanlarında unicode doğrulama yapar.
    Returns: hata mesajları listesi.
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
    Tüm string alanlarına NFC normalizasyonu uygular.
    Storyboard dict'ini mutate eder ve döndürür.
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
