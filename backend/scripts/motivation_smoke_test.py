#!/usr/bin/env python3
"""
Motivasyon videosu izole smoke testi.
Her aşamayı (DB → senaryo → TTS → Remotion → storage → durum) ayrı ayrı test eder.

Kullanım (Railway /app dizininden):
  python scripts/motivation_smoke_test.py

Ortam değişkenleri (Railway'de mevcut):
  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY, REMOTION_URL
"""
import os, sys, traceback, uuid
from datetime import datetime

# Railway: WORKDIR=/app, script at /app/scripts/ → app package at /app/app/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ─── Ortam ────────────────────────────────────────────────────────────────────
SUPABASE_URL  = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY  = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", os.environ.get("SUPABASE_KEY", ""))
OPENAI_KEY    = os.environ.get("OPENAI_API_KEY", "")
REMOTION_URL  = os.environ.get("REMOTION_URL", "")

_OK   = "\033[92m✓\033[0m"
_FAIL = "\033[91m✗\033[0m"
_WARN = "\033[93m⚠\033[0m"
_INFO = "\033[94mℹ\033[0m"

def _log(symbol: str, stage: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {symbol} [{stage}] {msg}", flush=True)

def _ok(stage, msg):   _log(_OK,   stage, msg)
def _fail(stage, msg): _log(_FAIL, stage, msg)
def _warn(stage, msg): _log(_WARN, stage, msg)
def _info(stage, msg): _log(_INFO, stage, msg)

errors: list[str] = []

# ─── Aşama 0: Ortam değişkenleri ──────────────────────────────────────────────
_info("ENV", "Ortam değişkenleri kontrol ediliyor...")
for name, val in [("SUPABASE_URL", SUPABASE_URL), ("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_KEY),
                   ("OPENAI_API_KEY", OPENAI_KEY), ("REMOTION_URL", REMOTION_URL)]:
    if val:
        _ok("ENV", f"{name} = ...{val[-6:]}")
    else:
        _warn("ENV", f"{name} eksik")
        if name != "REMOTION_URL":
            errors.append(f"ENV: {name} eksik")

if errors:
    _fail("ENV", f"{len(errors)} kritik değişken eksik — test durduruluyor")
    sys.exit(1)

# ─── Supabase istemcisi ────────────────────────────────────────────────────────
try:
    from supabase import create_client, Client
    sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    _ok("SUPABASE", "İstemci oluşturuldu")
except Exception as e:
    _fail("SUPABASE", f"İstemci oluşturulamadı: {e}")
    sys.exit(1)

# ─── Aşama 1: video_jobs INSERT (kısıt testi) ────────────────────────────────
_info("DB_INSERT", "video_jobs INSERT deneniyor (type='motivation')...")
test_job_id = str(uuid.uuid4())
try:
    r = sb.table("video_jobs").insert({
        "id": test_job_id,
        "type": "motivation",
        "title": "[SMOKE TEST] Motivasyon Videosu",
        "status": "pending",
        "format": "9:16",
    }).execute()

    if r.data:
        _ok("DB_INSERT", f"video_jobs INSERT başarılı — job_id={test_job_id[:8]}")
    else:
        _fail("DB_INSERT", "INSERT yanıtı boş")
        errors.append("DB_INSERT: Boş yanıt")
except Exception as e:
    err = str(e)
    if "check_violation" in err or "23514" in err or "video_jobs_type_check" in err:
        _fail("DB_INSERT", f"KİSIT İHLALİ — migration 009/010 production'da uygulanmamış!\n  {err[:300]}")
        errors.append("DB_INSERT: video_jobs_type_check kısıtı ihlali — migration 009 çalıştırılmamış")
    else:
        _fail("DB_INSERT", f"DB hatası: {err[:300]}")
        errors.append(f"DB_INSERT: {err[:200]}")

if errors:
    _fail("SMOKE", "Aşama 1 (DB INSERT) başarısız — sonraki aşamalar test edilemiyor")
    print("\n--- TANI RAPORU ---")
    for e in errors:
        print(f"  {_FAIL} {e}")
    print("\nÇözüm: Supabase SQL Editor'de 010_konu_anlatimi_type.sql çalıştırın.")
    sys.exit(1)

# ─── Aşama 2: video_scenes INSERT ────────────────────────────────────────────
_info("SCENES_INSERT", "video_scenes INSERT deneniyor (component='MotivationScene')...")
try:
    r2 = sb.table("video_scenes").insert({
        "job_id": test_job_id,
        "scene_index": 0,
        "component": "MotivationScene",
        "duration_seconds": 15,
        "data": {"id": 1, "component": "MotivationScene", "message": "Test mesajı"},
        "voice_text": "Bu bir smoke test mesajıdır.",
        "status": "pending",
    }).execute()

    if r2.data:
        _ok("SCENES_INSERT", f"video_scenes INSERT başarılı — scene_id={r2.data[0].get('id', '?')}")
    else:
        _fail("SCENES_INSERT", "INSERT yanıtı boş")
        errors.append("SCENES_INSERT: Boş yanıt")
except Exception as e:
    err = str(e)
    if "check_violation" in err or "23514" in err:
        _fail("SCENES_INSERT", f"KİSIT İHLALİ — video_scenes component kısıtı: {err[:300]}")
        errors.append(f"SCENES_INSERT: component kısıtı ihlali: {err[:150]}")
    else:
        _fail("SCENES_INSERT", f"DB hatası: {err[:300]}")
        errors.append(f"SCENES_INSERT: {err[:200]}")

# ─── Aşama 3: GPT (motivation_generator) ─────────────────────────────────────
_info("GPT", "motivation_generator test ediliyor...")
try:
    from app.modules.content.motivation_generator import generate_motivation_storyboard
    result = generate_motivation_storyboard("SGS sınavı yaklaşıyor", "reels", "sıcak ve samimi")
    scenes = result.get("scenes", [])
    if scenes:
        _ok("GPT", f"Storyboard üretildi: {result.get('title', '?')} ({len(scenes)} sahne)")
        for s in scenes[:2]:
            _info("GPT", f"  sahne={s.get('type')} narration={repr((s.get('narration') or '')[:60])}")
    else:
        _warn("GPT", "Sahne listesi boş")
        errors.append("GPT: Boş sahne listesi")
except Exception as e:
    _fail("GPT", f"motivation_generator hatası: {e}")
    errors.append(f"GPT: {str(e)[:200]}")
    traceback.print_exc()

# ─── Aşama 4: TTS ─────────────────────────────────────────────────────────────
_info("TTS", "TTS test ediliyor (kısa metin)...")
try:
    from app.modules.voice.tts import synthesize
    audio_bytes = synthesize("Bu bir smoke test sesidir.")
    if audio_bytes and len(audio_bytes) > 1000:
        _ok("TTS", f"TTS başarılı — {len(audio_bytes)} byte ses üretildi")
    else:
        _warn("TTS", f"TTS çok kısa yanıt: {len(audio_bytes) if audio_bytes else 0} byte")
        errors.append("TTS: Çok kısa çıktı")
except Exception as e:
    _fail("TTS", f"TTS hatası: {e}")
    errors.append(f"TTS: {str(e)[:200]}")

# ─── Aşama 5: Remotion bağlantısı ─────────────────────────────────────────────
if REMOTION_URL:
    _info("REMOTION", f"Remotion ping: {REMOTION_URL}/health ...")
    try:
        import httpx
        r3 = httpx.get(f"{REMOTION_URL}/health", timeout=30)
        if r3.status_code == 200:
            _ok("REMOTION", f"Remotion yanıt veriyor: {r3.text[:100]}")
        else:
            _warn("REMOTION", f"Remotion HTTP {r3.status_code}: {r3.text[:100]}")
            errors.append(f"REMOTION: HTTP {r3.status_code}")
    except Exception as e:
        _fail("REMOTION", f"Remotion bağlanamadı: {e}")
        errors.append(f"REMOTION: {str(e)[:150]}")
else:
    _warn("REMOTION", "REMOTION_URL yok — render testi atlandı")

# ─── Aşama 6: Temizlik ────────────────────────────────────────────────────────
_info("CLEANUP", "Test kaydı siliniyor...")
try:
    sb.table("video_scenes").delete().eq("job_id", test_job_id).execute()
    sb.table("video_jobs").delete().eq("id", test_job_id).execute()
    _ok("CLEANUP", f"Test kaydı silindi: {test_job_id[:8]}")
except Exception as e:
    _warn("CLEANUP", f"Temizlik hatası (önemli değil): {e}")

# ─── Sonuç ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if not errors:
    print(f"{_OK}  TÜM AŞAMALAR BAŞARILI — Motivasyon video pipeline sağlıklı")
else:
    print(f"{_FAIL}  {len(errors)} HATA BULUNDU:")
    for err in errors:
        print(f"     • {err}")
    print()
    if any("kısıt" in e or "constraint" in e.lower() or "migration" in e for e in errors):
        print("  → ACİL: Supabase SQL Editor'de 010_konu_anlatimi_type.sql çalıştırın")
    if any("TTS" in e for e in errors):
        print("  → TTS: OPENAI_API_KEY kotası veya bağlantı sorunu")
    if any("REMOTION" in e for e in errors):
        print("  → REMOTION: Railway servisi uyuyor olabilir — manuel wake-up yapın")
print("=" * 60)
sys.exit(0 if not errors else 1)
