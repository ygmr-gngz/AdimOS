# Kapanmamış İşler — Standart Açılış Kontrolü

**Son güncelleme:** 2026-07-09  
**Kural:** Her yeni görev bu tabloyu kontrol ederek başlar; tamamlananlar ✅, taşınanlar 🔄, bloklananlar 🔴.

---

## Aktif Tablo

| # | Görev | Madde | Durum | Kanıt / Not |
|---|-------|-------|-------|-------------|
| G1-OOM | Render Worker OOM | chromiumOptions eklendi (`--disable-dev-shm-usage`, `enableMultiProcessOnLinux:false`) | 🔄 Deploy bekleniyor | `remotion/src/server/index.ts` — commit yapıldı |
| G1-OOM | Render Worker OOM | Railway RAM artışı | 🔴 Kullanıcı onayı gerekli | Worker Settings → Memory: min 1.5 GB öneriliyor |
| G1-OOM | Render Worker OOM | App Sleeping kapalı mı? | 🔴 Kullanıcı kontrol edecek | Railway → Worker → Settings → Sleep |
| G1-OOM | Cobb-Douglas + motivasyon yeniden üretimi | Deploy sonrası test | ⏳ Bekliyor | Önce deploy, sonra üret |
| G2.1 | PDF boyutu 50 MB | Backend limit 200 MB yapıldı | 🔄 Deploy bekleniyor | `documents.py:17` |
| G2.1 | PDF boyutu 50 MB | Railway proxy limiti test edilmedi | ⚠️ Belirsiz | 120 MB test dosyası yükle |
| G2.1 | PDF boyutu 50 MB | Supabase Storage bucket limiti | 🔴 Kullanıcı kontrol edecek | Dashboard → Storage → documents bucket |
| G2.2 | Mükerrer PDF | `GET /documents/duplicate-audit` endpoint | 🔄 Deploy bekleniyor | `documents.py` — commit yapıldı |
| G2.2 | Mükerrer PDF | `POST /documents/archive-duplicates?dry_run=true` | 🔄 Deploy bekleniyor | Kullanıcı dry-run çalıştıracak → onay → uygulama |
| G2.2 | Mükerrer PDF | `archived` belgeler varsayılan listede gizlendi | 🔄 Deploy bekleniyor | `documents_repo.py` `.neq("status","archived")` |

---

## Tamamlanan Maddeler (bu oturumdan önce)

| Görev | Madde | Kanıt |
|-------|-------|-------|
| SGS | Vergi Hukuku → Belirsiz normalization | commit 98d0cd7 |
| Video | Sorun 1-2-3 (pipeline, marka, NameError) | commit 8a15127 |
| Video | SplitLessonScene bileşeni | commit 4d816ee |
| Video | Konu anlatımı backend pipeline | commit dc8d30a |
| GÖREV 3+4 | İndeksleme denetimi, smoke test, chunk bağımlılığı | commit f055334 |
| Migration 010 | konu_anlatimi tip kısıtı | Supabase SQL Editor'de uygulandı |
| Smoke test | TÜM AŞAMALAR BAŞARILI | Railway terminal çıktısı |

---

## Kullanıcı Aksiyon Listesi (bu oturumdan)

1. **Railway Worker → Settings → Memory: min 1.5 GB yap**
2. **Railway Worker → Settings → Sleep: Disabled yap**
3. Deploy tamamlanınca: Cobb-Douglas ve motivasyon videolarını yeniden üret → logları kontrol et
4. `/api/v1/documents/duplicate-audit` → çıktıyı oku → onaylarsan `/archive-duplicates?dry_run=false`
5. Supabase Storage → `documents` bucket → boyut limitini kontrol et
