# Storage Bütünlük Denetim Tablosu

**Tarih:** (doldurulacak)  
**Durum:** GET /api/v1/documents/storage-integrity çalıştırıldıktan sonra doldurulacak

---

## Nasıl Çalıştırılır

```
GET https://<railway-backend>/api/v1/documents/storage-integrity
```

Yanıt `yanlis_anahtarli` ve `gercek_kayip` listelerini döner.

---

## Özet (doldurulacak)

| Kategori | Sayı |
|----------|------|
| Sağlam | — |
| Yanlış anahtarlı (kurtarılabilir) | — |
| Gerçek kayıp | — |
| SGS stub (normal, dosya yok) | — |
| **TOPLAM** | — |

---

## Kök Neden

`create_upload_url` endpoint'i `_SAFE_NAME_RE.sub('_', file_name)` kullanıyordu.
Python `\w` Unicode-aware olduğu için Türkçe karakterler (Ç, Ğ, Ş vb.) tutuluyordu.
Frontend bu isimle Supabase'e PUT ederken, `download_file()` aynı adı
`slugify_filename()` ile normalize edip küçük ASCII'ye dönüştürüyordu.

Sonuç: storage'da "BORÇLAR.pdf" var, indirme "borclar.pdf" arıyor → BULUNAMADI.

**Düzeltme (commit: `fix/storage-slug`):**
- `create_upload_url` artık `slugify_filename()` kullanıyor → yükleme ve indirme AYNI anahtar
- `reindex_document` dosya bulamazsa `file_status='kayip'` işaretliyor → UI'da amber uyarı
- `upload_document` (eski route): storage yazımı başarısızsa DB kaydı siliniyor
