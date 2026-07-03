# FAZ 3 — Mimari Değerlendirme

**Tarih:** 2026-07-03

---

## 1. Güçlü Yönler

### ✅ Route Koruması — Router-Level Dependency
```python
_protected = APIRouter(dependencies=[Depends(get_current_user)])
```
Bireysel endpoint'lere `Depends` eklemeyi unutma riski sıfır. Tüm protected route'lar otomatik korunuyor.

### ✅ Tek Gerçek Kaynak — sgs_questions
Dashboard sayaçları `sgs_questions` tablosundan geliyor. `sgs_analyses.subjects` JSONB özet için kullanılıyor ama gerçek veri normalize tablo. Doğru tasarım.

### ✅ Background Task Pattern
FastAPI `BackgroundTasks` ile ağır işler (PDF analiz, video render, reindex) HTTP response'u bloke etmeden çalışıyor. SGS analiz endpoint'i sonucu direkt döndürse de video işleme arka planda.

### ✅ Modüler Backend Yapısı
```
backend/app/
├── api/routes/     # HTTP katmanı
├── modules/        # İş mantığı
├── db/repositories/ # Veri erişim katmanı
└── core/           # Config, auth
```
Katmanlar net ayrılmış. routes → modules → repositories zinciri doğru.

### ✅ CORS Dar Liste
Sadece 3 origin whitelist'te. Geniş CORS açık API'lar için tehlike.

---

## 2. Mimari Riskler

### ⚠️ M-01 — APScheduler Main Process'te

**Durum:** `start_scheduler()` uvicorn worker içinde çalışıyor.

**Risk:**
- Railway rolling restart → scheduler durur, gün için brief oluşturulmaz
- Birden fazla worker/replica → her worker kendi scheduler'ını çalıştırır → brief N kez oluşur
- Crash → `last_run` state kaybı

**Çözüm Seçenekleri (kolaydan zora):**

1. **Railway Cron Job** (önerilen — ücretsiz, Railway native):
   ```
   Railway → Add service → Cron
   Schedule: 0 8 * * *
   Command: python -m app.modules.automation.run_brief
   ```
   
2. **cron-job.org** — webhook tetikleyicisi, mevcut `/agents/daily-brief` endpoint'i çağırır

3. **Supabase pg_cron** — PostgreSQL içi cron (30 dakikadan uzun işler için uygun değil)

### ⚠️ M-02 — moviepy 1.0.3 + ffmpeg Bağımlılığı

`moviepy==1.0.3` stale bir sürüm (2020). Railway container'a `ffmpeg` kurulumu gerekiyor.

**Kontrol Edilmesi Gereken:** Railway'de `ffmpeg` build paketi var mı?

```dockerfile
# Procfile veya Railway Dockerfile'a eklenmeli:
RUN apt-get install -y ffmpeg
```

### ⚠️ M-03 — LangGraph Sürüm Uyumu

`langgraph==0.2.59` + `langchain==0.3.12` — uyumlu ama her ikisi de hızlı değişen paketler. Production'da `requirements.txt` tam pin edilmiş (✅). Ama `cryptography>=3.1` sürüm aralığı — pip update'lerde kırılabilir.

**Çözüm:** `cryptography>=3.1,<44` olarak sınırla.

### ❌ M-04 — Remotion Servisi Deploy Edilmemiş

`video.py` Remotion render servisini çağırıyor ama servis Railway'de yok. Mevcut fix (bu session): `ready_for_review` durumuna alıyor, TTS sesi çalınabiliyor. Kalıcı çözüm:

**Seçenek A:** Remotion servisini Railway'e deploy et  
**Seçenek B:** moviepy pipeline ile tam video üret (zaten `video_assembler.py` var)  
**Seçenek C:** Remotion özelliğini kaldır, sadece TTS+slideshow yap

### ⚠️ M-05 — JSONB vs Normalize Tablo Çift Kayıt

`sgs_analyses.subjects` JSONB ve `sgs_questions` normalize tablo ikisi de kullanılıyor. Senkronizasyon riski var. Eğer `sgs_questions` güncellenir ama `sgs_analyses.subjects` güncellenmezse tutarsızlık oluşur.

**Çözüm:** Dashboard ve topic analysis her zaman `sgs_questions`'dan okusun. `sgs_analyses.subjects` sadece "ham analiz arşivi" olarak kalsın, asla dashboard kaynağı olmasın.

---

## 3. Performans Değerlendirmesi

| Endpoint               | Süre Tahmini | Not                              |
|------------------------|-------------|----------------------------------|
| SGS PDF Analiz         | 30-120 sn   | GPT-4o PDF okuma — normal        |
| Video TTS üretimi      | 20-60 sn    | Sahne başına TTS — normal        |
| Dashboard istatistik   | < 1 sn      | Direkt Supabase sorgu            |
| Chat                   | 2-10 sn     | LangGraph + GPT-4o               |

**Frontend Timeout:** `api-client.ts` → `timeout: 30000` (30 sn). PDF analiz 120 sn sürebilir → **timeout hatası riski**.

**Çözüm:** 
- SGS analyze endpoint'i background task'e al, status polling ile takip et
- Veya frontend timeout'u 180 sn yap (geçici fix)

---

## 4. Ölçeklenebilirlik

Mevcut sistem **tek kullanıcı / tek şirket** için tasarlanmış. Bu iyi — gereksiz karmaşıklıktan kaçınılmış.

Çok kullanıcılı sisteme geçilecekse:
1. IDOR koruması (G-02) mutlaka önce
2. `user_id` kolonları tüm tablolara
3. Supabase RLS politikaları
4. APScheduler → per-user zamanlamalar için farklı çözüm

---

## 5. Kod Kalitesi

- **Loglama:** `loguru` kullanılıyor, structured logging var ✅
- **Error handling:** Route'larda try/except ve HTTPException doğru ✅  
- **Type hints:** FastAPI Pydantic modelleri bazı endpoint'lerde eksik (request body dict olarak alınıyor) ⚠️
- **Test:** Hiç test yok ❌ (FAZ 4'e bakın)
- **Yorum:** Minimal, kodun kendisi konuşuyor ✅
