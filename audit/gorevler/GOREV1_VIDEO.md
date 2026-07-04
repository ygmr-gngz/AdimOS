# GÖREV 1 — Takılı Video İşleri ve Frontend Polling Düzeltmeleri

**Durum:** TAMAMLANDI  
**Tarih:** 2026-07-04

---

## Sorunlar

### 1. Takılı Backend İşleri
- `5597a702` — 7000+ dakika `rendering` durumunda kaldı (TTS veya Remotion sessiz hata)
- `87415ddf` — Remotion Railway servisi 502 döndürdü, iş takılı kaldı
- `afa9f379` — Remotion 502, `ready_for_review` durumunda sıkıştı

### 2. TTS 429 Hatası
OpenAI kota sınırı aşıldığında storyboard üretimi başarısız oluyordu ama hata mesajı belirsizdi.

### 3. Frontend Polling Closure Bug
`setInterval` callback'i içindeki `jobs` değişkeni her zaman boş array'di — React closure stale değeri yakalıyordu. `hasActive` hiç `true` olmadığından polling asla tetiklenmiyordu.

### 4. Polling Limitsizdi
Polling sonsuza kadar devam ediyordu, durum alınamadığında kullanıcıya bildirim yoktu.

### 5. Failed Durumu
`failed` statüsündeki işler kırmızı gösterilmiyordu, retry butonu yoktu.

---

## Uygulanan Düzeltmeler

### Backend — `backend/app/api/routes/video.py`
```python
_WATCHDOG_MINUTES = 30

def _watchdog_sweep(sb) -> None:
    # GET /video/jobs her çağrıldığında 30dk+ active/rendering işleri failed yap
```
- Lazy watchdog pattern: `GET /video/jobs` endpoint'i her çağrıldığında otomatik tarama
- 30 dakikadan uzun `rendering`, `tts_generating`, `scripting`, `pending` işleri → `failed`
- Hata mesajı hangi adımda takıldığını belirtir

### Backend — `backend/app/modules/sgs/storyboard.py`
- 429 / quota hatası için özel yakalama eklendi
- Kullanıcıya "OpenAI kredisi tükendi, platform.openai.com'dan ekleyin" mesajı gösterilir

### Frontend — `frontend/web/src/app/video/page.tsx`
- `jobsRef` eklendi: `setInterval` içinde her zaman güncel jobs listesi okunur
- Polling 20 dakika sonra durur → "durum alınamıyor" banner'ı gösterilir
- `failed` job kartları kırmızı kenarlıkla vurgulanır
- Her `failed` job kartında "Yeniden Dene" butonu (yeni iş oluşturma modal'ını açar)
- Polling tüm aktif işler terminal duruma geçince otomatik durur

---

## Manuel Düzeltmeler (DB)
3 takılı iş `failed` olarak güncellendi:
- `5597a702` → failed (TTS/render zaman aşımı)
- `87415ddf` → failed (Remotion 502)
- `afa9f379` → failed (Remotion 502)

---

## Kalan Riskler
- Remotion Railway servisi hâlâ kapalı — yeni video işleri `rendering` aşamasında başarısız olabilir
- OpenAI kota yetersizse TTS adımı başarısız olur, watchdog 30dk sonra yakalar
