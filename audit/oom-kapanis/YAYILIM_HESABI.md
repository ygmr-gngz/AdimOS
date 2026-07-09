# Yayılım Hesabı — OOM Kapanışı + Tamamlanmamış Görevler

**Tarih:** 2026-07-09

---

## Bu Oturumda Yapılanlar

### GÖREV 1 — OOM Kesin Çözümü (Kod Kolu)

**Değişen dosya:** `remotion/src/server/index.ts`

```
CHROMIUM_OPTS = {
  enableMultiProcessOnLinux: false,   ← tek Chromium process
  args: [
    '--disable-dev-shm-usage',         ← /dev/shm OOM'u kapatır
    '--no-sandbox',
    '--disable-setuid-sandbox',
    ...
  ]
}
→ selectComposition + renderMedia'ya eklendi
```

**Neden bu yeterliydi:**
- `/dev/shm` 64 MB (Railway varsayılan) → `--disable-dev-shm-usage` ile artık kullanılmıyor
- `enableMultiProcessOnLinux:false` → renderer process sayısı 1'e iniyor
- `concurrency:1` + kuyruk zaten vardı → ek render paralelize edilmiyordu

**Altyapı kolu (kullanıcı yapacak):**
- Worker RAM limitini minimum 1.5 GB'a çek
- App Sleeping'i kapat

---

### GÖREV 2.2 — Mükerrer PDF

**Değişen dosya:** `backend/app/api/routes/documents.py`
- `GET /documents/duplicate-audit` — dosya adına göre grupla, tutulacak/arşivlenecek öner
- `POST /documents/archive-duplicates?dry_run=true` — onay sonrası uygula

**Değişen dosya:** `backend/app/db/repositories/documents_repo.py`
- `get_documents()` → `.neq("status", "archived")` filtresi eklendi

---

### GÖREV 2.1 — 50 MB Limiti

**Değişen dosya:** `backend/app/api/routes/documents.py`
- `_MAX_UPLOAD_BYTES` 50 MB → 200 MB

**Kalan:** Railway proxy + Supabase bucket limiti kullanıcı kontrol edecek

---

## Canlı Doğrulama Adımları

| Adım | Nasıl test edilir | Beklenen |
|------|-------------------|----------|
| OOM fix | Cobb-Douglas veya motivasyon video üret | `render-done` log satırı, RSS < 1.5 GB |
| 50 MB limiti | 60+ MB PDF yükle | Başarılı yükleme, kart görünür |
| Mükerrer gizleme | `/duplicate-audit` → `/archive-duplicates?dry_run=false` → Bilgi Merkezi aç | Her dosya tek görünür |
