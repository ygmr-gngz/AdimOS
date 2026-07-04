# GÖREV 4 — Altyapı Dayanıklılığı Backend Spesifikasyonu

> **Durum:** Watchdog (4.1 kısmi) implemente edildi. Aşağıdakiler kalan backend görevler.
> **Tarih:** 2026-07-04

---

## 4.1 İş Kuyruğu / Worker / Watchdog

### Mevcut Durum
- `_watchdog_sweep()` — `GET /video/jobs` her istendiğinde 30 dakika üzeri "aktif" işleri `failed` yapıyor. ✅
- `regenerate_job` endpoint aktif. ✅
- **Eksik:** İşler HTTP request ömrüne bağlı arka plan task'ları. Railway yeniden başladığında tüm `pending` işler kaybolur.

### Gerekli Değişiklik: DB-backed Worker Loop

```python
# backend/app/workers/video_worker.py (yeni dosya)
"""
Kalıcı video worker — Railway container restart'larına dayanıklı.
video_jobs tablosunu kuyruk olarak kullanır.
"""
import logging, time
from app.db.supabase import get_supabase

logger = logging.getLogger(__name__)
POLL_INTERVAL = 10  # saniye

def claim_next_job(sb) -> dict | None:
    """Bekleyen bir işi atomik olarak sahiplen (race condition önlemek için)."""
    result = sb.rpc("claim_next_video_job", {}).execute()
    return result.data[0] if result.data else None

def run_worker():
    """Ana worker döngüsü — uvicorn startup'ta thread'de başlatılır."""
    sb = get_supabase()
    logger.info("[worker] Video worker başlatıldı")
    while True:
        try:
            job = claim_next_job(sb)
            if job:
                logger.info(f"[worker] İş alındı: {job['id']}")
                _process_job(sb, job)
            else:
                time.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.error(f"[worker] Döngü hatası: {e}")
            time.sleep(30)
```

**Gerekli Supabase fonksiyonu:**

```sql
-- Atomik iş sahiplenme (iki worker aynı işi almasın)
CREATE OR REPLACE FUNCTION claim_next_video_job()
RETURNS SETOF video_jobs AS $$
  UPDATE video_jobs
  SET status = 'scripting', updated_at = NOW()
  WHERE id = (
    SELECT id FROM video_jobs
    WHERE status = 'pending'
    ORDER BY created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
  )
  RETURNING *;
$$ LANGUAGE SQL;
```

---

## 4.2 Sağlayıcı Sağlık Paneli

### `backend/app/api/routes/health.py` — yeni endpoint

```python
@router.get("/health/providers")
async def provider_health():
    """
    OpenAI, Remotion ve Supabase durumunu kontrol eder.
    Frontend bu endpoint'i 60 saniyede bir sorgular.
    """
    results = {}

    # OpenAI — küçük bir test çağrısı yapar
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=5.0)
        client.models.list()  # hafif endpoint
        results["openai"] = {"status": "ok", "latency_ms": ...}
    except Exception as e:
        results["openai"] = {"status": "error", "detail": str(e)[:100]}

    # Remotion — basit ping
    try:
        import httpx
        r = httpx.get(f"{settings.REMOTION_URL}/health", timeout=5)
        results["remotion"] = {"status": "ok" if r.status_code == 200 else "degraded"}
    except Exception as e:
        results["remotion"] = {"status": "error", "detail": "Ulaşılamıyor"}

    # Supabase — test sorgusu
    try:
        from app.db.supabase import get_supabase
        get_supabase().table("video_jobs").select("count").limit(1).execute()
        results["supabase"] = {"status": "ok"}
    except Exception as e:
        results["supabase"] = {"status": "error"}

    return results
```

**Frontend entegrasyonu:** Settings sayfasına basit durum göstergesi eklenmeli.  
Her sağlayıcı: yeşil nokta (ok) / sarı (degraded) / kırmızı (error).

---

## 4.3 Maliyet Sayacı

### Migration

```sql
ALTER TABLE video_jobs
  ADD COLUMN IF NOT EXISTS cost_llm_usd NUMERIC(10,6),
  ADD COLUMN IF NOT EXISTS cost_tts_chars INTEGER,
  ADD COLUMN IF NOT EXISTS cost_render_seconds FLOAT,
  ADD COLUMN IF NOT EXISTS cost_total_usd_est NUMERIC(10,6);
```

### Maliyet Hesaplama (video.py route'unda)

```python
def _calculate_cost(script_tokens: int, tts_chars: int, render_seconds: float) -> dict:
    # GPT-4o-mini: $0.15/1M input + $0.60/1M output — ortalama $0.40/1M
    llm_cost = (script_tokens / 1_000_000) * 0.40
    # OpenAI TTS: $15.00/1M karakter
    tts_cost = (tts_chars / 1_000_000) * 15.00
    # Render: Railway'de hesaplama maliyeti ihmal edilebilir (flat aylık)
    return {
        "cost_llm_usd": round(llm_cost, 6),
        "cost_tts_chars": tts_chars,
        "cost_render_seconds": render_seconds,
        "cost_total_usd_est": round(llm_cost + tts_cost, 6),
    }
```

**Raporlar sayfası:** `video_jobs` tablosundan aylık toplam maliyeti sorgula, dashboard'da göster.

---

## 4.4 Website Chatbot Backend Endpoint'leri

### Karar Seçenekleri

**A) Şimdi implemente et:**

```python
# backend/app/api/routes/website.py
@router.post("/website/chat")
async def website_chat(payload: WebsiteChatPayload):
    # 1. Konuşmayı Supabase'e kaydet
    # 2. RAG'a sor (mevcut rag.query())
    # 3. Yanıtı kaydet ve döndür

@router.get("/website/conversations")
async def list_conversations():
    # Supabase'den konuşma listesi

@router.get("/website/stats")
async def widget_stats():
    # total, today, active sayıları
```

**B) Şimdi değil → Frontend'den modülü gizle:**

`frontend/web/src/components/layout/Sidebar.tsx` içinde:
```tsx
// Website satırını navItems'dan kaldır VEYA "yakında" etiketi ekle
{ href: '/website', label: 'Web Sitesi', icon: Globe, disabled: true },
```

**Öneri:** Backend kısa sürede yazılamayacaksa B seçeneğini uygula — yarım özellik production'da durmasın.

---

## 4.5 Repo Güvenliği (TAMAMLANDI)

- ✅ README'deki `adimos.vercel.app` canlı URL'leri → placeholder ile değiştirildi
- ✅ `data-site-id="musavirlik"` → `data-site-id="your-site-id"` olarak değiştirildi
- ✅ Roadmap güncellendi (SGS Akademi: Aktif, Website Chatbot: Kısmi)

### Repo'yu Private Yapma (Gerekirse)

Şu an README'de iş mantığı, prompt mimarisi ve sistem akışı herkese açık.  
**Tavsiye:** Repo'yu private yap — GitHub'da Settings → Danger Zone → Make Private.  
Embed script'i public kalması gerekiyorsa sadece `public/embed.js` dosyasını ayrı bir public repo'da yayınla.

### Git Geçmişi Sır Taraması

```bash
# Geçmişte commit edilen .env veya secret'ları tara
git log --all --oneline | head -50
git grep -i "sk-" $(git rev-list --all)       # OpenAI key
git grep -i "supabase_service_role" $(git rev-list --all)
```

Eğer geçmişte API key bulunursa: **tüm anahtarları derhal rotate et**, git geçmişi temizlemek için `git-filter-repo` kullan.

---

## Öncelik Sırası

```
1. video_worker.py + claim_next_video_job() SQL fonksiyonu  → Production stabilitesi
2. tts_client.py + pronunciation_dict.py                   → Görev 1.2 + 1.3
3. /health/providers endpoint                              → Görev 4.2
4. cost_* sütunları + hesaplama                            → Görev 4.3
5. Website chatbot VEYA sidebar'dan gizle                  → Görev 4.4
```
