# Render Krizi Karar Önerisi — Yol A vs Yol B

**Tarih:** 2026-07-11  
**Durum:** Teşhis bekleniyor — aşağıdaki tablo mevcut bilgilerle hazırlandı

---

## Durum Özeti

| Faktör | Durum |
|--------|-------|
| Railway worker RAM | 8 GB (plan limiti) |
| Serverless/Sleeping | Kapalı ✓ |
| chromiumOptions fix | Deploy edildi (commit d3cfac1) |
| Test render sonucu | ⏳ Bekleniyor |

---

## Teşhis Kanalı

Worker loglarında aşağıdakilerden biri görünmeli:

**Durum A — İşler worker'a ulaşmıyor:**
```
(hiçbir render logu yok)
```
→ Sorun OOM DEĞİL. REMOTION_URL env var'ı, network, ya da backend'deki URL yanlış.

**Durum B — İşler ulaşıyor ama OOM:**
```
[remotion] render başlıyor: job=XXX
[remotion] render-start job=XXX | RSS=...MB
(sonra sessizlik, worker yeniden başlıyor)
```
→ OOM. chromiumOptions fix etkili olmamış veya başka bir neden var.

**Durum C — chromiumOptions fix çalıştı:**
```
[remotion] render başlıyor: job=XXX
[remotion] render-start job=XXX | RSS=...MB
[remotion] render-done job=XXX | RSS=...MB
```
→ Çözüldü.

---

## Yol A — Railway'de Kal

**Gerekli koşullar:**
- Worker loglarında render başlıyor ve bitiyor
- RSS zirve < 4 GB (8 GB'ın altı ama güvenli pay)

**Maliyet:**
- Railway Pro: ~$20-50/ay (sabit, 8 GB RAM her zaman ayrılmış)
- Sıfır geliştirme eforu (zaten çalışıyor)

**Risk:**
- OOM tekrarı uzun/ağır videolarda mümkün
- Kanal büyüyünce paralel render ihtiyacı doğar → tek worker yetersiz

---

## Yol B — Remotion Lambda

**Gerekli koşullar:**
- Yol A > 2 iş günü stabilize olmadıysa VEYA ölçek gereksinimi başlarsa

**Maliyet (tahmin, mevcut hacimle):**
- Lambda: $0.0000166667/GB-saniye + $0.20/1M request
- Bir 2 dakikalık video ~ 3.5 GB RAM × 120s = 420 GB-s → ~$0.007
- Günde 10 video: ~$0.07/gün = ~$2/ay
- Ciddi artış olsa bile (günde 100 video): ~$20/ay
- Railway worker'ı DURDURULURSA: ~$10-15/ay tasarruf (toplam maliyet azalır)

**Geliştirme eforu:** ~1-2 gün (Lambda kurulumu + backend adaptasyonu)

**Avantajlar:**
- OOM imkansız (Lambda RAM = belirlenen değer, asla aşılmaz)
- Paralel render bedava (her iş ayrı Lambda instance)
- Boşta maliyet = 0
- AdımOS kullanım desenine (patlamalı, aralıklı) biçilmiş kaftan

---

## ÖNERİ

**Bugün: Yol A test et** — yeni deploy + test render. `render-done` görünüyorsa A yeter.  
**2 iş günü sonra hâlâ crash: Yol B'ye geç** — geliştirme eforu minimal, maliyet düşer.

Yol B'ye geçiş kararında onay gerekiyor.

---

## Yol B Uygulama Adımları (onaylanırsa)

1. AWS hesabı + IAM kullanıcı (Remotion Lambda için gerekli izinler)
2. `npx remotion lambda sites create` — bundle'ı S3'e yükle
3. `npx remotion lambda functions deploy` — Lambda fonksiyon oluştur
4. Backend: `_run_remotion_render` → `renderMediaOnLambda` çağrısına çevir
5. Çıktı URL'si: S3 pre-signed URL → Supabase Storage'a aktar (isteğe bağlı)
6. Watchdog timeout'u Lambda profili için güncelle (Lambda cold start + render = farklı süre)
7. Railway Remotion servisi geçiş doğrulanana kadar DURDURMA; sonra emekliye ayır
