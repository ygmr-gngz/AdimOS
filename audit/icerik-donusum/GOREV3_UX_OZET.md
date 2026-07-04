# GÖREV 3 — UX Sadeleştirme Özeti

> **Durum:** TAMAMLANDI (frontend)
> **Tarih:** 2026-07-04

---

## Yapılanlar

### 3.1 Dashboard Hızlı Akışlar

`frontend/web/src/app/dashboard/page.tsx` — Selamlama bölümünün altına 3 kart eklendi:

| Kart | Hedef | Dinamik Davranış |
|------|-------|-----------------|
| PDF Yükle | `/knowledge` | Statik link |
| Video Üret | `/video` | Statik link |
| Onay Bekleyen | `/video` | `pending_content > 0` ise turuncu pulse nokta + sayı |

### 3.2 Video Üretim Sihirbazı (Wizard)

`frontend/web/src/app/video/page.tsx` — `CreateVideoModal` 3 adımlı wizard'a dönüştürüldü:

**Adım 1 — İçerik Seç:**
- 3 tip: Konu Anlatımı / Soru Çözümü / Kısa İçerik (Motivasyon kaldırıldı — SGS profiliyle alakasız)
- Ders + Konu alanları (shorts için opsiyonel)
- Quiz soruları katlanabilir bölümde (varsayılan: GPT otomatik üretir)

**Adım 2 — Format Seç:**
- Görsel en/boy oran seçici (YouTube 16:9 / Reels 9:16)
- Hedef süre + akıllı varsayılan (lesson: 12dk, quiz: 8dk, shorts: 1dk)
- Gelişmiş ayarlar gizli (başlık override + yönetmen notu)

**Adım 3 — Özet & Üret:**
- Seçimlerin özet tablosu
- Üretim süresi uyarısı (3-15 dakika)
- "Video Görevi Başlat" butonu

**Kaldırılan:** `motivation` tipi wizard UI'dan silindi (backend'de tip kaydı bozulmadı — mevcut işler etkilenmez)

---

## Kalan Frontend Görevler

| Görev | Açıklama | Zorluk |
|-------|----------|--------|
| Supabase Realtime | Polling yerine gerçek zamanlı job durumu | Orta |
| Provider Health UI | Settings'de sağlayıcı durum göstergesi | Kolay (backend endpoint'i gerekli) |
| YouTube/Instagram UI | Onay sonrası yayın butonu + takvim | Orta (backend OAuth gerekli) |
| Website Chatbot gizle | Backend hazır değilse sidebar'dan kaldır | Kolay |

### Supabase Realtime Geçişi (polling azaltma)

`video/page.tsx` içinde mevcut `setInterval(10s)` yerine:

```tsx
import { createClient } from '@supabase/supabase-js'

useEffect(() => {
  const channel = supabase
    .channel('video_jobs_changes')
    .on('postgres_changes',
      { event: 'UPDATE', schema: 'public', table: 'video_jobs' },
      (payload) => {
        setJobs(prev => prev.map(j => j.id === payload.new.id ? payload.new as VideoJob : j))
      }
    )
    .subscribe()
  return () => { supabase.removeChannel(channel) }
}, [])
```

**Gereksinim:** Supabase projesinde `video_jobs` tablosunda Realtime etkinleştirilmeli.

---

## Test Notları

- Wizard adım geçişleri: Geri butonu tüm adımlarda çalışıyor
- Tip değişince format/süre otomatik güncelleniyor (lesson→12dk/16:9, shorts→1dk/9:16)
- Validation: lesson/quiz'de ders ve konu boş bırakılırsa ilerlemiyor
- Mevcut iş kartları: başarısız işlerde kırmızı kenarlık + "Yeniden Dene" butonu korundu
- Pipeline bar: scripting/tts_generating/rendering adımları görsel göstergede ✅
