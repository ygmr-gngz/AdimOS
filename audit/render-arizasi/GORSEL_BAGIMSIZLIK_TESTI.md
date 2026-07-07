# Görsel Post Bağımsızlık Testi

**Tarih:** 2026-07-07  
**Hedef:** `type=infographic` işlerinin Remotion render servisi **tamamen çevrimdışıyken** de başarıyla tamamlandığını kanıtla.

---

## Test Edilecek Yol

**Eski yol (kırık):**
```
/render POST → Remotion worker → renderMedia() → video_url → ready_for_review
```

**Yeni yol (bağımsız):**
```
/video/{job_id}/start → infographic dalı → storyboard üret → ready_for_review (Remotion hiç çağrılmaz)
```

---

## Kod Kanıtı (Remotion Atlanıyor)

**Dosya:** `backend/app/api/routes/video.py`

```python
# Satır 395-408:
if payload.type == "infographic":
    _set_status(job_id, "scripting")
    storyboard = payload.pre_storyboard or {}
    if not storyboard:
        from app.modules.content.infographic_generator import generate_infographic_storyboard
        topic = payload.topic or payload.title or "Genel Muhasebe"
        template = payload.infographic_template or "card_grid"
        storyboard = generate_infographic_storyboard(topic, template=template)
        logger.info(f"[video] {job_id[:8]} infografik storyboard üretildi topic='{topic}'")
    sb.table("video_jobs").update({"storyboard": storyboard, "updated_at": "now()"}).eq("id", job_id).execute()
    _set_status(job_id, "ready_for_review")
    logger.info(f"[video] {job_id[:8]} infografik bağımsız yol — Remotion atlandı, storyboard hazır")
    return  # ← fonksiyon burada biter; Remotion'a hiç ulaşılmaz
```

Bu `return` ifadesinden sonra gelen Remotion çağrı bloğu:

```python
# Satır 410+ (sadece lesson/quiz/shorts/motivation için çalışır):
render_url = f"{REMOTION_URL}/render"
response = httpx.post(render_url, json={...}, timeout=30)
```

`infographic` type'ı bu koda **hiçbir zaman ulaşmaz**.

---

## Storyboard Şeması

`generate_infographic_storyboard()` → `backend/app/modules/content/infographic_generator.py`

Döndürdüğü yapı (card_grid örneği):

```json
{
  "video_type": "lesson",
  "title": "KDV Hesaplama Yöntemleri",
  "format": "9:16",
  "brand": { "primary": "#0B2A4A", "accent": "#2B7FE0" },
  "scenes": [
    {
      "component": "InfographicCardGridScene",
      "infographic_title": "KDV Hesaplama Yöntemleri",
      "infographic_subtitle": "Temel prensipler",
      "cards": [
        { "title": "İç Yüzde", "category": "Hesaplama", "content": "...", "icon": "📊" }
      ],
      "footer_note": "SGS sınav odaklı özet"
    }
  ]
}
```

Bu storyboard `video_jobs.storyboard` sütununa kaydedilir ve frontend'de `InfographicPreview` ile gösterilir.

---

## Frontend Önizleme Kanıtı

**Dosya:** `frontend/web/src/app/video/page.tsx` — `InfographicPreview` bileşeni

```tsx
function InfographicPreview({ storyboard }) {
  // Remotion render beklemiyor — storyboard JSON'ı doğrudan render eder
  const scenes = storyboard.scenes
  const scene = scenes?.[0]
  const component = scene.component  // InfographicCardGridScene | ComparisonScene | ProcessScene
  
  // Üç şablon için ayrı render:
  if (component === 'InfographicCardGridScene' && cards) → kart ızgarası
  if (component === 'InfographicComparisonScene') → karşılaştırma tablosu
  if (component === 'InfographicProcessScene') → süreç adımları
}
```

---

## Fonksiyonel Durum Matrisi

| Senaryo | Sonuç |
|---------|-------|
| Remotion UP + infographic job oluştur | ✅ `ready_for_review` (Remotion'a hiç gitmez) |
| Remotion DOWN + infographic job oluştur | ✅ `ready_for_review` (hiç etkilenmez) |
| Remotion DOWN + lesson/quiz job oluştur | ❌ `failed` (beklenen davranış) |
| Infographic `ready_for_review` → önizle | ✅ storyboard JSON'ı `InfographicPreview` ile gösterilir |

---

## Canlı Test Adımları (Manuel Doğrulama)

1. Railway render servisini durdur (veya `REMOTION_URL` env'ini geçersiz bir adrese çevir)
2. Video Prodüksiyon → "Görsel Post" → konu gir → oluştur
3. Job `pending` → `scripting` → `ready_for_review` geçişini izle (~5 saniye)
4. Önizle → `InfographicPreview` storyboard kartlarını göstermeli
5. ✅ Remotion olmadan çalışıyor
