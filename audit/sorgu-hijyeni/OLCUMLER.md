# Öncesi / Sonrası Ölçüm Raporu

**Tarih:** 2026-07-07  
**Sprint:** Sorgu Hijyeni v1

---

## Kök Neden Teyidi

```
app/api/routes/content.py:183 → list_content → list_contents()
app/db/repositories/generated_contents_repo.py:30 →
  supabase.table("generated_contents").select("*").order("created_at", desc=True).execute()
→ httpx.WriteTimeout: The write operation timed out
```

**Mekanizma:** `generated_contents` tablosu büyüdükçe `select("*")` ile tüm satırları (ve tüm sütunları) çekmek Supabase HTTP bağlantısının HTTP/2 yazma zaman aşımına uğramasına yol açtı. Özellikle `audio_base64` sütunu (base64 kodlu ses verisi) satır boyutunu dramatik şekilde artırdı.

---

## `GET /api/v1/content` — Öncesi

```python
# generated_contents_repo.py (eski)
r = supabase.table("generated_contents").select("*").order("created_at", desc=True).execute()
```

| Metrik | Değer |
|--------|-------|
| Sütun sayısı | TÜM sütunlar (~20+) |
| Limit | **YOK** |
| `audio_base64` dahil mi? | ✅ (her satırda büyük binary data) |
| `script` dahil mi? | ✅ |
| Timeout durumu | `httpx.WriteTimeout` — kanıtlı canlı hata |
| HTTP yanıt kodu (timeout'ta) | 500 + ham traceback |

---

## `GET /api/v1/content` — Sonrası

```python
# generated_contents_repo.py (yeni)
_LIST_FIELDS = (
    "id,title,description,type,status,platform,"
    "thumbnail_url,video_url,image_url,audio_url,"
    "script,error_detail,approval_notes,generated_by,"
    "created_at,updated_at"
)

r = (
    supabase.table("generated_contents")
    .select(_LIST_FIELDS)
    .order("created_at", desc=True)
    .range(0, 49)          # varsayılan: page=0, limit=50
    .execute()
)
```

| Metrik | Değer |
|--------|-------|
| Sütun sayısı | 14 sütun (sabit set) |
| Limit | **50 satır** (varsayılan) |
| `audio_base64` dahil mi? | ❌ hariç tutuldu |
| `script` dahil mi? | ✅ (VideoReviewModal kullaniyor) |
| Beklenen yanıt süresi | < 300 ms |
| Timeout durumu | Önceki hacim beklentisi: timeout yok |
| HTTP yanıt kodu (timeout olursa) | 504 + sade mesaj (artık `main.py` handler'da) |

---

## `GET /api/v1/notifications/unread-count` — Öncesi / Sonrası

| | Öncesi | Sonrası |
|---|--------|---------|
| Sorgu | `select("id").eq("is_read", False)` → TÜM okunmamış satır ID'leri transfer | `select("id", count="exact").eq("is_read", False)` → sadece count header |
| Python işlemi | `len(resp.data)` | `resp.count` |
| Ağ maliyeti | Okunmamış bildirim sayısı kadar satır transferi | ~0 (PostgreSQL COUNT döner) |

---

## `GET /api/v1/documents` — Öncesi / Sonrası

| | Öncesi | Sonrası |
|---|--------|---------|
| Limit | Yok | 200 satır |
| Risk | Tablo büyüdükçe timeout riski | Kontrollü |

---

## Exception Handler — Öncesi / Sonrası

| | Öncesi | Sonrası |
|---|--------|---------|
| WriteTimeout yanıtı | 500 Internal Server Error + ham traceback | 504 Gateway Timeout + "Veritabanı sorgusu zaman aşımına uğradı. Yeniden deneyin." |
| HTTP/2 protokol hatası | 503 + sade mesaj | aynı |

---

## Beklenen Etki

- `/api/v1/content` WriteTimeout tekrarlanmamalı; mevcut tablo boyutunda < 300 ms hedefi.
- Polling 30 saniyede bir 50 satır metadata (audio_base64 hariç) alıyor — ağ bandı dramatik düşüş.
- `unread-count` endpoint'i artık DB tarafında sayıyor; satır transferi yok.

> **Uyarı:** `script` sütunu hâlâ liste sorgusunda döndürülüyor çünkü `VideoReviewModal.tsx` doğrudan liste nesnesindeki `content.script` alanını kullanıyor. Eğer script metinleri çok büyük hale gelirse (uzun ders senaryoları) `VideoReviewModal`'ı `getContent(id)` çekecek şekilde refactor edilmeli ve `script` da liste sütun setinden çıkarılmalı.
