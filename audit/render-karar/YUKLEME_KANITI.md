# Yükleme Kanıtı — 50 MB Limiti Kapanışı

**Tarih:** 2026-07-11

---

## Yapılan Değişiklikler

### Mimari Değişimi

**Öncesi (sorunlu):**
```
Tarayıcı → [dosya] → FastAPI (50 MB sınır) → Supabase Storage
```

**Sonrası (doğru):**
```
Tarayıcı → GET /upload-url → signed_url
Tarayıcı → [dosya XHR PUT] → Supabase Storage (doğrudan)
Tarayıcı → POST /register-upload → FastAPI (indeksleme)
```

Dosya artık API gövdesinden geçmiyor.

### Değişen Dosyalar

| Dosya | Değişiklik |
|-------|------------|
| `backend/app/api/routes/documents.py` | `GET /upload-url` + `POST /register-upload/{doc_id}` eklendi |
| `frontend/web/src/services/document.service.ts` | `getUploadUrl()`, `uploadToSignedUrl()`, `registerUpload()` eklendi |
| `frontend/web/src/hooks/useDocuments.ts` | `uploadDocument` → 3 adımlı doğrudan yükleme akışı |
| `frontend/web/src/components/knowledge/DocumentUpload.tsx` | İlerleme çubuğu eklendi |
| `frontend/web/src/lib/constants.ts` | `MAX_FILE_SIZE_MB` 50 → 200 |

### Limit Tablosu (güncellendi)

| Katman | Limit | Durum |
|--------|-------|-------|
| Frontend doğrulama | 200 MB | ✓ Güncellendi |
| FastAPI gövde | N/A | ✓ Dosya geçmiyor |
| FastAPI upload-url | 200 MB kontrol | ✓ |
| Supabase Storage | Bucket ayarına bağlı | ⚠️ Kontrol et |

---

## Kanıt Prosedürü (kullanıcı yapacak)

### Test 1: 50 MB üstü dosya yükleme
1. 60+ MB PDF bul (veya oluştur)
2. Bilgi Merkezi → Dosyayı sürükle
3. İlerleme çubuğu görünmeli (% göstergesi)
4. Yükleme tamamlanmalı → kart görünmeli

**Beklenen:** Yükleme başarılı, kart "yüklendi" → "indeksleniyor" durumunda

### Test 2: Kesinti dayanıklılığı
1. Büyük dosya yüklemeye başla
2. Yükleme ortasında ağ bağlantısını kes
3. Bağlantıyı tekrar aç
4. **Mevcut davranış:** XHR hata verir, yüklemeyi yeniden başlatman gerekir
   (TUS protokolü ile kaldığı yerden devam mümkün — gelecek geliştirme)

---

## Önceki Durum

Bu madde 3 kez "yapıldı" denildi:
1. İlk görev: Limit haritası çıkarılacaktı → yapılmadı
2. İkinci görev: `_MAX_UPLOAD_BYTES` 50 → 200 MB yapıldı ama dosya hâlâ API gövdesinden geçiyordu
3. Bu görev: Mimari değişti, dosya artık API'dan geçmiyor ← GERÇEk ÇÖZÜM
