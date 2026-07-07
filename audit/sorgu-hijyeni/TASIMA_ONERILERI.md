# Taşıma Önerileri — Büyük Alan Analizi

**Tarih:** 2026-07-07

---

## `generated_contents` — Satır Boyutu Analizi

### Sorunlu Alanlar

| Alan | Tip | Boyut Tahmini | Sorun |
|------|-----|---------------|-------|
| `audio_base64` | TEXT (base64) | 1–5 MB/satır | TTS ses dosyası base64 kodlu saklanıyor |
| `script` | TEXT | 2–20 KB/satır | Uzun ders/quiz senaryosu |

### `audio_base64` İçin Taşıma Önerisi

**Mevcut durum:** TTS üretimi sonucu ses verisi `generated_contents.audio_base64` sütununa base64 string olarak yazılıyor.

**Önerilen yol:** Ses dosyası Supabase Storage'a yüklenmeli, URL `generated_contents.audio_url` sütununa yazılmalı, `audio_base64` DB'den silinmeli.

```
Taşıma adımları (onay bekliyor):
1. `content/service.py` içinde TTS üretimi sonrası ses verisini base64 yerine Storage'a yükle
   → bucket: "content-audio" (oluşturulacak)
   → path: "audios/{content_id}.mp3"
   → URL'yi `audio_url` alanına yaz
2. `generated_contents_repo.py` içinde `audio_url` alanının mevcut olduğunu doğrula
3. `audio_base64` sütununu migration ile kaldır (onaydan sonra)
4. Mevcut satırlardaki `audio_base64` değerleri için migration script:
   - Varsa → Storage'a yükle → `audio_url` güncelle → NULL yap
   - Yoksa → dokunma
```

**Etki:** Satır başına 1–5 MB → ~0 KB (sadece URL string).

---

## Supabase Timeout Ayarı — Öneri

**Mevcut durum:** `app/db/supabase.py` içinde Supabase istemcisi varsayılan httpx timeout ile oluşturuluyor (varsayılan = sonsuz bekleme).

**Önerilen değişiklik (onay bekliyor):**

```python
# app/db/supabase.py
import httpx

_client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
    options=ClientOptions(
        httpx_options={"timeout": httpx.Timeout(connect=5.0, read=15.0, write=10.0, pool=5.0)}
    )
)
```

**Etki:** Supabase yanıt vermezse 15 saniye sonra `httpx.ReadTimeout` → `main.py` handler → istemciye 504. Aksi halde worker thread sonsuza dek kilitli kalıyor.

---

## Async Postgrest İstemcisi — Uzun Vadeli Öneri

**Mevcut durum:** Tüm Supabase sorguları senkron (`supabase-py` sync client). FastAPI bunları `run_in_threadpool` ile çalıştırıyor. Yavaş bir sorgu worker thread'i kilitliyor.

**Uzun vadeli çözüm:** `supabase-py` async client'a geçiş.

```python
# Örnek (mevcut değil — değişiklik gerektirir)
from supabase._async.client import AsyncClient

async def get_async_supabase_client() -> AsyncClient:
    return await acreate_client(URL, KEY)
```

**Etki:** Yavaş sorgu sırasında diğer istekler bloklanmaz; thread havuzu tükenmiyor.

**Bu sprint'e alınmadı** — mevcut tüm route'ları async'e çevirmek geniş kapsamlı refactor gerektirir. Yukarıdaki timeout ayarı + limit ekleme kısa vadeli çözüm olarak yeterlidir.

---

## `conversations` / `messages` — İzleme Kararı

Agent chat özelliği büyüdükçe:
- `messages` tablosu hızla büyür (her konuşma tur başına satır)
- `list_messages()` limitsiz — yüzlerce mesajlı konuşmada sorun çıkarabilir

**Önerilen (agent UI aktif hale gelince):** `list_messages()` içine `.limit(100)` + mesaj sayfalama.
