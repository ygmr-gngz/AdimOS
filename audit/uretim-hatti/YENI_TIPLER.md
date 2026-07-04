# Yeni Video Tipleri — Motivasyon ve Görsel Post

**Tarih:** 2026-07-05  
**Etkilenen Bileşenler:** Video Prodüksiyon wizard, video pipeline  
**Durum:** ✅ Tamamlandı

---

## Motivasyon Videosu (`motivation`)

### Özellikler
- **Süre:** 15-30 saniye
- **Format:** 9:16 dikey
- **Yöntem:** Standart pipeline (TTS + Remotion)
- **Sahne üretimi:** `generate_motivation_storyboard(topic)` — kinetik tipografi

### Wizard Akışı
1. Konu girişi (ders adı gerekmez)
2. Format seçimi (9:16 ön seçili)
3. Özet ve onay

## Görsel Post — İnfografik (`infographic`)

### Özellikler
- **Format:** 9:16 dikey, statik görsel
- **Yöntem:** Remotion YOK — anında üretim
- **İçerik:** Bilgi Merkezi RAG + GPT-4o-mini
- **Sonuç:** `ready_for_review` durumu (render bekleme yok)

### Şablon Seçenekleri

| Şablon | Bileşen | Kullanım |
|--------|---------|----------|
| `card_grid` | `InfographicCardGridScene` | Kategorilere ayrılmış bilgi kartları |
| `comparison` | `InfographicComparisonScene` | İki kavramı karşılaştır |
| `process` | `InfographicProcessScene` | Adım adım süreç |

### Wizard Akışı
1. Konu girişi + şablon seçimi
2. ~~Format Seçimi~~ (atlanır — her zaman 9:16)
3. Özet ve onay

### Backend Akışı
```
POST /video/create {type: "infographic", topic, infographic_template}
  → _run_pipeline_inner()
  → generate_infographic_storyboard(topic, template)  ← Bilgi Merkezi RAG
  → storyboard kaydedilir
  → status = "ready_for_review"  ← Anında hazır
```

## Etkilenen Dosyalar

- `frontend/web/src/services/video.service.ts`
- `frontend/web/src/app/video/page.tsx`
- `backend/app/api/routes/video.py`
- `backend/app/modules/content/infographic_generator.py`
- `infrastructure/supabase/migrations/009_video_pipeline_v2.sql`
