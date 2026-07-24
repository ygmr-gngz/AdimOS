"""
Matematik doğrulayıcı — SymPy ile storyboard'daki hesaplama adımlarını çapraz kontrol eder.

ChalkboardSolutionScene'deki chalkboard_steps içinde yer alan
sayısal sonuçların doğruluğunu SymPy üzerinden denetler.

Kullanım:
  errors = validate_math_steps(chalkboard_steps)
  # errors boş → tüm adımlar doğru (veya SymPy yüklenemedi — sessizce geçildi)
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def _try_import_sympy():
    try:
        import sympy  # type: ignore
        return sympy
    except ImportError:
        return None


def _parse_equation(text: str):
    """
    'ifade = sonuç' biçimindeki board_text'i parçalar.
    Returns: (lhs_str, rhs_str) veya None.
    """
    parts = re.split(r'(?<!=)=(?!=)', text.strip(), maxsplit=1)
    if len(parts) != 2:
        return None
    lhs = parts[0].strip()
    rhs = parts[1].strip()
    if not lhs or not rhs:
        return None
    # Birim içeren değerleri atla: "1.500 TL", "% 18" vb.
    if re.search(r'[A-Za-zÇçĞğıİÖöŞşÜü₺%]', rhs):
        return None
    return lhs, rhs


def _sanitize_for_sympy(expr: str) -> str:
    """İnsan-okunur ifadeyi SymPy'a beslenebilir hale getirir."""
    # Türkçe ondalık virgülünü noktaya çevir
    expr = re.sub(r'(\d),(\d)', r'\1.\2', expr)
    # Binlik ayırıcı nokta veya virgül: "1.500" → "1500"
    expr = re.sub(r'(\d)\.(\d{3})(?!\d)', r'\1\2', expr)
    # × → *
    expr = expr.replace('×', '*').replace('÷', '/')
    # Boşluklar arasındaki çarpma: "2 a" → "2*a"
    expr = re.sub(r'(\d)\s+([a-zA-Z])', r'\1*\2', expr)
    return expr.strip()


def validate_math_steps(
    chalkboard_steps: list[dict],
    tolerance: float = 1e-6,
) -> list[str]:
    """
    chalkboard_steps listesindeki sayısal denklemleri SymPy ile kontrol eder.

    Returns: hata mesajları listesi. Boş → tamam.
    """
    sympy = _try_import_sympy()
    if sympy is None:
        logger.debug("[math] SymPy yüklü değil — doğrulama atlandı")
        return []

    errors: list[str] = []

    for i, step in enumerate(chalkboard_steps):
        board_text = (step.get("board_text") or "").strip()
        if not board_text:
            continue

        parsed = _parse_equation(board_text)
        if parsed is None:
            continue

        lhs_raw, rhs_raw = parsed
        try:
            lhs_expr = _sanitize_for_sympy(lhs_raw)
            rhs_expr = _sanitize_for_sympy(rhs_raw)

            lhs_val = sympy.sympify(lhs_expr, evaluate=True)
            rhs_val = sympy.sympify(rhs_expr, evaluate=True)

            diff = sympy.Abs(lhs_val - rhs_val)
            simplified = sympy.simplify(diff)

            # Sayısal değerlendirme dene
            try:
                num_diff = float(simplified.evalf())
                if num_diff > tolerance:
                    errors.append(
                        f"Adım {i+1} hatalı: '{board_text}' "
                        f"(fark={num_diff:.6g})"
                    )
            except (TypeError, ValueError, sympy.core.sympify.SympifyError):
                # Sayısal değerlendirilemiyorsa atla
                pass

        except Exception as exc:
            logger.debug(f"[math] adım {i+1} SymPy parse hatası (atlandı): {exc}")
            continue

    if errors:
        logger.warning(f"[math] {len(errors)} matematik hatası tespit edildi")
    return errors


def validate_storyboard_math(storyboard: dict) -> list[str]:
    """
    Storyboard'daki tüm ChalkboardSolutionScene sahnelerini kontrol eder.
    Returns: birleşik hata listesi.
    """
    all_errors: list[str] = []
    for scene in storyboard.get("scenes", []):
        if scene.get("component") != "ChalkboardSolutionScene":
            continue
        steps = scene.get("chalkboard_steps") or []
        errs  = validate_math_steps(steps)
        for err in errs:
            all_errors.append(f"Sahne {scene.get('id', '?')}: {err}")
    return all_errors
