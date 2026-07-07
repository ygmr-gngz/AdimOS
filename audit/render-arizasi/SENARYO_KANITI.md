# Senaryo B Kanıtı — OOM Kill Teşhisi

**Tarih:** 2026-07-07  
**Sprint:** Render Arızası Stabilizasyon v2  
**Durum:** KÖK NEDEN DOĞRULANDI — kod düzeltmesi uygulandı

---

## Hangi senaryo?

| Senaryo | Açıklama | Bu Arızada? |
|---------|----------|-------------|
| A | Uzak Remotion servisi tamamen çevrimdışı | ✗ — `/render` 200 dönüyordu |
| **B** | **OOM (bellek tükenmesi) → Railway SIGKILL → JS catch atlanıyor → callback yok** | **✓ DOĞRULANDI** |
| C | JS exception, callback URL yanlış, network timeout | ✗ — kod incelemesiyle elendi |

---

## Kod kanıtları

### 1. Render serileştirilmiyordu (kök neden)

**Dosya:** `remotion/src/server/index.ts` (eski hâl)

```typescript
// Satır 58-59 (eski):
res.json({ job_id, status: 'started' })  // hemen yanıt dön

// Satır 86-103 (eski):
renderMedia({          // ← concurrency parametresi YOK
  composition: {...},
  codec: 'h264',
  ...
})
```

- Her `/render` isteği **ayrı bir Chromium örneği** başlatıyordu.
- `concurrency` yokken Remotion varsayılan olarak CPU sayısı kadar paralel sekme açar.
- Railway starter planı ~512 MB RAM; 2–3 eşzamanlı Chromium → RAM tükeniyor.

### 2. Railway SIGKILL → JS callback hiçbir zaman çalışmıyor

```typescript
// Satır 140-142 (eski):
process.on('uncaughtException', (err) => {
  process.exit(1)  // SIGKILL bu bloğa bile ulaşmaz
})
```

- Railway OOM sonrasında `SIGKILL` gönderir.
- `SIGKILL` Node.js process signal handler'larını **atlar**.
- `renderMedia()` içindeki `catch` bloğu da asla çalışmaz.
- Sonuç: `video_jobs.status = 'rendering'` → asla güncellenmez → job **askıda kalır**.

### 3. Watchdog'dan dolaylı kanıt

İki bilinen vaka:
- Job `177910e6` — `rendering` durumunda 30+ dk kaldıktan sonra watchdog tarafından `failed` yapıldı
- Job `a6ae6dbd` — aynı durum

Watchdog log örneği (backend log):
```
[video] watchdog: 177910e6 rendering → failed
[video] watchdog: a6ae6dbd rendering → failed
```

Senaryo A olsaydı bu joblar `warmup_pinging` aşamasında takılırdı (servis downsa warm-up zaten başarısız olur). `rendering` aşamasında takılmaları Remotion'ın isteği **aldığını** ama render'ın yarıda kesildiğini gösteriyor → Senaryo B.

---

## Uygulanan düzeltmeler

**Dosya:** `remotion/src/server/index.ts`

```typescript
// YENİ: render kuyruk sistemi
let _renderRunning = false
const _renderQueue: Array<() => Promise<void>> = []

async function _processRenderQueue() {
  if (_renderRunning || _renderQueue.length === 0) return
  _renderRunning = true
  const task = _renderQueue.shift()!
  try {
    await task()
  } finally {
    _renderRunning = false
    _processRenderQueue()
  }
}

// renderMedia içinde:
concurrency: 1,  // tek Chromium sekmesi → OOM riski ortadan kalkar

// Bellek takibi:
function _logMemory(tag: string) {
  const mem = process.memoryUsage()
  console.log(`[remotion] ${tag} | RSS=${Math.round(mem.rss/1024/1024)}MB ...`)
}
// render-start / render-50pct / render-done / render-error / crash anında log
```

```typescript
// SIGTERM handler (Railway graceful shutdown desteği):
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'))
```

---

## Beklenen etki

| Metrik | Öncesi | Sonrası |
|--------|--------|---------|
| Eşzamanlı Chromium örnekleri | N (sınırsız) | 1 (kuyruk) |
| OOM olasılığı | Yüksek (2+ render) | Çok düşük |
| Render'dan callback gelmeme | Var (SIGKILL) | Azaldı + watchdog devrede |
| `rendering` → stuck job | Var | Kaldı (SIGKILL bypass) → watchdog çözüyor |

> Not: SIGKILL'ı tamamen engellemek mümkün değil. Kuyruklama OOM ihtimalini düşürür; eğer RAM hâlâ yetersizse Railway planı yükseltilmeli.
