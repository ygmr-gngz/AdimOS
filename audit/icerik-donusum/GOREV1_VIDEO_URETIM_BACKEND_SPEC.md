# GÖREV 1 — Video Üretim Hattı Backend Spesifikasyonu

> **Durum:** Frontend tamamlandı. Aşağıdakiler backend'de (kullanıcı tarafından) implemente edilecek.
> **Tarih:** 2026-07-04

---

## 1.2 TTS Dayanıklılığı (Tek Sağlayıcı — OpenAI)

**Karar:** Tek sağlayıcı (OpenAI TTS), ancak retry + exponential backoff ile sağlamlaştırılacak.  
Gelecekte Google/Azure eklemek için soyutlama katmanı hazır tutulacak ama şimdi aktif değil.

### `backend/app/modules/content/tts_client.py` (yeni dosya)

```python
"""
TTS istemcisi — retry + backoff + loglama.
İleride sağlayıcı eklendikçe bu dosya genişleyecek.
"""
import logging, time, os, uuid
from openai import OpenAI, RateLimitError, APITimeoutError
from app.core.config import settings

logger = logging.getLogger(__name__)
_client = OpenAI(api_key=settings.OPENAI_API_KEY)
_OUTPUT_DIR = "/tmp/audio"

_BACKOFF = (2, 8, 20)  # saniye — 3 deneme


def synthesize(text: str, voice: str = "nova") -> tuple[str, str]:
    """
    Metni sese çevirir.
    Returns: (mp3_dosya_yolu, kullanilan_saglayici)
    Raises: RuntimeError — tüm denemeler başarısız olursa
    """
    text = apply_pronunciation_dict(text)  # 1.3 telaffuz sözlüğü
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    path = os.path.join(_OUTPUT_DIR, f"{uuid.uuid4()}.mp3")

    last_err = None
    for attempt, wait in enumerate(_BACKOFF, 1):
        try:
            resp = _client.audio.speech.create(
                model="tts-1-hd", voice=voice, input=text, speed=0.93
            )
            with open(path, "wb") as f:
                f.write(resp.content)
            logger.info(f"[tts] openai · deneme {attempt} · başarılı · {len(text)} karakter")
            return path, "openai"
        except (RateLimitError, APITimeoutError) as e:
            last_err = e
            logger.warning(f"[tts] openai · deneme {attempt} başarısız: {e} — {wait}s bekleniyor")
            time.sleep(wait)
        except Exception as e:
            raise RuntimeError(f"[tts] OpenAI TTS hatası: {e}") from e

    raise RuntimeError(f"[tts] 3 denemeden sonra OpenAI TTS başarısız: {last_err}")
```

### `audio_generator.py` değişikliği

`generate_audio()` → `tts_client.synthesize()` ile değiştir.  
`generate_audio_segment()` → `tts_client.synthesize()` çağır, path + duration döndür.

---

## 1.3 Telaffuz Sözlüğü

### `backend/app/modules/content/pronunciation_dict.py` (yeni dosya)

```python
"""
SGS terimleri için TTS telaffuz düzeltici.
Metin TTS'e gitmeden önce bu fonksiyondan geçer.
"""
import re

_REPLACEMENTS: list[tuple[str, str]] = [
    # Kısaltmalar — harf harf okunması için
    (r'\bKDV\b',   'K D V'),
    (r'\bVUK\b',   'V U K'),
    (r'\bTTK\b',   'T T K'),
    (r'\bTMS\b',   'T M S'),
    (r'\bTFRS\b',  'T F R S'),
    (r'\bSGK\b',   'S G K'),
    (r'\bSSK\b',   'S S K'),
    (r'\bSMMM\b',  'S M M M'),
    (r'\bYMM\b',   'Y M M'),
    (r'\bSGS\b',   'S G S'),
    (r'\bGVK\b',   'G V K'),
    (r'\bÖTV\b',   'Ö T V'),
    (r'\bBSMV\b',  'B S M V'),
    (r'\bKVK\b',   'K V K'),
    # Madde numaraları — "m." → "madde"
    (r'\bm\.\s*(\d+)', r'madde \1'),
    (r'\bMd\.\s*(\d+)', r'madde \1'),
    # Fıkra
    (r'\bf\.\s*(\d+)', r'fıkra \1'),
    # Yüzde
    (r'%\s*(\d)', r'yüzde \1'),
]

_compiled = [(re.compile(pat, re.IGNORECASE), repl) for pat, repl in _REPLACEMENTS]


def apply_pronunciation_dict(text: str) -> str:
    for pattern, replacement in _compiled:
        text = pattern.sub(replacement, text)
    return text
```

**Entegrasyon:** `tts_client.synthesize()` içinde `text = apply_pronunciation_dict(text)` satırı zaten var.

---

## 1.5 Render Çıktı Doğrulaması

### `backend/app/modules/content/video_assembler.py` değişikliği

`assemble_video()` döndürmeden önce:

```python
def _validate_video_output(path: str, expected_min_seconds: float = 5.0) -> None:
    """Render sonrası temel doğrulama — başarısız işler erkenden fail etsin."""
    if not os.path.exists(path):
        raise RuntimeError(f"[render] Video dosyası oluşturulmadı: {path}")
    size = os.path.getsize(path)
    if size < 50_000:  # 50 KB altı — büyük ihtimalle bozuk
        raise RuntimeError(f"[render] Video dosyası çok küçük ({size} B) — render başarısız")
    # Süre kontrolü mutagen benzeri ile veya dosya boyutundan tahmin
    # Şimdilik boyut yeterli; ileride ffprobe ile süre kontrolü eklenebilir
```

### Supabase Storage kaydetme

`video.py` route'unda iş tamamlandıktan sonra:

```python
def _upload_to_storage(sb, video_path: str, job_id: str) -> str:
    """Render sonrası video dosyasını Supabase Storage'a yükler."""
    with open(video_path, "rb") as f:
        data = f.read()
    storage_path = f"videos/{job_id}.mp4"
    sb.storage.from_("videos").upload(storage_path, data, {"content-type": "video/mp4"})
    url = sb.storage.from_("videos").get_public_url(storage_path)
    return url  # video_jobs.video_url alanına yaz
```

**Gerekli migration:**

```sql
-- video_jobs tablosuna eklenecek sütunlar
ALTER TABLE video_jobs
  ADD COLUMN IF NOT EXISTS storage_path TEXT,
  ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT,
  ADD COLUMN IF NOT EXISTS duration_seconds FLOAT,
  ADD COLUMN IF NOT EXISTS tts_provider TEXT DEFAULT 'openai';
```

---

## Kalan Riskler

| Risk | Etki | Öneri |
|------|------|-------|
| OpenAI TTS 429 kota sınırı | Video üretimi durur | `_BACKOFF` + kota izleme; kota bitince kullanıcıya bildirim |
| Render sırasında bellek/disk dolması | Railway container crash | `/tmp` temizleme cron'u; büyük videolarda streaming render |
| `mutagen` süre okuma hatalı | Sahne süreleri yanlış | Unit test: bilinen süredeki MP3 ile doğrula |
| Remotion 502 | Video render başarısız | Health check + circuit breaker (Görev 4.1 kapsamında) |
