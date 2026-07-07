# Çift Üretim Test Planı

**Tarih:** 2026-07-07  
**Durum:** KOD CANLI — CANLI TEST BEKLİYOR

---

## Uçtan Uca Test Adımları

### Test 1: Soru Çözümü (Mevcut Akış)

1. SGS Akademi sayfasında herhangi bir konuya git (örn. "Kıdem Tazminatı")
2. **"Soru Çöz"** butonuna tıkla
3. Beklenen: Video Prodüksiyon sayfasına yönlendir, pending job var
4. Kanıt: `GET /api/v1/video/jobs` → yeni job `type=lesson, status=pending`

### Test 2: Konu Anlatımı (Yeni Akış)

1. Aynı konuya git
2. **"Kaynak İçerik"** sekmesine tıkla → kaynak parça sayısını kontrol et
   - Kaynak yoksa: amber uyarı görünmeli (üretme izni yok)
   - Kaynak varsa: yeşil badge + doküman listesi
3. **"Konu Anlat"** butonuna tıkla
4. Beklenen: 
   - Kaynak yoksa: toast hata "PDF yükleyin" mesajı (422)
   - Kaynak varsa: Video Prodüksiyon'a yönlendirme, job oluştu
5. Kanıt: `GET /api/v1/video/jobs` → yeni job `payload_json.production_type=konu_anlatimi`

### Test 3: Halüsinasyon Koruması

```
POST /api/v1/sgs/topics/BilinmeyenKonu/generate-konu-anlatimi
```

Beklenen: 422 — "kaynak içerik bulunamadı"

---

## Başarı Kriterleri

| Kriter | Test | Durum |
|--------|------|-------|
| İki buton konu satırında görünüyor | UI | ⏳ |
| "Soru Çöz" mevcut akışla çalışıyor | Test 1 | ⏳ |
| "Konu Anlat" kaynak chunk gerektiriyor | Test 2 | ⏳ |
| Kaynak yoksa 422 dönüyor | Test 3 | ⏳ |
| Job `production_type=konu_anlatimi` kaydediliyor | DB | ⏳ |
| Kaynak İçerik sekmesi doğru bilgi gösteriyor | UI | ⏳ |

---

## Kapsam / Fırsat Görünümü (Sonraki Sprint)

Video Prodüksiyon sayfasında her konu için 2 rozet:
- 🎯 Soru Çözümü: var / yok
- 📖 Konu Anlatımı: var / yok

Varsayılan sıralama: "çok soru çıkmış ama konu anlatımı videosu yok" konular öne.
Bu UI değişikliği bir sonraki sprint'te.
