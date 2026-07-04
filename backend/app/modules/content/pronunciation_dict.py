"""
SGS / muhasebe terimleri için TTS telaffuz düzeltici.
Metin TTS'e gitmeden önce apply_pronunciation_dict() fonksiyonundan geçer.
"""
import re

# (regex_pattern, replacement) çiftleri — sırayla uygulanır
_RULES: list[tuple[str, str]] = [
    # Kısaltmalar — harf harf okunması için boşluk eklenir
    (r'\bKDV\b',   'K D V'),
    (r'\bÖTV\b',   'Ö T V'),
    (r'\bVUK\b',   'V U K'),
    (r'\bGVK\b',   'G V K'),
    (r'\bKVK\b',   'K V K'),
    (r'\bTTK\b',   'T T K'),
    (r'\bBK\b',    'B K'),
    (r'\bİK\b',    'İ K'),
    (r'\bSSGSS\b', 'S S G S S'),
    (r'\bSGK\b',   'S G K'),
    (r'\bSSK\b',   'S S K'),
    (r'\bBAĞ-KUR\b', 'Bağ-Kur'),
    (r'\bTMS\b',   'T M S'),
    (r'\bTFRS\b',  'T F R S'),
    (r'\bUMS\b',   'U M S'),
    (r'\bIFRS\b',  'I F R S'),
    (r'\bSMMM\b',  'S M M M'),
    (r'\bYMM\b',   'Y M M'),
    (r'\bSGS\b',   'S G S'),
    (r'\bSMBK\b',  'S M B K'),
    (r'\bBSMV\b',  'B S M V'),
    (r'\bMTVK\b',  'M T V K'),
    (r'\bEVSE\b',  'E V S E'),
    # Madde/fıkra numaraları
    (r'\bm\.\s*(\d+)',   r'madde \1'),
    (r'\bMd\.\s*(\d+)',  r'madde \1'),
    (r'\bf\.\s*(\d+)',   r'fıkra \1'),
    (r'\bBd\.\s*(\d+)',  r'bent \1'),
    # Yüzde işareti
    (r'%\s*(\d)',        r'yüzde \1'),
    # Para birimleri
    (r'\bTL\b',          'Türk Lirası'),
    (r'₺\s*(\d)',        r'Türk Lirası \1'),
    # Yaygın muhasebe terimleri kısaltma → tam form
    (r'\bDR\b',          'Borç'),
    (r'\bAL\b',          'Alacak'),
    # Sıra sayıları (1. → birinci)  sadece tek haneli — daha uzunu bırak
    (r'(?<!\d)1\.',  'birinci'),
    (r'(?<!\d)2\.',  'ikinci'),
    (r'(?<!\d)3\.',  'üçüncü'),
    (r'(?<!\d)4\.',  'dördüncü'),
    (r'(?<!\d)5\.',  'beşinci'),
]

_compiled = [
    (re.compile(pattern, re.IGNORECASE), replacement)
    for pattern, replacement in _RULES
]


def apply_pronunciation_dict(text: str) -> str:
    """TTS'e gönderilmeden önce metni standartlaştırır."""
    for pattern, replacement in _compiled:
        text = pattern.sub(replacement, text)
    return text
