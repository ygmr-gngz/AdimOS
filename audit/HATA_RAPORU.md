# FAZ 1 — Kritik Hata Raporu

**Tarih:** 2026-07-03  
**Durum:** 8/8 hata kapatıldı

---

## H-01 — SGS Konu/Ders Adı Karışıklığı ✅ KAPATILDI

**Önem:** Kritik  
**Etki:** Dashboard'da Türkçe, Matematik, Finansal Muhasebe soruları yanlış derse atanıyor  

**Kök Neden:**  
GPT-4o bazen konu (`topic`) olarak ders adının kendisini yazıyor (`"Matematik"`, `"Finansal Muhasebe"`). `_TOPIC_LESSON_MAP` bu değerleri anahtar olarak içermediği için `_resolve_lesson_for_topic("Matematik", "Türkçe")` fonksiyonu "Türkçe" döndürüyordu (AI subject değerini kullanıyor).

**Çözüm:** `backend/app/db/repositories/sgs_repo.py`  
Tüm 17 SGS ders adı + yaygın AI kısaltmaları `_TOPIC_LESSON_MAP`'e eklendi:
```python
"matematik": "Matematik",
"finansal muhasebe": "Finansal Muhasebe",
"muhasebe": "Finansal Muhasebe",
"hukuk": "Meslek Hukuku",
# ... 17 ders + kısaltmalar
```

**Sonraki Adım:** Deploy sonrası "Yeniden Sınıflandır" butonuna tıklanmalı.

---

## H-02 — Hukuk PDF Sorularının Parse Edilmemesi ✅ KAPATILDI

**Önem:** Yüksek  
**Etki:** Hukuk PDF'i yüklenip analiz edilse de topic analysis'te görünmüyor  

**Kök Neden:**  
Hukuk sorularında AI güven skoru < 0.6 → `ai_subject = "Belirsiz"` ataması. `parse_questions_by_ranges` fonksiyonu Belirsiz soruları `continue` ile atlıyordu.

**Çözüm:** `backend/app/db/repositories/sgs_repo.py`  
Belirsiz sorular için konu (`topic`) bazlı çözümleme eklendi:
```python
if not ai_subject or ai_subject == "Belirsiz":
    resolved = _resolve_lesson_for_topic(topic, "")
    if not resolved:
        continue
    lesson = resolved
```

---

## H-03 — PDF Tekrar Yükleme (Duplicate Entries) ✅ KAPATILDI

**Önem:** Yüksek  
**Etki:** Aynı PDF birden fazla kez analiz edilip veritabanında kopya oluşturuyordu

**Çözüm — Backend:** `backend/app/api/routes/sgs.py`  
`find_analysis_by_pdf_name()` ile dedup kontrolü:
```python
existing = find_analysis_by_pdf_name(file.filename)
if existing:
    return {**existing, "analysis_id": existing["id"], "already_exists": True}
```

**Çözüm — Frontend:** `frontend/web/src/app/academy/page.tsx`  
Upload öncesi client-side kontrol:
```javascript
if (savedAnalyses.some(a => a.pdf_name === file.name)) {
    toast('Bu PDF zaten yüklü.', { icon: 'ℹ️' })
    return
}
```

---

## H-04 — Video Render HTTP 502 Hatası ✅ KAPATILDI

**Önem:** Yüksek  
**Etki:** Video oluşturma tamamen başarısız oluyordu, kullanıcıya anlamsız hata gösteriliyordu

**Kök Neden:**  
`REMOTION_URL` Railway'de tanımlı ama Remotion servisi deploy edilmemiş → her render isteği 502 döndürüyor.

**Çözüm:** `backend/app/api/routes/video.py`  
Remotion konfigürasyon kontrolü eklendi:
```python
is_remotion_configured = (
    REMOTION_URL and "localhost" not in REMOTION_URL and "127.0.0.1" not in REMOTION_URL
)
if not is_remotion_configured:
    _set_status(job_id, "ready_for_review", {
        "error_message": "Render sunucusu bağlı değil — ses sahneleri hazır."
    })
```
TTS ses dosyaları artık video olmadan da çalınabiliyor (her sahnede audio player).

---

## H-05 — Backend Dosya Boyutu Sınırı Yok ✅ KAPATILDI

**Önem:** Yüksek  
**Etki:** Sonsuz büyüklükte dosya yüklenebilir → bellek tüketimi, Railway crash riski

**Çözüm:** `backend/app/api/routes/documents.py` ve `sgs.py`  
50 MB üst sınır eklendi (413 Request Entity Too Large):
```python
if len(content) > 50 * 1024 * 1024:
    raise HTTPException(status_code=413, detail="Dosya boyutu 50 MB sınırını aşıyor.")
```

---

## H-06 — Kullanılmayan Celery/Redis Bağımlılıkları ✅ KAPATILDI

**Önem:** Düşük  
**Etki:** `requirements.txt`'de `celery==5.4.0` ve `redis==5.2.1` var, hiçbir yerde import edilmiyor. Railway build süresi ve image boyutunu artırıyordu.

**Çözüm:** `backend/requirements.txt` — iki satır kaldırıldı.  
Görev zamanlama APScheduler ile yapılıyor (uygun).

---

## H-07 — .env.local Git'te İzleniyordu ✅ KAPATILDI

**Önem:** Orta (dosya sadece public key içerdiği için düşük risk, ama prensip ihlali)  
**Etki:** `frontend/web/.env.local` git geçmişine işlendi. Gelecekte gerçek sır içerse tarihte kalır.

**Çözüm:**  
- `.gitignore`'a `.env.local` ve `.env*.local` eklendi  
- `git rm --cached frontend/web/.env.local` ile git takibinden çıkarıldı

---

## H-08 — Raporlar Sayfası Boş Görünüyordu ✅ KAPATILDI

**Önem:** Orta  
**Etki:** CEO Agent brief'leri oluşturuluyor ama `/reports` sayfası göstermiyordu

**Çözüm:** `frontend/web/src/app/reports/page.tsx` tam yeniden yazıldı:  
- `dashboardService.getDailyBrief()` ile brief yükleniyor  
- "Şimdi Oluştur" butonu `generateBrief()` çağırıyor  
- Markdown benzeri içerik (##, ###, listeler) render ediliyor

---

## Açık Kalıplar (Sonraki Sprint)

| Kod  | Sorun                                        | Öneri                              |
|------|----------------------------------------------|------------------------------------|
| A-01 | IDOR: kullanıcı başkasının analizine erişebilir | `user_id` sahiplik kontrolü ekle |
| A-02 | Rate limiting yok — LLM spam riski          | slowapi veya nginx rate limit      |
| A-03 | Token localStorage'da XSS riski              | httpOnly cookie'ye geç            |
| A-04 | APScheduler process'e bağlı — restart riski  | cron-job.org veya Railway cron    |
| A-05 | Remotion servisi deploy edilmemiş            | Deploy et veya moviepy ile değiştir|
| A-06 | Sentry/monitoring yok                        | Sentry.io entegrasyonu             |
