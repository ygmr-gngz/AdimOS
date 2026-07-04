# Remotion Bağlantı Hatası — Teşhis ve Çözüm Raporu

**Tarih:** 2026-07-05  
**Etkilenen Bileşen:** `backend/app/api/routes/video.py` — Remotion render aşaması  
**Durum:** ✅ Çözüldü

---

## Kök Neden

Railway App Sleeping özelliği, Remotion servisinin boşta kalması durumunda servisi uyku moduna geçirir.
Uyku modundan çıkış **15–60 saniye** sürer. Eski implementasyonda 5 saniyelik health check timeout'u
ile bu süre içinde başarısız olunuyordu → `"Remotion sunucusuna ulaşılamıyor"` hatası.

## Uygulanan Çözümler

### 1. Warm-Up Retry Stratejisi
`_remotion_warm_up(url, job_id)` fonksiyonu eklendi:

| Deneme | Timeout | Önceki Bekleme | Açıklama |
|--------|---------|----------------|----------|
| 1.     | 15 s    | 0 s            | İlk hızlı deneme |
| 2.     | 30 s    | 5 s            | Ek bekleme |
| 3.     | 45 s    | 10 s            | Son şans |

Toplam maksimum süre: ~90 saniye

### 2. `warmup_pinging` Durumu
Pipeline'a yeni bir geçici durum eklendi. Kullanıcı arayüzünde:
- "Render servisi hazırlanıyor..." olarak gösterilir
- Hata değil — bekleme durumu
- Pipeline barında "Render" adımı aktif gösterilir

### 3. Devre Kesici (Circuit Breaker)
3 ardışık Remotion başarısızlığında devre açılır:
- Yeni iş geldiğinde Remotion'a ulaşmaya çalışmadan `ready_for_review` durumuna geçer
- `error_message`'a "render servisi geçici olarak devre dışı" notu eklenir
- TTS sesi tamamlandığında kaydedilmiş olur
- `POST /video/render-health/reset` ile devre manuel kapatılabilir

### 4. Yeni Endpointler
- `GET /video/render-health` — devre durumu ve Railway yapılandırma önerileri
- `POST /video/render-health/reset` — devreyi manuel sıfırla

## Etkilenen Dosyalar

- `backend/app/api/routes/video.py`
- `frontend/web/src/services/video.service.ts` (warmup_pinging durumu eklendi)
- `frontend/web/src/app/video/page.tsx` (UI güncellendi)
- `infrastructure/supabase/migrations/009_video_pipeline_v2.sql`

## Railway Yapılandırma Önerileri

Railway dashboard'da Remotion servisi için:
- **Sleep threshold**: minimum değere ayarla (veya devre dışı bırak)
- **Health check path**: `/health`
- **Startup timeout**: 120 saniye olarak artır
