# AdimOS Teslim Notları

## Widget kurulumu

```html
<script src="https://adimos-production.up.railway.app/widget/chat.js" data-adimos-key="PUBLIC_KEY" async></script>
```

Önce `backend/migrations/016_publishing_queue.sql` ve `017_widget_chat.sql` Supabase SQL Editor'de uygulanmalı; ardından backend, Remotion site/bridge ve frontend deploy edilmelidir.

## Gerekli ortam değişkenleri

```text
YOUTUBE_CLIENT_ID
YOUTUBE_CLIENT_SECRET
YOUTUBE_REFRESH_TOKEN
YOUTUBE_CHANNEL_ID
INSTAGRAM_ACCESS_TOKEN
INSTAGRAM_BUSINESS_ID
FACEBOOK_PAGE_ID
INSTAGRAM_APP_SECRET
ADIMOS_WIDGET_PUBLIC_KEY
```

Mevcut eski adlar (`META_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`) geriye dönük desteklenir.

## OAuth ve platform kurulumu

### YouTube

1. Google Cloud Console'da YouTube Data API v3'ü etkinleştirin.
2. OAuth consent screen'i yapılandırın.
3. Web application OAuth client oluşturun.
4. Redirect URI olarak `https://adimos-production.up.railway.app/api/v1/oauth/youtube/callback` ekleyin.
5. Kanal sahibiyle yetkilendirip offline access refresh token alın.
6. Değerleri Railway ortam değişkenlerine ekleyin.

Varsayılan kota 10.000 birim/gün; yükleme yaklaşık 1.600 birimdir. Kod yeni upload öncesinde limiti kontrol eder.

### Instagram / Meta

1. Meta for Developers'da Business türünde uygulama oluşturun.
2. Instagram Business/Creator hesabını bir Facebook Sayfasına bağlayın.
3. Instagram Graph API ve Webhooks ürünlerini ekleyin.
4. App Review için `instagram_basic`, `instagram_content_publish`, `instagram_manage_messages` ve kullanılan webhook izinlerini talep edin.
5. Uzun ömürlü access token, Instagram Business ID ve Facebook Page ID'yi Railway'e ekleyin.
6. Token yenileme için `refresh_long_lived_token()` çağrısını süresi dolmadan planlayın.

Webhook callback:

```text
https://adimos-production.up.railway.app/api/v1/meta/webhook
```

Instagram DM yanıtı yalnızca kullanıcının mesajından sonraki 24 saat içinde gönderilir. Pencere dışındaki mesajlar panelde manuel işlem gerektirir; toplu/istenmeyen DM uygulanmamıştır.

## Bağlantı sonrası checklist

- [ ] Migration 016 ve 017 başarıyla uygulandı.
- [ ] Railway backend `/health` 200 dönüyor.
- [ ] Remotion bundle 8 composition içeriyor; `SummaryPostVideo` listede.
- [ ] Widget script'i örnek bir sayfada Shadow DOM içinde açılıyor.
- [ ] Widget mesajı `chat_sessions` ve `chat_messages` tablolarına yazılıyor.
- [ ] Onaylanan içerik `publishing_queue` tablosuna seçilen hedeflerle düşüyor.
- [ ] Scheduler 09:00/13:00/19:00 TRT, 4 saat ve günlük 3 limitini koruyor.
- [ ] YouTube test yüklemesi yalnızca yetkili test kanalında yapılıyor.
- [ ] Instagram Reels container durumu `FINISHED` olduktan sonra publish ediliyor.
- [ ] Carousel çocuk container'ları ve parent container sırası doğrulanıyor.
- [ ] `/mesajlar` yeni mesajı sayfa yenilemeden gösteriyor.
- [ ] Manuel modda widget botu cevap vermiyor.

## FAZ 0 — Acil düzeltmeler

### Yapılanlar

- Panel motivasyon akışı `select_asset()` hattında tutuldu; `recently_used` DB hatası artık fail-fast.
- Görsel seçim logu: `job`, `tema`, `aday_sayisi`, `secilen`.
- `spoken_text` TTS önceliği, `SGS → se ge se`, Whisper `language="tr"` doğrulandı.
- Remotion maliyet şekli `costs.accruedSoFar: number` olarak düzeltildi.
- 9:16/16:9 token ve aspect-aware iki sütunlu AccountCard düzeni eklendi.
- Eksik görsel kütüphanesi tamamlandı; eski duplicate Storage kayıtları idempotent kurtarıldı.

### Ölçümler

- Görsel üretimi: 7 kabul / 8 API denemesi; gerçek maliyet `$0.328`.
- Canlı başlangıç: 131/138; yeni hedef görseller: 7/7. Son durum: 140/138 (`mola=12`, `esnaf_isletme=14`; iki eski ödenmiş pending kayıt ayrıca kurtarıldı).
- Still: 1080×1920 ve 1920×1080 render geçti.
- Minimum ölçülen kontrast: 9.65:1.
- 9:16 başlık/gövde: 2/4 satır; 16:9: 1/3 satır.

### Kabul ölçütleri

- Kod ve yerel render: geçti.
- Canlı panel job doğrulaması: deploy sonrası checklist'e kaldı.

### Kalan riskler

- Değişiklikler kullanıcı talimatı gereği commit/push edilmedi; production eski kodu çalıştırır.

## FAZ 1 — Görsel genişletme

### Yapılanlar

- `SummaryPostVideo`, 1080×1350, 2×2/2×3 grid.
- Backend `/summary-post`, `publish_package.summary_post` ve race-free sosyal asset orchestration.
- Panelde Carousel / Tek Görsel sekmeleri ve indirme.

### Ölçümler

- Yerel still: 1080×1350; 6 mini kart; 3.845 byte widget ölçümünden bağımsız.
- Remotion manifest: 8 composition.

### Kabul ölçütleri

- Composition, backend ve panel build: geçti.
- Canlı URL üretimi: deploy sonrası.

### Kalan riskler

- Lambda site bundle yeniden deploy edilmeden canlı bridge `SummaryPostVideo`yu göremez.

## FAZ 2 — Onay ve yayın kuyruğu

### Yapılanlar

- `publishing_queue` migration, idempotent enqueue, platform seçimleri.
- 15 dakikalık scheduler, 4 saat aralık, günlük 3 gönderi, 3 deneme ve açık hata.
- `/publishing` paneli.

### Ölçümler

- Slot testleri: 09:00, 13:00, 19:00 TRT ve sonraki güne geçiş geçti.

### Kabul ölçütleri

- Unit test: geçti; canlı tablo testi migration sonrası.

### Kalan riskler

- Supabase SQL bağlantısı verilmediği için migration otomatik uygulanmadı.

## FAZ 3 — Web chatbot

### Yapılanlar

- Vanilla TypeScript, Shadow DOM widget; public-key doğrulama.
- Session/message/history API, KVKK bildirimi, lead istemi ve marketing filtresi.
- Backend static servis.

### Ölçümler

- Bundle: 4.606 byte raw, 2.063 byte gzip.

### Kabul ölçütleri

- Bundle, Shadow DOM ve yasak ifade testleri geçti; DB testi migration sonrası.

### Kalan riskler

- `ADIMOS_WIDGET_PUBLIC_KEY` ayarlanmadan widget 401 döner.

## FAZ 4 — Sosyal medya

### Yapılanlar

- YouTube publisher/quota ve mevcut resumable uploader adaptörü.
- Instagram Reels, carousel, single image ve token refresh istemcisi.
- Instagram DM birleşik chat kaydı ve 24 saat kontrolü.

### Ölçümler

- Reels/carousel/24 saat mock testleri geçti.

### Kabul ölçütleri

- Kod ve mock test: geçti; gerçek yayın bilerek yapılmadı.

### Kalan riskler

- OAuth, App Review ve canlı tokenlar olmadan gerçek yayın doğrulanamaz.

## FAZ 5 — Chat görünürlüğü

### Yapılanlar

- `/mesajlar`: oturum listesi, mesaj akışı, manuel yanıt, bot-manuel mod.
- Supabase Realtime INSERT subscription ve authenticated read policy.

### Ölçümler

- Frontend TypeScript: 0 hata.

### Kabul ölçütleri

- Kod/build geçti; canlı realtime migration/deploy sonrası.

### Kalan riskler

- Realtime publication migration uygulanmalıdır.

## FAZ 6 — Test sonucu

- Backend: 19 passed, 2 deprecation warning.
- Frontend: `tsc --noEmit` geçti.
- Remotion: TypeScript build geçti, 8 composition.
- Widget: build geçti, 4.606 byte raw / 2.063 byte gzip.
- Git commit/push yapılmadı.
