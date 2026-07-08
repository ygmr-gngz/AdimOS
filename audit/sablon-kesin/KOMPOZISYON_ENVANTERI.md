# Kompozisyon Envanteri

**Tarih:** 2026-07-08  
**Durum:** Aktif — eski şablon seçilemez

---

## Mevcut Kompozisyonlar (remotion/src/Root.tsx)

| ID | Tip | Format | Bileşen | Durum |
|----|-----|--------|---------|-------|
| `QuizVideo` | quiz/sgs_topic_video | 16:9 | `SplitQuizScene` | ✅ AKTİF |
| `SplitQuizVerticalDemo` | quiz | 9:16 | `SplitQuizVerticalScene` | ✅ AKTİF |
| `MotivationVideo` | motivation | 9:16 | `MotivationScene` | ✅ AKTİF |
| `InfographicVideo` | lesson/infographic | 9:16 | `InfographicCardGridScene` vb. | ✅ AKTİF |

## Render Sunucusu Seçim Mantığı (remotion/src/server/index.ts satır 107)

```typescript
const compositionId =
  storyboard.video_type === 'motivation' ? 'MotivationVideo' :
  storyboard.video_type === 'lesson'     ? 'InfographicVideo' :
  'QuizVideo'   // quiz + sgs_topic_video → SplitQuizScene
```

## Eski Pipeline Durumu

`scene_engine.py` (PIL/MoviePy) artık `generate_topic_video` endpoint'inden **çağrılmıyor**.  
`_bg_topic_video` fonksiyonu ve `build_sgs_topic_video` importları dosyada kaldı ama çağrılmıyor.  
Bir sonraki temizlikte `LEGACY_` prefix ile işaretlenip kaldırılabilir.

## SGS "Soru Çöz" Akışı (2026-07-08 sonrası)

```
SGS Akademi → "Soru Çöz" butonu
  → POST /sgs/generate-topic-video
  → QuizQuestion dönüşümü
  → video_jobs INSERT (status=pending)
  → _run_pipeline(job_id, payload)  ← video.py
  → _build_quiz_storyboard → scenes[SplitQuizScene]
  → _run_remotion_render → QuizVideo composition
  → SplitQuizScene render (beyaz zemin, çift panel, kırmızı şık)
```

## Kanıt Beklentisi (Adım 2-3)

- Yeni üretilen her işte `payload_json.type = "quiz"` ve `composition = "SplitQuizScene (QuizVideo)"` kaydı logda görünür.
- `GET /video/jobs/{job_id}` → storyboard.scenes[i].component = "SplitQuizScene"
