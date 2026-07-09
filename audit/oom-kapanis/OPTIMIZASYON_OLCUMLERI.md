# Render Worker OOM Optimizasyon Ölçümleri

**Tarih:** 2026-07-09  
**Teşhis:** Watchdog 30 dk sonra ölü render tespit etti — Cobb-Douglas (quiz) + motivasyon her ikisi de düştü. Aynı neden = worker kendisi ölüyor.

---

## Kök Neden

Railway container'da `/dev/shm` varsayılan **64 MB**. Chromium (Remotion'ın render motoru) renderer'lar arası IPC için `/dev/shm` kullanır. Render başlayınca kısa sürede 64 MB dolar → Chromium crash → worker ölür → watchdog "30 dk rendering" fark eder.

---

## Uygulanan Kod Optimizasyonları (`remotion/src/server/index.ts`)

| # | Değişiklik | Beklenen Etki |
|---|------------|---------------|
| 1 | `--disable-dev-shm-usage` | `/dev/shm` yerine `/tmp` (disk) kullanır → OOM yok |
| 2 | `--no-sandbox` + `--disable-setuid-sandbox` | Container'da zorunlu bayraklar |
| 3 | `enableMultiProcessOnLinux: false` | Tek Chromium process — ayrı renderer process açılmaz → RAM yarıya iner |
| 4 | `--disable-background-timer-throttling` | Arka plan CPU spike'ını azaltır |
| 5 | `scale: 1` | Yanlışlıkla 2x scale render riskini kapatır |
| 6 | `gl: 'angle'` | Mesa software renderer — GPU gerektirmez |

Mevcut (önceden yapılmış):
- `concurrency: 1` — tek Chromium sekmesi, paralel render yok ✓
- Kuyruk sistemi — aynı anda tek render ✓
- Bellek log'ları (RSS/Heap) render başlangıç/orta/bitiş ✓

---

## Doğrulama Prosedürü (kullanıcı adımları)

Deploy sonrası Railway logs'ta şu satırları kontrol et:

```
[remotion] render-start job=XXX | RSS=NNNmb Heap=.../...MB
[remotion] render-50pct job=XXX | RSS=NNNmb Heap=.../...MB
[remotion] render-done job=XXX | RSS=NNNmb Heap=.../...MB
```

Beklenen: RSS (Resident Set Size) başlangıçta ~300-500 MB, render sırasında ~600-900 MB, render bitince düşer. 1.5 GB'ı aşmıyor olmalı.

---

## 1.3 Altyapı Talimatları (kullanıcı uygular)

### Railway Worker Servisi Gereken RAM
- Minimum önerilen: **1.5 GB RAM** (Remotion 4.x + Chromium headless)
- Güvenli tavan: **2 GB RAM** (stres testi için pay)
- Railway ayarı: Worker servisinin Settings → Resources → Memory Limit

### Diğer Kontroller
| Ayar | Durum | Talimat |
|------|-------|---------|
| Restart policy | Railway varsayılan = on-failure ✓ | Değiştirme |
| App Sleeping | Kapalı olmalı | Settings → Sleep → Disabled |
| Devre kesici | Backend watchdog 30 dk'da tespit ediyor ✓ | İzle |

---

## Öncesi/Sonrası Karşılaştırma (doldur)

| Ölçüm | Önce | Sonra |
|-------|------|-------|
| Motivasyon video (9:16, ~60s) | CRASH | — |
| Cobb-Douglas quiz (16:9, ~90s) | CRASH | — |
| RSS zirve | N/A (crash) | — |
| Render süresi | N/A (crash) | — |
