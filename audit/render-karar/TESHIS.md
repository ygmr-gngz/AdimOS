# Render Krizi Teşhis Belgesi

**Tarih:** 2026-07-11  
**Durum:** Kanıt bekleniyor — kullanıcıdan log/metrik alınacak

---

## Teşhis Adımları (kullanıcı yapacak)

### Adım 1: Render worker'a ulaşıp ulaşmadığını test et

Railway → Remotion servisi → **Logs** sekmesi açık iken yeni bir video üret (herhangi biri).

Logda aşağıdakilerden hangisi görünüyor?

**Senaryo A — Hiçbir log yok (worker render'dan habersiz):**
- Sorun OOM değil: backend worker'a ulaşamıyor
- Kontrol: `REMOTION_URL` env var doğru mu? Backend logs'ta "remotion" hatası var mı?

**Senaryo B — Render başlıyor ama ölüyor:**
```
[remotion] render başlıyor: job=XXX
[remotion] render-start job=XXX | RSS=NNNmb
(sonra sessizlik → process yeniden başlatılıyor)
```
- chromiumOptions fix yeterli olmadı
- Seçenek: Yol B (Lambda)

**Senaryo C — Render tamamlanıyor:**
```
[remotion] render başlıyor: job=XXX
[remotion] render-start job=XXX | RSS=NNNmb
[remotion] job=XXX ilerleme=10%
...
[remotion] render-done job=XXX | RSS=NNNmb
```
- Çözüldü ✓

---

### Adım 2: Memory grafiği

Railway → Remotion servisi → **Metrics** → Memory grafiği (son 24 saat).

- Grafik render sırasında tırmanıp düşüyor mu?
- Yoksa hiç hareket yok mu (→ Senaryo A)?
- Tırmanıp dip yapıyor mu (→ crash = Senaryo B)?

---

## Bilinen Kanıtlar (bu oturumdan önce)

| Tarih | Olay |
|-------|------|
| 2026-07-09 | Smoke test: TÜM AŞAMALAR BAŞARILI (DB, GPT, TTS, Remotion /health) |
| 2026-07-09 | chromiumOptions fix deploy edildi: `--disable-dev-shm-usage`, `enableMultiProcessOnLinux:false` |
| 2026-07-10 | Watchdog: 9d8440cc, 7833005a, 08e1f28d → failed (eski işler, fix öncesi) |
| 2026-07-11 | Durum: Yeni deploy sonrası test render sonucu bilinmiyor |

---

## Sonraki Adım

Yukarıdaki logları gönder → hangi senaryoda olduğumuzu belirle → karar kapısına geç.
