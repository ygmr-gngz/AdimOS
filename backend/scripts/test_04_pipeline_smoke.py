"""
Test 4 — Pipeline entegrasyon smoke testi (API + DB gerektirir)

Kontrol eder:
  - POST /api/v1/video/preview endpoint'i (storyboard + kalite uyarıları)
  - POST /api/v1/video/create (arka plan pipeline tetikleme)
  - GET  /api/v1/video/jobs/{id} (iş durumu takibi)
  - POST /api/v1/video/render-health (devre kesici durumu)
  - İçerik dedup: check_content_duplicate çalışıyor

⚠️  Railway backend ayakta ve BACKEND_URL env değişkeni gereklidir.
    Yerel test için: BACKEND_URL=http://localhost:8000 python scripts/test_04_pipeline_smoke.py
    Railway testi:   BACKEND_URL=https://adimos-production.up.railway.app python scripts/test_04_pipeline_smoke.py

    JWT token için AUTH_TOKEN env değişkeni gereklidir.
"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

try:
    import httpx
except ImportError:
    print("❌ httpx yüklü değil: pip install httpx")
    sys.exit(1)

PASS = "✅"
FAIL = "❌"

BASE_URL  = os.getenv("BACKEND_URL", "http://localhost:8000")
API       = f"{BASE_URL}/api/v1"
TOKEN     = os.getenv("AUTH_TOKEN", "")
HEADERS   = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}


def _get(path: str) -> httpx.Response:
    return httpx.get(f"{API}{path}", headers=HEADERS, timeout=30)

def _post(path: str, body: dict) -> httpx.Response:
    return httpx.post(f"{API}{path}", json=body, headers=HEADERS, timeout=60)


def test_health():
    r = httpx.get(f"{BASE_URL}/api/v1/health", timeout=10)
    assert r.status_code == 200, f"Health endpoint HTTP {r.status_code}"
    print(f"{PASS} /health: {r.json()}")


def test_render_health():
    r = _get("/video/render-health")
    assert r.status_code == 200, f"render-health HTTP {r.status_code}"
    data = r.json()
    print(f"{PASS} render-health: circuit_open={data.get('circuit_open')}, "
          f"failures={data.get('consecutive_failures')}")


def test_preview_reel():
    body = {
        "type": "reel",
        "title": "Smoke Test Reels",
        "topic": "5188 Sayılı Kanun — Kimlik Kartı",
        "lesson_name": "Özel Güvenlik",
        "content_series": "iki_dakikada_sgs",
        "format": "9:16",
    }
    r = _post("/video/preview", body)
    assert r.status_code == 200, f"preview HTTP {r.status_code}: {r.text[:200]}"
    data = r.json()
    assert data.get("ok"), "preview ok=False"
    scene_count = data.get("scene_count", 0)
    assert scene_count >= 5, f"Yeterli sahne üretilmedi: {scene_count}"
    warnings = data.get("quality_warnings", [])
    print(f"{PASS} preview/reel: {scene_count} sahne, {len(warnings)} uyarı")
    if warnings:
        print(f"  Uyarılar: {warnings[:2]}")
    return data["storyboard"]


def test_create_reel_job():
    if not TOKEN:
        print(f"⚠️  AUTH_TOKEN yok — create job testi atlandı")
        return None
    body = {
        "type": "reel",
        "title": "Smoke Test — SGS Kimlik Kartı",
        "topic": "Özel güvenlik kimlik kartı geçerlilik süresi",
        "lesson_name": "Özel Güvenlik",
        "format": "9:16",
        "content_series": "iki_dakikada_sgs",
        "requested_duration_seconds": 120,
        "duration_tolerance_seconds": 20,
    }
    r = _post("/video/create", body)
    assert r.status_code == 200, f"create HTTP {r.status_code}: {r.text[:200]}"
    job = r.json()
    job_id = job.get("id")
    assert job_id, "job_id yok"
    print(f"{PASS} iş oluşturuldu: {job_id[:8]}... status={job.get('status')}")
    return job_id


def test_job_status(job_id: str | None):
    if not job_id:
        print(f"⚠️  job_id yok — durum testi atlandı")
        return
    # 5 saniye bekle, durumu kontrol et
    time.sleep(5)
    r = _get(f"/video/jobs/{job_id}")
    assert r.status_code == 200, f"job get HTTP {r.status_code}"
    job = r.json()
    status = job.get("status")
    print(f"{PASS} iş durumu: {status} (beklenen: scripting/tts_generating/pending)")


def test_dedup_module():
    """Dedup modülü import + threshold kontrolü."""
    from app.modules.content.content_dedup import (
        _SIMILARITY_THRESHOLD,
        _cosine,
    )
    assert _SIMILARITY_THRESHOLD == 0.82, f"Eşik 0.82 olmalı: {_SIMILARITY_THRESHOLD}"
    # Aynı vektörün kendisiyle benzerliği 1.0
    v = [1.0] * 100
    sim = _cosine(v, v)
    assert abs(sim - 1.0) < 1e-9, f"Aynı vektör benzerliği 1.0 olmalı: {sim}"
    # Dik vektörler benzerliği 0.0
    v1 = [1.0] + [0.0] * 99
    v2 = [0.0] + [1.0] * 99
    sim2 = _cosine(v1, v2)
    assert abs(sim2) < 1e-9, f"Dik vektörler 0.0 olmalı: {sim2}"
    print(f"{PASS} dedup cosine similarity doğru çalışıyor")


if __name__ == "__main__":
    print(f"\n═══ Test 4: Pipeline Smoke Testi ═══")
    print(f"Backend: {BASE_URL}")
    print(f"Auth: {'var' if TOKEN else 'YOK — create job atlanacak'}\n")

    job_id = None
    tests = [
        ("health",        test_health),
        ("render_health", test_render_health),
        ("dedup_module",  test_dedup_module),
        ("preview_reel",  test_preview_reel),
        ("create_job",    lambda: test_create_reel_job()),
    ]

    passed = 0
    for name, t in tests:
        try:
            print(f"--- {name} ---")
            result = t()
            if name == "create_job" and result:
                job_id = result
            passed += 1
        except AssertionError as e:
            print(f"❌ {name}: {e}")
        except Exception as e:
            print(f"❌ {name} beklenmeyen hata: {type(e).__name__}: {e}")

    if job_id:
        print(f"--- job_status ---")
        try:
            test_job_status(job_id)
            passed += 1
        except Exception as e:
            print(f"❌ job_status: {e}")

    print(f"\nSonuç: {passed}/{len(tests) + (1 if job_id else 0)} geçti")
