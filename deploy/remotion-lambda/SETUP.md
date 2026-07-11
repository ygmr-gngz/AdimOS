# Remotion Lambda Kurulum Rehberi

**Tahmini süre:** 30-45 dakika  
**Maliyet:** AWS Free Tier kapsamında ilk 12 ay bedava (sonrası ~$1-5/ay)

---

## Ön Gereksinimler

- Node.js 18+ (yerel bilgisayarda)
- `remotion/` klasöründe `npm install` yapılmış olmalı

---

## BÖLÜM 1 — AWS Hesabı Oluştur (hesabın yoksa)

1. `https://aws.amazon.com` → "Create an AWS Account"
2. E-posta, şifre, hesap adı ("AdimOS")
3. Kişisel hesap seç → kredi kartı bilgisi (Free Tier'da ücret alınmaz)
4. Telefon doğrulama
5. **Free Plan (Basic)** seç

---

## BÖLÜM 2 — IAM Kullanıcı Oluştur

1. AWS Console → arama: "IAM" → **IAM**
2. Sol menü: **Users** → **Create user**
3. Kullanıcı adı: `remotion-adimos`
4. **Next** → "Attach policies directly"
5. **Create policy** (yeni sekme açılır):
   - JSON sekmesine geç
   - `deploy/remotion-lambda/iam-policy.json` içeriğini yapıştır
   - **Next** → Policy name: `RemotionAdimOSPolicy`
   - **Create policy** → sekmeyi kapat
6. Geri dön, sayfayı yenile → `RemotionAdimOSPolicy` seç
7. **Create user**

### Access Key Oluştur

1. IAM → Users → `remotion-adimos` → **Security credentials**
2. **Create access key** → "Application running outside AWS"
3. **Access Key ID** ve **Secret Access Key**'i kaydet (bir daha göremezsin!)

---

## BÖLÜM 3 — Yerel Ortam Değişkenleri

Terminalde ayarla (geçici, sadece aşağıdaki komutlar için):

```bash
# Windows PowerShell:
$env:AWS_ACCESS_KEY_ID = "AKIAXXXXXXXXXXXXXXXX"
$env:AWS_SECRET_ACCESS_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:AWS_REGION = "eu-central-1"

# Linux/Mac:
export AWS_ACCESS_KEY_ID="AKIAXXXXXXXXXXXXXXXX"
export AWS_SECRET_ACCESS_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export AWS_REGION="eu-central-1"
```

---

## BÖLÜM 4 — Lambda Fonksiyon Dağıt

```bash
cd remotion
npm install

# Lambda fonksiyon oluştur (Remotion'un hazır container image'ı kullanılır)
npx remotion lambda functions deploy \
  --memory=3072 \
  --timeout=240 \
  --region=eu-central-1
```

**Çıktıdan not al:**
```
Function deployed: remotion-render-4-0-272-mem3072mb-disk2048mb-240sec
```
→ Bu değer `REMOTION_LAMBDA_FUNCTION_NAME`

---

## BÖLÜM 5 — Bundle'ı S3'e Yükle (Site)

```bash
cd remotion

npx remotion lambda sites create \
  --site-name=adimos-remotion \
  --region=eu-central-1 \
  src/index.ts
```

**Çıktıdan not al:**
```
Site URL: https://remotionlambda-XXXXXXXXXX.s3.eu-central-1.amazonaws.com/sites/adimos-remotion/index.html
```
→ Bu değer `REMOTION_SERVE_URL`

---

## BÖLÜM 6 — Railway Ortam Değişkenleri

Railway → Remotion servisi → **Variables** → şunları ekle:

| Değişken | Değer |
|----------|-------|
| `REMOTION_LAMBDA_FUNCTION_NAME` | `remotion-render-4-0-272-...` (Bölüm 4 çıktısı) |
| `REMOTION_LAMBDA_REGION` | `eu-central-1` |
| `REMOTION_SERVE_URL` | `https://remotionlambda-...` (Bölüm 5 çıktısı) |
| `AWS_ACCESS_KEY_ID` | IAM kullanıcı access key |
| `AWS_SECRET_ACCESS_KEY` | IAM kullanıcı secret key |

---

## BÖLÜM 7 — Railway Remotion Servis RAM'ini Düşür

Artık Chromium yok → 256 MB yeterli → maliyet düşer.

Railway → Remotion servisi → **Settings** → **Resources** → RAM → **512 MB**

---

## BÖLÜM 8 — Deploy & Test

1. Railway → Remotion servisi → **Deploy** tetikle
2. Logs'ta şunu gör:
   ```
   [lambda] Lambda Bridge başlıyor PORT=3001
   [lambda] function=remotion-render-4-0-272-...
   [lambda] serveUrl=(ayarlı)
   ```
3. Health check: `GET https://<remotion-url>/health`
   ```json
   { "lambda_ready": true, "lambda_function": "remotion-render-...", ... }
   ```
4. Yeni video üret (herhangi bir tip)
5. Logs'ta şunu gör:
   ```
   [lambda] renderMediaOnLambda başlıyor: QuizVideo
   [lambda] Lambda render başlatıldı: renderId=xxx bucket=remotionlambda-...
   [lambda] job=xxx ilerleme=10%
   ...
   [lambda] render tamam (90s): renders/xxx/out.mp4
   [lambda] Supabase'e yüklendi (15.3 MB): https://...
   ```

---

## BÖLÜM 9 — Başarı Kriterleri

- [ ] `lambda_ready: true` health check'te görünüyor
- [ ] Soru çözümü videosu uçtan uca tamamlanıyor
- [ ] Motivasyon videosu uçtan uca tamamlanıyor
- [ ] Konu anlatımı videosu uçtan uca tamamlanıyor
- [ ] Railway watchdog hiçbir iş için tetiklenmiyor
- [ ] Railway Remotion servis RAM 512 MB'a düşürüldü

---

## Olası Sorunlar

### "Lambda fonksiyon bulunamadı"
- `REMOTION_LAMBDA_FUNCTION_NAME` değeri tam olarak kopyalandı mı?
- Aynı region'da mı? (`REMOTION_LAMBDA_REGION` = `eu-central-1`)

### "S3 object not found" (download hatası)
- `privacy: 'private'` ayarındaki S3 nesnesini indirmeye çalışıyoruz
- IAM user'ın S3 GetObject izni var mı? (`iam-policy.json` doğru uygulandı mı?)

### "serveUrl (eksik)" log mesajı
- `REMOTION_SERVE_URL` Railway'e eklendi mi?
- `sites create` komutu başarıyla tamamlandı mı?

### Render çok yavaş
- `framesPerLambda: 40` azalt (ör. `20`) → daha fazla paralel Lambda → daha hızlı ama biraz daha pahalı
- Lambda memory'yi artır: `functions deploy --memory=5120`

---

## Maliyet Özeti

| Bileşen | Maliyet |
|---------|---------|
| Lambda işlem (3 GB, ~2 dk/video) | ~$0.01/video |
| S3 site storage (~50 MB bundle) | ~$0.001/ay |
| S3 çıktı (geçici, hemen Supabase'e taşınır) | Eser miktarda |
| **Railway Remotion servis (512 MB)** | ~$5/ay (8 GB'dan düşürüldü) |
| **Toplam (ayda 50 video)** | **~$5.50/ay** (önceki: ~$40/ay + crash) |
