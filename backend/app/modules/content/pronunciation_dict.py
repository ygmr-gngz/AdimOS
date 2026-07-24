"""
SGS / muhasebe terimleri için TTS telaffuz düzeltici.
Metin TTS'e gitmeden önce apply_pronunciation_dict() fonksiyonundan geçer.

Ek: latex_to_spoken_turkish() — LaTeX matematik ifadelerini TTS için Türkçeye çevirir.
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
    # Matematik kutu karakterleri — TTS'de "kare" olarak okunur
    (r'□',           'kare'),
    (r'■',           'dolu kare'),
    (r'△',           'üçgen'),
    (r'○',           'daire'),
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


# ── LaTeX → Türkçe TTS dönüştürücü ─────────────────────────────────────────
# Sıralı — daha önce gelen kural sonraki kuralı etkiler

_LATEX_RULES: list[tuple[str, str]] = [
    # Kesirler: \frac{a}{b} → "a bölü b"
    (r'\\frac\{([^{}]+)\}\{([^{}]+)\}',  r'\1 bölü \2'),
    # Kare kök
    (r'\\sqrt\{([^{}]+)\}',              r'\1 kare kökü'),
    (r'\\sqrt',                          'kare kök'),
    # Üs
    (r'\^\{(\d+)\}',                     r'\1. kuvveti'),
    (r'\^2\b',                           'kare'),
    (r'\^3\b',                           'küp'),
    (r'\^\{?([a-zA-Z])\}?',             r'\1. kuvveti'),
    # Alt indis
    (r'_\{([^{}]+)\}',                   r'\1'),
    (r'_([a-zA-Z\d])',                   r'\1'),
    # Operatörler
    (r'\\times',                         'çarpı'),
    (r'\\cdot',                          'çarpı'),
    (r'\\div',                           'bölü'),
    (r'\\pm',                            'artı eksi'),
    (r'\\mp',                            'eksi artı'),
    (r'\\geq',                           'büyük eşit'),
    (r'\\leq',                           'küçük eşit'),
    (r'\\neq',                           'eşit değil'),
    (r'\\approx',                        'yaklaşık'),
    (r'\\equiv',                         'denk'),
    (r'\\in',                            'elemanı'),
    (r'\\notin',                         'elemanı değil'),
    (r'\\subset',                        'alt kümesi'),
    (r'\\cup',                           'birleşim'),
    (r'\\cap',                           'kesişim'),
    # Büyük operatörler
    (r'\\sum',                           'toplam'),
    (r'\\prod',                          'çarpım'),
    (r'\\int',                           'integral'),
    (r'\\lim',                           'limit'),
    (r'\\infty',                         'sonsuz'),
    # Yunan harfleri
    (r'\\alpha',                         'alfa'),
    (r'\\beta',                          'beta'),
    (r'\\gamma',                         'gama'),
    (r'\\Gamma',                         'Gama'),
    (r'\\delta',                         'delta'),
    (r'\\Delta',                         'Delta'),
    (r'\\epsilon',                       'epsilon'),
    (r'\\varepsilon',                    'epsilon'),
    (r'\\zeta',                          'zeta'),
    (r'\\eta',                           'eta'),
    (r'\\theta',                         'teta'),
    (r'\\Theta',                         'Teta'),
    (r'\\lambda',                        'lambda'),
    (r'\\Lambda',                        'Lambda'),
    (r'\\mu',                            'mü'),
    (r'\\nu',                            'nü'),
    (r'\\xi',                            'ksi'),
    (r'\\pi',                            'pi'),
    (r'\\Pi',                            'Pi'),
    (r'\\rho',                           'ro'),
    (r'\\sigma',                         'sigma'),
    (r'\\Sigma',                         'Sigma'),
    (r'\\tau',                           'tau'),
    (r'\\phi',                           'fi'),
    (r'\\Phi',                           'Fi'),
    (r'\\psi',                           'psi'),
    (r'\\Psi',                           'Psi'),
    (r'\\omega',                         'omega'),
    (r'\\Omega',                         'Omega'),
    # Gruplandırıcılar — kaldır
    (r'\\left\s*[\(\[\{]',              ' '),
    (r'\\right\s*[\)\]\}]',             ' '),
    (r'\\bigl?\s*[\(\[\{]',             ' '),
    (r'\\bigr?\s*[\)\]\}]',             ' '),
    # Metin komutları
    (r'\\text\{([^{}]+)\}',             r'\1'),
    (r'\\mathrm\{([^{}]+)\}',           r'\1'),
    (r'\\mathbf\{([^{}]+)\}',           r'\1'),
    # Geriye kalan LaTeX komutları ve süslü parantezler
    (r'\\[a-zA-Z]+',                    ' '),
    (r'[{}]',                           ' '),
    # Birden fazla boşluk
    (r'\s{2,}',                         ' '),
]

_latex_compiled = [
    (re.compile(p), r)
    for p, r in _LATEX_RULES
]


def latex_to_spoken_turkish(latex: str) -> str:
    """
    LaTeX matematik ifadesini TTS için Türkçe konuşma diline çevirir.
    MathExpression.spoken_text yoksa bu fonksiyon kullanılır.

    Örnek:
      "\\frac{a+b}{2}"  →  "a artı b bölü 2"
      "x^{2}"           →  "x kare"
      "\\sqrt{9}"       →  "9 kare kökü"
    """
    text = latex.strip()
    for pattern, replacement in _latex_compiled:
        text = pattern.sub(replacement, text)
    # Son temizlik
    text = text.strip()
    # Bitişik operatör düzeltmesi: "a+ b" → "a artı b" gibi
    text = re.sub(r'\s*\+\s*', ' artı ', text)
    text = re.sub(r'\s*-\s*(?=\w)', ' eksi ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()
