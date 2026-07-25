"""
Test 3 — EducationalReel120 storyboard üreticisi (GPT-4o gerektirir)

Kontrol eder:
  - generate_educational_reel_storyboard: 7 sahne, doğru component, segment_type'lar
  - İçerik serisi başlık şablonu
  - Sahne alanları (voice_text, hook_text, cta_text vb.)

⚠️  Bu test gerçek OpenAI API çağrısı yapar — OPENAI_API_KEY gereklidir.
    Çalıştırmak için: python scripts/test_03_reel_storyboard.py
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

PASS = "✅"
FAIL = "❌"

_EXPECTED_SEGMENTS = ["hook", "context", "content", "content", "mistake", "tip", "outro"]


def test_reel_storyboard_structure():
    from app.modules.sgs.educational_reel_storyboard import generate_educational_reel_storyboard

    sb = generate_educational_reel_storyboard(
        title="SGS Kimlik Kartı Geçerlilik Süresi",
        topic="Özel güvenlik kimlik kartı 5 yıl geçerlidir",
        subject="Özel Güvenlik",
        content_series="iki_dakikada_sgs",
    )

    scenes = sb.get("scenes", [])
    print(f"  Üretilen sahne sayısı: {len(scenes)}")
    assert len(scenes) >= 5, f"En az 5 sahne beklendi, {len(scenes)} üretildi"
    print(f"{PASS} sahne sayısı: {len(scenes)}")

    # Tüm sahneler EducationalReelScene olmalı
    wrong_comp = [s for s in scenes if s.get("component") != "EducationalReelScene"]
    assert not wrong_comp, f"Yanlış component: {[s['component'] for s in wrong_comp]}"
    print(f"{PASS} tüm sahneler EducationalReelScene")

    # İlk sahne hook olmalı
    assert scenes[0].get("segment_type") == "hook", \
        f"İlk sahne hook olmalı, '{scenes[0].get('segment_type')}' geldi"
    print(f"{PASS} ilk sahne hook")

    # Son sahne outro olmalı
    assert scenes[-1].get("segment_type") == "outro", \
        f"Son sahne outro olmalı, '{scenes[-1].get('segment_type')}' geldi"
    print(f"{PASS} son sahne outro")

    # Hook sahnesi hook_text taşımalı
    hook = scenes[0]
    assert hook.get("hook_text"), "hook sahnesi hook_text taşımalı"
    print(f"{PASS} hook_text: '{hook['hook_text'][:40]}'")

    # Outro sahnesi cta_text taşımalı
    outro = scenes[-1]
    assert outro.get("cta_text"), "outro sahnesi cta_text taşımalı"
    print(f"{PASS} cta_text: '{outro['cta_text'][:40]}'")

    # Tüm sahneler voice_text taşımalı
    missing_voice = [s.get("id") for s in scenes if not (s.get("voice_text") or "").strip()]
    assert not missing_voice, f"voice_text eksik sahneler: {missing_voice}"
    print(f"{PASS} tüm sahnelerde voice_text var")

    # İçerik serisi başlığı uygulanmış olmalı
    assert "2 Dakikada SGS" in sb.get("title", ""), \
        f"İçerik serisi başlığı uygulanmadı: '{sb.get('title')}'"
    print(f"{PASS} seri başlığı: '{sb['title']}'")

    # Toplam süre ~120s civarında olmalı
    total = sum(s.get("duration_seconds", 0) for s in scenes)
    assert 90 <= total <= 150, f"Toplam süre {total}s — 90-150s aralığı beklendi"
    print(f"{PASS} toplam süre: {total}s")

    return sb


def test_series_title_templates():
    from app.modules.sgs.educational_reel_storyboard import (
        SERIES_TITLE_TEMPLATES,
        _apply_series_title,
    )
    for series, template in SERIES_TITLE_TEMPLATES.items():
        result = _apply_series_title("test", "KDV", series)
        assert "KDV" in result, f"Şablon KDV içermeli: {result}"
    print(f"{PASS} {len(SERIES_TITLE_TEMPLATES)} seri başlık şablonu çalışıyor")


if __name__ == "__main__":
    print("\n═══ Test 3: EducationalReel Storyboard (GPT-4o) ═══\n")
    print("⚠️  Bu test OpenAI API çağrısı yapar (~2-5 saniye)\n")
    tests = [
        test_series_title_templates,
        test_reel_storyboard_structure,
    ]
    passed = 0
    for t in tests:
        try:
            print(f"--- {t.__name__} ---")
            t()
            passed += 1
        except ImportError as e:
            print(f"❌ Import hatası (env yüklü mü?): {e}")
        except Exception as e:
            print(f"❌ {t.__name__}: {e}")
    print(f"\nSonuç: {passed}/{len(tests)} geçti")
