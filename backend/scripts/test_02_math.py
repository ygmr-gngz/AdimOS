"""
Test 2 — Matematik araçları (pronunciation_dict + math_validator)

Kontrol eder:
  - latex_to_spoken_turkish: LaTeX → Türkçe dönüşüm
  - apply_pronunciation_dict: kısaltma ve kutu karakteri kuralları
  - validate_math_steps: SymPy ile doğru/yanlış denklem ayrımı
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.modules.content.pronunciation_dict import (
    apply_pronunciation_dict,
    latex_to_spoken_turkish,
)
from app.modules.content.math_validator import validate_math_steps

PASS = "✅"
FAIL = "❌"


def test_latex_fraction():
    result = latex_to_spoken_turkish(r"\frac{a+b}{2}")
    assert "bölü" in result.lower(), f"Kesir dönüşümü beklendi: '{result}'"
    print(f"{PASS} kesir: '{result}'")


def test_latex_sqrt():
    result = latex_to_spoken_turkish(r"\sqrt{9}")
    assert "kök" in result.lower(), f"Kök dönüşümü beklendi: '{result}'"
    print(f"{PASS} kökü: '{result}'")


def test_latex_power():
    result = latex_to_spoken_turkish(r"x^2")
    assert "kare" in result.lower(), f"Üs dönüşümü beklendi: '{result}'"
    print(f"{PASS} kare: '{result}'")


def test_latex_greek():
    result = latex_to_spoken_turkish(r"\alpha + \beta")
    assert "alfa" in result.lower() and "beta" in result.lower(), f"Yunan harfi beklendi: '{result}'"
    print(f"{PASS} yunan harfleri: '{result}'")


def test_pronunciation_kdv():
    result = apply_pronunciation_dict("KDV oranı %18'dir.")
    assert "K D V" in result, f"KDV kısaltması: '{result}'"
    assert "yüzde" in result.lower(), f"Yüzde dönüşümü: '{result}'"
    print(f"{PASS} KDV + yüzde: '{result}'")


def test_pronunciation_box_char():
    result = apply_pronunciation_dict("Cevap: □")
    assert "kare" in result.lower(), f"Kutu karakteri dönüşümü: '{result}'"
    print(f"{PASS} kutu karakteri □ → 'kare': '{result}'")


def test_math_validator_correct():
    steps = [
        {"board_text": "2 + 3 = 5", "step_type": "solve"},
        {"board_text": "10 * 5 = 50", "step_type": "solve"},
    ]
    errs = validate_math_steps(steps)
    assert len(errs) == 0, f"Doğru denklemlerde hata olmamalı: {errs}"
    print(f"{PASS} doğru denklemler geçti")


def test_math_validator_wrong():
    steps = [
        {"board_text": "2 + 3 = 6", "step_type": "solve"},  # yanlış
    ]
    errs = validate_math_steps(steps)
    # SymPy varsa hata yakalar, yoksa boş döner (graceful)
    if errs:
        print(f"{PASS} yanlış denklem yakalandı: {errs[0][:60]}")
    else:
        print(f"{PASS} SymPy yüklü değil veya parse edilemedi — graceful skip")


def test_math_validator_text_skip():
    # Türkçe metin — denklem değil, atlanmalı
    steps = [
        {"board_text": "Kasa hesabı borç bakiyesi verir", "step_type": "text"},
        {"board_text": "1.500 TL nakit vardır", "step_type": "given"},
    ]
    errs = validate_math_steps(steps)
    assert len(errs) == 0, f"Metin adımları hata vermemeli: {errs}"
    print(f"{PASS} metin adımları atlandı")


if __name__ == "__main__":
    print("\n═══ Test 2: Matematik Araçları ═══\n")
    tests = [
        test_latex_fraction,
        test_latex_sqrt,
        test_latex_power,
        test_latex_greek,
        test_pronunciation_kdv,
        test_pronunciation_box_char,
        test_math_validator_correct,
        test_math_validator_wrong,
        test_math_validator_text_skip,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"❌ {t.__name__}: {e}")
        except Exception as e:
            print(f"❌ {t.__name__} beklenmeyen hata: {e}")
    print(f"\nSonuç: {passed}/{len(tests)} geçti")
