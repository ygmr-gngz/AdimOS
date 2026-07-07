# Polling Ölçüm Raporu

**Tarih:** 2026-07-07  
**Sprint:** Render Arızası Stabilizasyon v2  
**Hedef:** Tüm polling envanteri + öncesi/sonrası istek sayısı ölçümleri

---

## Tam Polling Envanteri

| Endpoint | Dosya | Yöntem | Aralık (öncesi) | Aralık (sonrası) | Koşul | Görünmez sekme | Durum |
|----------|-------|--------|-----------------|-------------------|-------|----------------|-------|
| `GET /api/v1/content` | `automation/page.tsx` | `recursive setTimeout` | ~12s (timer zinciri) | **30s** | sadece `generating` item varken | **DURDURULUR** | ✅ DÜZELTİLDİ |
| `GET /api/v1/video/jobs` | `video/page.tsx` | `setInterval` | 10s | **10s** (değişmedi) | sadece aktif job varken; max 20 dk | **ATLANIR** | ✅ DÜZELTİLDİ |
| `GET /api/v1/notifications/unread-count` | `Header.tsx` | `setInterval` | 60s | 60s | her zaman | cleanup ✓ | ✅ SORUN YOK |
| `GET /api/v1/documents` (reindex) | `useDocuments.ts` | tek `setTimeout(10s)` | tek seferlik | tek seferlik | reindex sonrası | — | ✅ SORUN YOK |

---

## Öncesi — Polling Fırtınası Analizi

### `automation/page.tsx` problemi (timer zinciri birikimi)

**Eski kod:**
```typescript
// Her handleX fonksiyonu kendi timer'ını başlatıyordu:
if (pollRef.current) clearTimeout(pollRef.current)
pollRef.current = setTimeout(fetchContent, 5000)  // 5 saniye

// fetchContent içinde:
pollRef.current = setTimeout(fetchContent, 12000)  // 12 saniye
```

**Problem:** Kullanıcı hızlı action yapınca (approve → reject → retry) her action yeni bir 5s timer başlatıyordu. Eski timer iptal edilmeden yeni chain başlıyordu.

**Tahmini istek oranı (öncesi):**
- Sessiz durumda: 5 req/dakika (12s aralık)
- 3 action/dakika durumunda: ~15 req/dakika (5s öncül timer + zincirleme)
- Sekme arka planda: istek **DEVAM EDİYORDU** (temizlik yoktu)

### `video/page.tsx` problemi (visibilitychange eksikti)

**Eski kod:**
```typescript
setInterval(async () => {
  // document.hidden kontrolü yoktu
  // Her 10 saniyede bir istek → sekme arka plandayken de
  const data = await videoService.listJobs(...)
}, 10000)
```

**Tahmini istek oranı (öncesi, arka plan sekmede):**
- 20 dakika boyunca arka planda: **120 istek** (10s × 120 = 20 dk)

---

## Sonrası — Düzeltilmiş Davranış

### `automation/page.tsx` (generation counter + self-cancel)

```typescript
const generationRef = useRef(0)

const fetchContent = useCallback(async () => {
  if (pollRef.current) { clearTimeout(pollRef.current); pollRef.current = null }
  const gen = ++generationRef.current  // eski çağrıların yanıtını yok say
  try {
    const data = await automationService.listContent(...)
    if (gen !== generationRef.current) return  // stale yanıt
    const hasGenerating = data.some(c => c.status === 'generating')
    if (hasGenerating) {
      pollRef.current = setTimeout(fetchContent, 30000)  // 30 saniye
    }
    // generating yoksa timer KURULMAZ → polling tamamen durur
  }
}, [filter])

// visibilitychange:
document.hidden → clearTimeout (polling durur)
tab öne gelince → fetchContent() (hemen bir istek, sonra gerekirse 30s)
```

**Tahmini istek oranı (sonrası):**
- Generating item yokken: **0 req/dakika**
- Generating item varken, sekme önde: **2 req/dakika** (30s aralık)
- Generating item varken, sekme arka planda: **0 req/dakika**

### `video/page.tsx` (hidden skip + visibilitychange)

```typescript
setInterval(async () => {
  if (document.hidden) return  // ← YENİ

  const hasActive = jobsRef.current.some(j => ACTIVE_STATUSES.includes(j.status))
  if (!hasActive) return  // aktif job yoksa atla
  ...
}, 10000)

// visibilitychange:
useEffect(() => {
  const onVisibility = () => {
    if (!document.hidden) loadJobs()  // öne gelince hemen çek
  }
  document.addEventListener('visibilitychange', onVisibility)
  return () => document.removeEventListener('visibilitychange', onVisibility)
}, [])
```

**Tahmini istek oranı (sonrası):**
- Aktif job yokken: **0 req/dakika**
- Aktif job varken, sekme önde: **6 req/dakika** (10s aralık)
- Aktif job varken, sekme arka planda: **0 req/dakika**

---

## Önce / Sonra Karşılaştırması

### En kötü durum: 2 sekme açık (automation + video), her ikisi arka planda, her ikisinde aktif iş var

| Endpoint | Öncesi (req/dk) | Sonrası (req/dk) | Azalma |
|----------|----------------|------------------|--------|
| `/content` (automation) | ~5–15 | **0** (sekme gizli) | **%100** |
| `/video/jobs` | ~6 | **0** (sekme gizli) | **%100** |
| `/notifications/unread-count` | 1 | 1 | — (değişmedi, normal) |
| **Toplam** | **12–22** | **1** | **~%94 azalma** |

### Sekme önde, hiç aktif iş yok

| Endpoint | Öncesi (req/dk) | Sonrası (req/dk) | Azalma |
|----------|----------------|------------------|--------|
| `/content` | 5 | **0** (timer kurulmaz) | **%100** |
| `/video/jobs` | 6 | **0** (hasActive=false, skip) | **%100** |

### Sekme önde, aktif iş var

| Endpoint | Öncesi (req/dk) | Sonrası (req/dk) | Not |
|----------|----------------|------------------|-----|
| `/content` | ~5–15 | **2** | 30s aralık, stale-free |
| `/video/jobs` | 6 | **6** | 10s aralık (hızlı geri bildirim) |

---

## Kalan Risk

- `video/page.tsx` 10s aralık hâlâ yüksek gelebilir; render pipeline 3–15 dakika sürdüğünden 10s pratik bir değer. Gerekirse 15s'e çıkarılabilir.
- `Header.tsx` 60s unread-count polling: cleanup ✓, sessiz hata ✓ — değiştirilmedi.
- Backend `Cache-Control` / ETag başlıkları eklenmedi (düşük öncelik — sunucu taraflı iyileştirme, sprintin dışında bırakıldı).
