# Yükleme İz Kaydı

**Tarih:** 2026-07-07  
**Durum:** KOD HAZIR, CANLI'DA AKTİF

---

## Nasıl Çalışıyor

Her `POST /api/v1/documents` isteği artık `notifications` tablosuna iz bırakıyor:

| Alan | Değer |
|------|-------|
| `type` | `upload_attempt` |
| `title` | `Yükleme: {dosya_adı}` |
| `body` | `Aşama: tamamlandi — Başarılı` VEYA `Aşama: storage_yukleme — Hata: ...` |
| `status` | `success` / `error` |
| `priority` | `high` (hata) / `low` (başarı) |
| `details` | JSON: `{file_name, file_size, phase, error, doc_id}` |

---

## İzleme Aşamaları

| Aşama | Ne Zaman | Açıklama |
|-------|----------|----------|
| `boyut_kontrolu` | Dosya boyutu > 50 MB | Hata — istek reddedildi |
| `storage_yukleme` | Storage'a yazma başarısız | Hata — kayıt oluştu ama dosya yüklenemedi |
| `tamamlandi` | Storage'a yazma başarılı | Başarılı — arka plan işlemleri başlıyor |

---

## Yükleme Logunu Sorgulamak

```
GET /api/v1/documents/upload-log?limit=50
```

Döndürür: son 50 yükleme denemesi (başarılı + başarısız), azalan tarih sırasıyla.

---

## Sorun 1 (Borçlar Hukuku) Teşhis Adımları

1. `GET /api/v1/documents/upload-log?limit=20` → "Borçlar" içeren kayıt var mı?
   - **Varsa** → `status`, `body`, `details.error` alanlarına bak
   - **Yoksa** → istek API'ye hiç ulaşmadı (ağ/boyut/frontend hatası)

2. `GET /api/v1/documents` → Dosyanın DB'de kaydı var mı?
   - **Kayıt varsa** → `sgs_analysis_id` null → pipeline çalışmadı
   - `POST /api/v1/documents/{doc_id}/reindex` → yeniden işle

3. Başarılı yüklenen dosyalarla karşılaştır:
   - Borçlar Hukuku PDF boyutu > 50 MB ise → 413 hatası
   - PDF taranmışsa → log'da `"PDF metni çıkarılamadı"` mesajı

---

## Migration Planı: `upload_attempts` Tablosu (Gelecek Sprint)

Şu an `notifications` tablosu kullanılıyor. Bağımsız tablo için migration:

```sql
CREATE TABLE upload_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_name TEXT NOT NULL,
  file_size BIGINT,
  phase TEXT NOT NULL,
  status TEXT NOT NULL,  -- 'success' | 'error'
  error TEXT,
  doc_id UUID REFERENCES documents(id),
  source_module TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_upload_attempts_created_at ON upload_attempts(created_at DESC);
CREATE INDEX idx_upload_attempts_status ON upload_attempts(status);
```

**Avantaj:** Notifications tablosunu kirlitmez, ayrı yetkilendirme mümkün.
**Onay gerektirir** — migration çalıştırmadan önce dry-run sunulacak.
