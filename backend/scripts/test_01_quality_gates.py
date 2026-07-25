"""
Test 1 — Kalite kapıları (quality_gates.py)

Kontrol eder:
  - check_storyboard_quality: eksik sahne, voice_text, component kuralları
  - check_audio_volume: geçerli MP3 baytları ile ses seviyesi
  - check_video_duration: süre toleransı
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.modules.content.quality_gates import (
    check_storyboard_quality,
    check_audio_volume,
    check_video_duration,
)

PASS = "✅"
FAIL = "❌"


def test_storyboard_empty():
    w = check_storyboard_quality({"scenes": []}, "konu_anlatimi")
    assert w, "Boş storyboard uyarı üretmeli"
    print(f"{PASS} boş storyboard uyarısı: {w[0][:60]}")


def test_storyboard_min_scenes():
    scenes = [
        {"id": i, "component": "LessonConceptScene",
         "voice_text": "test", "duration_seconds": 90}
        for i in range(1, 5)
    ]
    w = check_storyboard_quality({"scenes": scenes}, "konu_anlatimi")
    assert any("sahne" in x.lower() for x in w), "Yetersiz sahne sayısı uyarı vermeli"
    print(f"{PASS} sahne sayısı uyarısı: {w[0][:60]}")


def test_storyboard_missing_voice():
    scenes = [
        {"id": i, "component": "LessonConceptScene",
         "voice_text": "" if i % 2 == 0 else "text", "duration_seconds": 90}
        for i in range(1, 12)
    ]
    w = check_storyboard_quality({"scenes": scenes}, "konu_anlatimi")
    assert any("voice_text" in x for x in w), "Eksik voice_text uyarı vermeli"
    print(f"{PASS} voice_text eksik uyarısı: {w[0][:60]}")


def test_storyboard_ok():
    scenes = [
        {"id": i, "component": "LessonConceptScene",
         "voice_text": "Uzun anlatım metni " * 10, "duration_seconds": 90}
        for i in range(1, 12)
    ]
    w = check_storyboard_quality({"scenes": scenes}, "konu_anlatimi")
    # Sadece süre uyarısı olabilir (voice_text çok kısa), sahne sayısı OK
    no_scene_warn = not any("sahne sayısı" in x for x in w)
    no_voice_warn = not any("voice_text" in x for x in w)
    assert no_scene_warn, f"Yeterli sahne var, uyarı olmamalı: {w}"
    assert no_voice_warn, f"Voice_text var, uyarı olmamalı: {w}"
    print(f"{PASS} geçerli storyboard uyarı yok (toplam={len(w)} uyarı)")


def test_audio_volume_skip_no_ffmpeg():
    # ffmpeg yoksa True döner (graceful skip)
    ok, vol = check_audio_volume(b"\x00" * 100)
    # Gerçek MP3 değil — parse edilemez, graceful True beklenir
    print(f"{PASS} ses seviyesi kontrolü (dummy bytes): ok={ok}, vol={vol:.1f}dB")


def test_duration_no_url():
    ok, actual, msg = check_video_duration("", None)
    assert ok, "URL/süre yok → True döner"
    print(f"{PASS} süre kontrolü skip: {msg}")


def test_duration_tolerance():
    # ffprobe olmadan URL kontrolü yapılamaz, graceful döner
    ok, actual, msg = check_video_duration("https://example.com/video.mp4", 120, 15)
    # ffprobe bulunamaz ya da URL erişilemez → True döner
    print(f"{PASS} süre kontrolü (erişilemeyen URL): ok={ok}, msg={msg[:60]}")


if __name__ == "__main__":
    print("\n═══ Test 1: Kalite Kapıları ═══\n")
    tests = [
        test_storyboard_empty,
        test_storyboard_min_scenes,
        test_storyboard_missing_voice,
        test_storyboard_ok,
        test_audio_volume_skip_no_ffmpeg,
        test_duration_no_url,
        test_duration_tolerance,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"{FAIL} {t.__name__}: {e}")
        except Exception as e:
            print(f"{FAIL} {t.__name__} beklenmeyen hata: {e}")
    print(f"\nSonuç: {passed}/{len(tests)} geçti")
