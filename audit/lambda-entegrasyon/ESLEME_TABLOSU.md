# Composition Eşleme Tablosu

**Kaynak:** `remotion/src/server/index.ts` — `COMPOSITION_MAP`  
**Tarih:** 2026-07-12

---

## İş Tipi → Composition ID

| video_type (backend) | format | Composition ID (Remotion) | Notlar |
|---------------------|--------|--------------------------|--------|
| `soru_cozumu` | `16:9` | `QuizVideo` | Yatay soru çözümü |
| `quiz` | `16:9` | `QuizVideo` | Alias |
| `soru_cozumu` | `9:16` | `SplitQuizVerticalDemo` | Dikey soru çözümü |
| `quiz` | `9:16` | `SplitQuizVerticalDemo` | Alias |
| `shorts` | herhangi | `SplitQuizVerticalDemo` | Kısa dikey içerik |
| `kisa_icerik` | herhangi | `SplitQuizVerticalDemo` | Alias |
| `motivasyon` | herhangi | `MotivationVideo` | |
| `motivation` | herhangi | `MotivationVideo` | İngilizce alias |
| `infografik_animasyon` | herhangi | `InfographicVideo` | |
| `infographic` | herhangi | `InfographicVideo` | Alias |
| `lesson` | herhangi | `InfographicVideo` | Alias |
| `konu_anlatimi` | herhangi | `LessonVideoDemo` | Uzun format |
| `sgs_topic_video` | herhangi | `LessonVideoDemo` | SGS konu videosu |

---

## Eşleme Mantığı

```typescript
// Önce format bazlı anahtar dene:  "soru_cozumu:9:16"
// Sonra sadece tip:                 "soru_cozumu"
// Yoksa 422 hata dön
COMPOSITION_MAP[`${videoType}:${format}`] ?? COMPOSITION_MAP[videoType] ?? null
```

---

## Bilinmeyen Tip Davranışı

Eşleme dışı `video_type` gelirse render **başlatılmaz**, backend `422` alır:

```json
{
  "error": "Bilinmeyen iş tipi: \"xxx\" (format: 16:9). Geçerli tipler: soru_cozumu, quiz, ..."
}
```

---

## Canlı Doğrulama

```
GET https://<remotion-url>/compositions
→ { "mapping": { "soru_cozumu:16:9": "QuizVideo", ... } }
```
