# Kurtarma Eşleştirme Raporu

**Tarih:** (doldurulacak)  
**Durum:** POST /api/v1/documents/fix-storage-paths?dry_run=true sonucuyla doldurulacak

---

## Adım 1: Dry-Run Raporu Al

```
POST https://<railway-backend>/api/v1/documents/fix-storage-paths?dry_run=true
```

`plan` dizisi: her kayıt için `from_storage_key → to_storage_key` eşleştirmesi.

---

## Adım 2: Onay

Aşağıdaki tabloyu doldur → onay ver → dry_run=false ile uygula.

| Dosya Adı | Mevcut Key | Hedef Key | Durum |
|-----------|------------|-----------|-------|
| (dry-run sonucundan gelecek) | | | |

---

## Adım 3: Uygulama

```
POST https://<railway-backend>/api/v1/documents/fix-storage-paths?dry_run=false
```

Yanıt: `duzeltilen` ve `basarisiz` sayıları.

---

## Uygulama Sonucu (doldurulacak)

| | Sayı |
|-|------|
| Düzeltilen | — |
| Başarısız | — |
| Reindex tetiklenen | — |
