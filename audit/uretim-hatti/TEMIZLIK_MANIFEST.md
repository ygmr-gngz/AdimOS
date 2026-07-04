# Video Pipeline Temizlik Manifestosu

**Tarih:** 2026-07-05  
**Etkilenen Bileşenler:** Video pipeline temizlik altyapısı  
**Durum:** ��� Tamamlandı

---

## Temizlik Kuralları

| Kategori | Durum | Eşik | Eylem |
|----------|-------|------|-------|
| Takılı iş | pending, scripting, tts_generating, warmup_pinging, rendering | 4+ saat güncellenmemiş | `archived` |
| Eski hata | failed | 7+ gün önce | `archived` |

## Uygulama Katmanları

### 1. Manuel Temizlik Endpointleri (`backend/app/api/routes/video.py`)

**Kuru Çalıştırma** `GET /video/cleanup/dry-run`:
- Hangi işlerin arşivleneceğini listeler
- Veritabanında değişiklik yapmaz

**Uygulama** `POST /video/cleanup/apply`:
- Kuru çalıştırmada listelenen işleri arşivler
- `status = 'archived'`, `archived_at = NOW()` set edilir
- İş kaydı silinmez — raporlama için korunur

**Envanter** `GET /video/cleanup/inventory`:
- Tüm işlerin kategori bazlı dökümü

### 2. Haftalık Otomatik Temizlik (`scheduler.py`)

Her Pazartesi 03:00'da `_task_video_cleanup()` çalışır.
Takılı ve eski başarısız işleri otomatik arşivler.

### 3. Migration (`009_video_pipeline_v2.sql`)

- `archived_at TIMESTAMPTZ` sütunu eklendi
- `infographic_template TEXT` sütunu eklendi
- `idx_video_jobs_type_status` indeksi eklendi
- `video_jobs_active` view eklendi (archived/rejected hariç)

## Frontend Değişiklikleri

- `VideoStatus` tipine `'archived'` eklendi
- Arşivlenmiş işler için gri badge
- Filtre listesinde infographic tipi

## Arşiv Politikası

Arşivlenen işler:
- DB'de kalır (denetim için)
- `video_jobs_active` view'ında görünmez
- Kendi ID'si ile `GET /video/jobs/{id}` üzerinden erişilebilir
