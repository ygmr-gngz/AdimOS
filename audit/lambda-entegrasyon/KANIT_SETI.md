# Lambda Entegrasyon — Kanıt Seti

**Tarih:** 2026-07-12  
**Durum:** Doldurulacak (canlı testlerden sonra)

---

## Gerekli Kanıtlar (Hepsi Panel Arayüzünden)

### Kısa Videolar
- [ ] **Motivasyon videosu** → tamamlandı, onay kartında oynuyor
  - Composition: `MotivationVideo`
  - Log: `render tamam (Xs): composition=MotivationVideo`
  - Video URL: *(doldur)*

- [ ] **Soru çözümü 16:9** (örn. "Cobb-Douglas") → tamamlandı
  - Composition: `QuizVideo`
  - Log: `render tamam (Xs): composition=QuizVideo`
  - Video URL: *(doldur)*

- [ ] **Soru çözümü 16:9** (örn. "Bono") → tamamlandı
  - Composition: `QuizVideo`
  - Video URL: *(doldur)*

- [ ] **Dikey kısa içerik 9:16** → tamamlandı
  - Composition: `SplitQuizVerticalDemo`
  - Video URL: *(doldur)*

### Uzun Video
- [ ] **Konu anlatımı ≥15 dk** → tamamlandı, ses ve görüntü bütün
  - Composition: `LessonVideoDemo`
  - framesPerLambda: *(log'dan al)*
  - Render süresi: *(doldur)*
  - Video URL: *(doldur)*

---

## Sistem Kontrolleri

- [ ] `GET /health` → `lambda_ready: true`
- [ ] `GET /compositions` → 5 tip doğru eşlenmiş
- [ ] Railway logs: `render tamam` — OOM/watchdog-30dk hatası yok
- [ ] Supabase `video-outputs` bucket → videolar mevcut
- [ ] `video_jobs.composition_id` DB'de dolu (migration 011 uygulandı)

---

## Eski Worker Emekliliği

- [ ] Kanıt seti tamamlandı
- [ ] Railway eski render worker → **DURDURULDU** (silinmedi)
- [ ] `backend/app/api/routes/video.py` warm-up kodu devre dışı
- [ ] `/video/render-health` → Lambda sağlığına bağlandı

---

## Başarı Kriterleri

| Kriter | Durum |
|--------|-------|
| 5 içerik tipi Lambda üzerinden çalışıyor | ⬜ |
| ≥15 dk konu anlatımı sorunsuz | ⬜ |
| Maliyet iş başına görünür | ⬜ |
| Günlük guardrail aktif | ⬜ |
| OOM/watchdog-30dk tarihe karıştı | ⬜ |
