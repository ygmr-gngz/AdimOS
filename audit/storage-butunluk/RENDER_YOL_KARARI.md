# Render OOM — Yol Kararı (GÖREV 2)

**Tarih:** 2026-07-11  
**Durum:** Kullanıcı onayı bekleniyor

---

## Karar

| Faktör | Durum |
|--------|-------|
| chromiumOptions fix | Deploy edildi ✓ |
| Railway worker RAM | **8 GB** (zaten var) |
| Test render sonucu | Hâlâ crash — Yol A başarısız |
| **Karar** | **YOL B — Remotion Lambda** |

---

## Yol B Uygulama Durumu

---

## Yol A — Railway'de Kal (RAM artır)

**Gerekli:** Settings → Resources → RAM → 4 GB (veya üstü)

Adımlar:
1. Railway → render/worker servisi → Settings → Resources → RAM → 4 GB
2. Deploy
3. Yeni video üret (herhangi bir tip)
4. Logs: `render-done` görünüyor mu?

**Başarı kriteri:** 3 iş tipinin hepsi (soru çözümü, motivasyon, konu anlatımı)
canlıda uçtan uca tamamlanıyor.

**Maliyet:** ~$20-50/ay (Railway Pro, 4 GB sabit ayrılmış)

---

## Yol B — Remotion Lambda (hâlâ crash ederse)

**Tetikleyici:** RAM artırıldı + 2 iş günü sonra hâlâ OOM.

**Maliyet:** ~$2/ay (günde 10 video @ 3.5 GB-s/video × $0.0000166667)

**Uygulama adımları:**
1. AWS IAM kullanıcı + Remotion Lambda izinleri
2. `npx remotion lambda sites create` → S3 bundle
3. `npx remotion lambda functions deploy` → Lambda fonksiyon
4. Backend: `_run_remotion_render()` → `renderMediaOnLambda()` çağrısına çevir
5. Çıktı: S3 pre-signed URL → Supabase Storage'a aktar
6. Watchdog timeout güncelle (Lambda cold start farklı)
7. Railway Remotion servisini geçiş doğrulanana kadar DURDURMA

**Geliştirme eforu:** ~1-2 gün  
**Onay gerekiyor:** Yol B başlamadan önce kullanıcı onayı al.

---

## Karar Kuralı

```
RAM artırıldı?
├─ HAYIR → önce artır (Railway Settings), Görev 1'e devam et
├─ EVET + hâlâ crash → Yol B başlat
└─ EVET + düzeldi → Yol A yeterli, izle
```

**Şu an ne yapmalısın:**
Railway → render worker → Settings → Resources → RAM değerini bana söyle.
