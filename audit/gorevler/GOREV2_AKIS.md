# GÖREV 2 — İçerik Otomasyonu İş Akışı Yeniden Yapılandırma

**Durum:** TAMAMLANDI (UI katmanı)  
**Tarih:** 2026-07-04

---

## Hedef

Video üretimini tek bir noktadan yönetmek:
- **Video Prodüksiyon** → Üretim, TTS, render, onay
- **İçerik Otomasyonu** → Shorts, Reels, görsel post; onaylanan videolar buraya aktarılır

---

## Uygulanan Değişiklikler

### `GenerateContentModal.tsx`
**Kaldırıldı:**
- "Konu Anlatım Videosu" seçeneği (`content_type: 'video'`, `backend_type: 'topic_explanation'`)
- "Soru Çözüm Videosu" seçeneği (`content_type: 'video'`, `backend_type: 'question_solution'`)
- `BACKEND_ROUTE` içinden `topic_explanation`, `question_solution`, `video` anahtarları

**Eklendi:**
- Modal açıldığında üst kısımda mavi bilgi banner'ı:
  _"Konu anlatım ve soru çözüm videoları Video Prodüksiyon'da üretilir"_ + "Git →" linki

**Kalan seçenekler:**
- YouTube Shorts
- Instagram Reel
- Instagram Görsel Post

### `automation/page.tsx`
**Kaldırıldı:**
- "Motivasyon İçeriği Oluştur" accordion bölümü
- `motivOpen`, `motivTopic`, `motivPlatform`, `motivLoading` state'leri
- `handleMotivation()` fonksiyonu
- `Sparkles`, `ChevronDown` icon import'ları

**Eklendi:**
- İçerik listesinin üstünde kalıcı banner:
  _"Konu anlatım ve soru çözüm videoları Video Prodüksiyon'da üretilir. Onaylanan videolar buraya otomatik aktarılır."_ + "Video Prodüksiyon →" linki

---

## Kalan İş (Backend/DB)

Video Prodüksiyon → İçerik Otomasyonu otomatik aktarım henüz implement edilmedi.  
Mevcut akış: Video Prodüksiyon'da "Onayla" → `video_jobs.status = 'approved'` → 
İçerik Otomasyonu'nda manuel görüntüleme.

Tam otomatik aktarım için:
1. `video_jobs` tablosuna `approval_status` alanı ekle
2. Onay anında `generated_contents` tablosuna kayıt yaz
3. İçerik Otomasyonu'nda `content_type = 'video'` satırları göster
