# Storage Yazım Sözleşmesi Testi

**Tarih:** 2026-07-11  
**Durum:** Uygulandı — canlı test bekleniyor

---

## Sözleşme

> Bir doküman kaydı, ancak storage yazımı doğrulandıktan sonra kalıcı olur.
> Storage yazılamazsa kayıt silinir; kullanıcıya açık hata döner.

---

## Uygulanan Değişiklikler

### `upload_document` (POST /documents — eski akış)

**Öncesi:** DB kaydı oluşur → storage yazmaya çalışır → başarısız → exception → HTTP 500
ama DB KAYDI KALIRDI (hayalet kayıt).

**Sonrası:**
```python
try:
    upload_file(...)
    # Yazım doğrula: storage.list() ile dosya görünüyor mu?
    folder_files = sb.storage.from_(BUCKET).list(doc_id)
    if not any(f["name"] == expected_key for f in folder_files):
        raise Exception("storage list'te dosya görünmüyor")
except Exception as e:
    # DB kaydını sil — hayalet kayıt oluşmaz
    sb.table("documents").delete().eq("id", doc_id).execute()
    raise HTTPException(500, ...)
```

### `create_upload_url` (yeni akış)

Signed URL üretilemezse (Supabase storage hatası) DB kaydı silinir:
```python
except Exception as e:
    sb.table("documents").delete().eq("id", doc_id).execute()
    raise HTTPException(500, ...)
```

Not: Signed URL üretildi ama frontend PUT başarısız olursa kayıt hayatta kalır
(`uploaded` statüsünde, file_status=None). Bu kayıtlar `backfill-indexing` ile tespit
edilip `İndeksle` butonu aracılığıyla kurtarılabilir. Eğer dosya yoksa reindex
`file_status='kayip'` işaretler ve "Yeniden Yükle" butonu gösterilir.

---

## Normalizasyon Sözleşmesi

> Tüm storage anahtarları tek noktadan — `slugify_filename()` — geçer.
> Yükleme ve indirme AYNI fonksiyonu kullanır.

| Akış | Önce | Sonra |
|------|------|-------|
| `upload_file()` | `_clean_path()` → `slugify_filename()` | Değişmedi ✓ |
| `create_upload_url` | `_SAFE_NAME_RE.sub()` (Türkçe tutar) | `slugify_filename()` ✓ |
| `download_file()` | `_clean_path()` → `slugify_filename()` | Değişmedi ✓ |

---

## Canlı Test Prosedürü

### Test A — Normal yükleme (>50 MB, Türkçe isim)
1. "BORÇLAR HUKUKU 2026.pdf" isimli bir dosya yükle
2. Signed URL path'inde `borclar_hukuku_2026.pdf` (küçük, ASCII) görünmeli
3. Yükleme tamamlanınca indeksleme başlamalı
4. `/storage-integrity` çağrısında bu dosya "sağlam" kategorisinde olmalı

### Test B — Storage yazım sözleşmesi (bozuk senaryo)
1. Backend'den geçici olarak Supabase service_role_key'i geçersiz yap
2. `upload_document` çağır → HTTP 500 dönmeli
3. DB'de yeni kayıt OLMAMALI (hayalet yok)
4. Key'i geri al

### Test C — Kayıp dosya tespiti
1. Herhangi bir dokümanın storage kaydını Supabase dashboard'dan sil
2. `/storage-integrity` çağır → o doküman "gercek_kayip" veya "yanlis_anahtarli"
3. Kart üzerinde "Yeniden Yükle" butonu görünmeli
4. "İndeksle" butonu görünmemeli
