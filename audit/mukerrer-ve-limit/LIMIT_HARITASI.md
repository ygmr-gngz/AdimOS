# Dosya Boyutu Limit Haritası

**Tarih:** 2026-07-09

---

## Yükleme Zinciri — Katman Bazlı Limitler

| Katman | Limit | Durum | Not |
|--------|-------|-------|-----|
| **Frontend** (tarayıcı) | — | Doğrulama YOK | `<input type="file">` limitsiz; sunucu hatası gösterilir |
| **FastAPI** (`_MAX_UPLOAD_BYTES`) | ~~50 MB~~ → **200 MB** | ✓ Güncellendi | `backend/app/api/routes/documents.py:17` |
| **FastAPI body limit** | Sınırsız (stream) | ✓ Aktif | `await file.read()` belleğe alır; 200 MB dosya = 200 MB RAM spike |
| **Railway proxy** | ~100 MB (HTTP body) | ⚠️ Belirsiz | Railway'nin ters proxy limiti belgelenmemiş — büyük ihtimalle 100 MB |
| **Supabase Storage** | Free: 50 MB/dosya · Pro: 5 GB/dosya | ⚠️ Kontrol gerekli | Supabase dashboard → Storage → Bucket ayarları |
| **Supabase DB** (`chunks` tablo) | — | ✓ | Metin chunk'ları küçük, sorun değil |

---

## Aktif Sorun

`_MAX_UPLOAD_BYTES` 50 MB → 200 MB yapıldı.

**Kalan riskler:**
1. Railway proxy 100 MB kısıtı varsa 100-200 MB arası dosyalar 502/413 ile düşer.
   - Test: 120 MB dosya yükle, Railway loglarında HTTP 413 veya 502 ara.
2. Supabase Storage bucket'ı Free plan kullanıyorsa 50 MB/dosya sınırına çarpar.
   - Kontrol: Supabase Dashboard → Storage → `documents` bucket → Policy / Settings.

---

## Önerilen Kalıcı Çözüm (opsiyonel)

Büyük dosyalar için **imzalı URL + doğrudan Supabase'e yükleme** (backend'i bypass eder):
1. Frontend: `POST /documents/signed-upload-url` → imzalı URL al
2. Frontend: dosyayı doğrudan Supabase Storage'a PUT
3. Backend: `POST /documents/register-uploaded` → DB kaydı + indexleme başlat

Bu yapıda Railway proxy limiti aşılır, backend'de bellek spike olmaz. Gerektikçe implemente edilebilir.

---

## Değişiklik Geçmişi

| Tarih | Değişiklik |
|-------|------------|
| 2026-07-09 | Backend limit 50 MB → 200 MB |
