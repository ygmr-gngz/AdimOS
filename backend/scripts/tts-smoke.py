"""
TTS Smoke Testi — Bölüm 2, TEST R1

Kabul kriterleri:
  - duration >= 8 saniye
  - mean_volume > -30 dB
  - mean_volume != max_volume  (gerçek ses var, sessiz değil)

Kulakla doğrulama için 10 Türkçe telaffuz örneği seslendirilir.

Çalıştır:
  python scripts/tts-smoke.py

Env değişkenleri (Railway'den veya .env'den):
  TTS_PROVIDER  — openai | elevenlabs | google
  TTS_API_KEY   — sağlayıcı API anahtarı
  TTS_VOICE_ID  — Türkçe kadın sesi kimliği
"""
import os, sys, json, subprocess, tempfile, pathlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

PASS = "[OK]"
FAIL = "[FAIL]"

PROVIDER = os.getenv("TTS_PROVIDER", "")
API_KEY  = os.getenv("TTS_API_KEY",  "") or os.getenv("OPENAI_API_KEY", "")
VOICE_ID = os.getenv("TTS_VOICE_ID", "")

# Bölüm 2.4 — 10 telaffuz örneği
PRONUNCIATION_SAMPLES = [
    ("153 Ticari Mallar hesabı",        "yüz elli üç, ticari mallar"),
    ("191 İndirilecek KDV",             "yüz doksan bir, indirilecek ka de ve"),
    ("%18 KDV oranı",                   "yüzde on sekiz ka de ve oranı"),
    ("1.250,50 TL tutarında alış",      "bin iki yüz elli lira elli kuruş"),
    ("800.000 TL öz kaynak",            "sekiz yüz bin lira"),
    ("SGS sınavı tarihleri",            "es ge es sınavı"),
    ("A.Ş. unvanı değişikliği",        "anonim şirket unvanı"),
    ("TTK madde 519 uyarınca",         "türk ticaret kanunu madde"),
    ("2023 yılında vergi oranları",    "iki bin yirmi üç"),
    ("50.000 çalışan kayıt altına",    "elli bin çalışan"),
]

MAIN_TEXT = (
    "Merhaba. Yüz elli üç, ticari mallar hesabı bir varlık hesabıdır. "
    "Alışlarda yüzde on sekiz ka de ve ayrıca kaydedilir. "
    "Bin iki yüz elli lira elli kuruşluk bir alışta borç ve alacak toplamı eşit olmalıdır. "
    "Sınav yaklaşıyor, hazırlıklarını düzenli sürdür."
)

OUT_DIR = pathlib.Path(tempfile.gettempdir()) / "adimos_tts_smoke"
OUT_DIR.mkdir(exist_ok=True)


def _synthesize_openai(text: str, out_path: pathlib.Path) -> bool:
    try:
        import openai
        client = openai.OpenAI(api_key=API_KEY)
        voice = VOICE_ID or "nova"   # nova: Türkçe kadın sesi
        resp = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=0.98,
        )
        out_path.write_bytes(resp.content)
        return True
    except Exception as e:
        print(f"  OpenAI TTS hatası: {e}")
        return False


def _synthesize(text: str, out_path: pathlib.Path) -> bool:
    provider = PROVIDER.lower() or "openai"
    if provider == "openai":
        return _synthesize_openai(text, out_path)
    print(f"  Bilinmeyen provider: {provider}. Desteklenen: openai")
    return False


def _ffprobe(path: pathlib.Path) -> tuple[float, float, float]:
    """Returns (duration_sec, mean_vol_db, max_vol_db)"""
    try:
        r_dur = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=20,
        )
        duration = float(r_dur.stdout.strip() or 0)

        r_vol = subprocess.run(
            ["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, timeout=20,
        )
        import re
        mean_m = re.search(r"mean_volume:\s*([-\d.]+)", r_vol.stderr)
        max_m  = re.search(r"max_volume:\s*([-\d.]+)",  r_vol.stderr)
        mean_vol = float(mean_m.group(1)) if mean_m else 0.0
        max_vol  = float(max_m.group(1))  if max_m  else 0.0
        return duration, mean_vol, max_vol
    except FileNotFoundError:
        print("  ffprobe/ffmpeg bulunamadı — ses analizi atlandı")
        return 0.0, 0.0, 0.0
    except Exception as e:
        print(f"  ffprobe hatası: {e}")
        return 0.0, 0.0, 0.0


def test_main_smoke():
    print("\n--- Ana metin smoke testi ---")
    out = OUT_DIR / "main.mp3"

    print(f"  Sağlayıcı : {PROVIDER or 'openai (varsayılan)'}")
    print(f"  API key   : {'var' if API_KEY else 'YOK'}")
    print(f"  Voice ID  : {VOICE_ID or '(varsayılan kullanılacak)'}")
    print(f"  Metin     : {MAIN_TEXT[:80]}...")

    if not API_KEY:
        print(f"{FAIL} TTS_API_KEY veya OPENAI_API_KEY env'de yok — test atlandı")
        return False

    ok = _synthesize(MAIN_TEXT, out)
    if not ok:
        print(f"{FAIL} Ses üretilemedi")
        return False

    duration, mean_vol, max_vol = _ffprobe(out)
    print(f"  Süre      : {duration:.1f}s  (min: 8s)")
    print(f"  mean_vol  : {mean_vol:.1f} dB  (min: -30 dB)")
    print(f"  max_vol   : {max_vol:.1f} dB")
    print(f"  Dosya     : {out}")

    passed = True
    if duration < 8:
        print(f"{FAIL} Süre kısa: {duration:.1f}s < 8s")
        passed = False
    else:
        print(f"{PASS} Süre OK: {duration:.1f}s >= 8s")

    if mean_vol <= -30:
        print(f"{FAIL} Ses kısık: {mean_vol:.1f} dB <= -30 dB")
        passed = False
    else:
        print(f"{PASS} Ses seviyesi OK: {mean_vol:.1f} dB > -30 dB")

    if mean_vol == max_vol:
        print(f"{FAIL} Sessiz ses: mean == max ({mean_vol:.1f} dB)")
        passed = False
    else:
        print(f"{PASS} Gerçek ses: mean={mean_vol:.1f} != max={max_vol:.1f}")

    return passed


def test_pronunciation_samples():
    if not API_KEY:
        print("\n--- Telaffuz örnekleri atlandı (API key yok) ---")
        return

    print("\n--- Bölüm 2.4: 10 Türkçe telaffuz örneği ---")
    print("  (Dosyaları kulakla dinleyin ve telaffuz doğruysa [OK] yazın)\n")

    for i, (text, expected_spoken) in enumerate(PRONUNCIATION_SAMPLES, 1):
        out = OUT_DIR / f"sample_{i:02d}.mp3"
        ok  = _synthesize(text, out)
        if ok:
            print(f"  {i:2d}. Girdi   : {text}")
            print(f"      Beklenen: {expected_spoken}")
            print(f"      Dosya   : {out}")
            print(f"      --> Kulakla dinle ve dogrula\n")
        else:
            print(f"  {i:2d}. {FAIL} Ses üretilemedi: {text}\n")


if __name__ == "__main__":
    print("=" * 55)
    print("  AdimOS TTS Smoke Testi — Bolum 2 / TEST R1")
    print("=" * 55)

    smoke_ok = test_main_smoke()
    test_pronunciation_samples()

    print("\n" + "=" * 55)
    if smoke_ok:
        print(f"{PASS} Smoke testi gecti — ses kalitesi kabul edilebilir.")
        print(f"  Telaffuz dosyaları: {OUT_DIR}")
        print("  Kulakla dinleme: her dosyayi acip bolum 2.4 listesiyle karsilastir.")
    else:
        print(f"{FAIL} Smoke testi BASARISIZ — deploy oncesi sorunu coz.")
    print("=" * 55)

    sys.exit(0 if smoke_ok else 1)
