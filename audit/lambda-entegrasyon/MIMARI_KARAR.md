# Lambda Entegrasyonu — Mimari Karar

**Tarih:** 2026-07-12  
**Durum:** Uygulandı

---

## Seçilen Yaklaşım: Lambda Bridge (Node.js) — Mevcut HTTP Arayüzü Korunur

```
Frontend → Backend (FastAPI) → Lambda Bridge (Node.js/Railway)
                                      ↓ renderMediaOnLambda
                               AWS Lambda (Chromium, paralel)
                                      ↓ S3 çıktı
                         Lambda Bridge (S3 indir → Supabase yükle)
                                      ↓ /video/render-callback
                             Backend (FastAPI) → DB güncelle → Frontend
```

### Neden bu yaklaşım?

| Seçenek | Değerlendirme |
|---------|---------------|
| Lambda Bridge (Node.js) | ✅ Backend sıfır değişiklik; Remotion SDK zaten Node.js |
| Python boto3 Lambda invoke | ❌ Remotion resmi client'ı yok; ham Lambda invoke kırılgan |
| FastAPI'den doğrudan çağrı | ❌ Python ekosisteminde `getRenderProgress` polling karmaşık |

---

## Kritik Tasarım Kararları

### 1. framesPerLambda — Dinamik Hesap

```
MAX_CONCURRENT_LAMBDAS = 8  (env, kota artınca 200 yap — kod değişmez)
totalFrames = storyboard.scenes[].duration_seconds × 30 fps
framesPerLambda = max(20, ceil(totalFrames / MAX_CONCURRENT))
```

**25 dk video örneği (kota=8):**
- 25 dk × 60s × 30fps = 45.000 kare
- framesPerLambda = ceil(45000 / 8) = 5625
- Her Lambda ~94s (5625 / 30fps / 2 render hızı) ≤ 900s timeout ✓

**Kota onayı sonrası:** sadece `MAX_CONCURRENT_LAMBDAS=200` yap → framesPerLambda=225, paralel hız artar.

### 2. Uzun Video Stratejisi (Kota Onayı Öncesi)

Segmentasyon **gerekmez**. framesPerLambda hesabı 8 Lambda ile dahi 25 dk videoyu
Lambda timeout'u (900s) aşmadan render eder. Açıklama: 5625 kare / (30fps × 2x render hızı) ≈ 94s/Lambda.

Segmentasyon yalnızca Lambda timeout'u aşılırsa gündeme gelir.

### 3. Günlük Maliyet Guardrail

`DAILY_COST_LIMIT_USD=5.0` env ile yapılandırılır. Aşılınca `/render 429` döner,
render durur, log çıkar. Limit artırmak için env değiştir.

### 4. Rate Exceeded Retry

`renderMediaOnLambda` "rate exceeded" hatası verirse:
- framesPerLambda × 2 (daha az Lambda, daha az paralel istek)
- Bir kez yeniden dene

### 5. Progress Callback

Her 10%'de `POST /video/render-callback { status:'rendering', progress_pct: X }` gönderilir.
Backend bu callback'i alıp `render_progress_pct` kolonunu güncellerse frontend yüzde gösterebilir
(isteğe bağlı iyileştirme — mevcut sistem olmadan da çalışır).

---

## Env Değişkenleri (Railway — Remotion Servisi)

| Değişken | Değer |
|----------|-------|
| `REMOTION_LAMBDA_FUNCTION_NAME` | `remotion-render-4-0-488-...` |
| `REMOTION_SERVE_URL` | `https://remotionlambda-eucentral1-bc2ioanhxy.s3...` |
| `REMOTION_AWS_ACCESS_KEY_ID` | ✅ eklendi |
| `REMOTION_AWS_SECRET_ACCESS_KEY` | ✅ eklendi |
| `REMOTION_AWS_REGION` | `eu-central-1` ✅ eklendi |
| `MAX_CONCURRENT_LAMBDAS` | `8` (kota artınca `200` yap) |
| `DAILY_COST_LIMIT_USD` | `5.0` |
