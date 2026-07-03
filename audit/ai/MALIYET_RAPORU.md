# Maliyet ve Performans Raporu

**Tarih:** 2026-07-03  
**Fiyatlar:** OpenAI Temmuz 2026 fiyat listesi referans alındı

---

## 1. Model Fiyat Tablosu (Kullanılan Modeller)

| Model | Girdi (M token) | Çıktı (M token) | Kullanım yeri |
|-------|----------------|-----------------|---------------|
| gpt-4o | $2.50 | $10.00 | SGS Storyboard |
| gpt-4o-mini | $0.15 | $0.60 | Analiz, Chat, Script, TTS planı |
| text-embedding-3-small | $0.02 | — | RAG embedding |
| tts-1 | $15/M karakter | — | Sohbet sesi |
| tts-1-hd | $30/M karakter | — | Video TTS |
| whisper-1 | $0.006/dk | — | STT |

---

## 2. Ana İş Akışı — İstek Başına Maliyet

### 2.1 SGS PDF Analizi (En Pahalı)

| Adım | Model | Girdi token | Çıktı token | Maliyet |
|------|-------|-------------|-------------|---------|
| Analiz | gpt-4o-mini | ~25,000 | ~8,000 | ~$0.008 |
| Storyboard (5 soru) | gpt-4o | ~4,000 | ~8,000 | ~$0.090 |
| TTS (30 sahne×200 karakter) | tts-1-hd | 6,000 karakter | — | ~$0.180 |
| **TOPLAM (1 video)** | | | | **~$0.28** |

**Aylık tahmin (20 video):** ~$5.60

### 2.2 RAG Chat (Günlük Kullanım)

| Adım | Model | Girdi token | Çıktı token | Maliyet |
|------|-------|-------------|-------------|---------|
| Embedding | text-embedding-3-small | ~200 | — | ~$0.000004 |
| RAG yanıt | gpt-4o-mini | ~4,000 | ~500 | ~$0.0009 |
| **TOPLAM (1 soru)** | | | | **~$0.001** |

**Aylık tahmin (500 soru):** ~$0.50

### 2.3 CEO Brief (Günlük × 30 gün)

| Adım | Model | Token | Maliyet/gün | Aylık |
|------|-------|-------|-------------|-------|
| Brief üretimi | gpt-4o-mini | ~1,500 girdi + 900 çıktı | ~$0.0008 | ~$0.02 |

### 2.4 İçerik Scripti (Haftalık)

| Script türü | Model | Token | Maliyet |
|-------------|-------|-------|---------|
| Video script | gpt-4o-mini | ~800 girdi + 2,000 çıktı | ~$0.0013 |
| Storyboard (full) | gpt-4o-mini | ~2,000 girdi + 3,500 çıktı | ~$0.0024 |
| Director pass | gpt-4o-mini | ~4,000 girdi + 3,000 çıktı | ~$0.0024 |

**Aylık tahmin (20 içerik):** ~$0.12

---

## 3. Toplam Aylık Maliyet Tahmini

| Hizmet | Aylık Maliyet |
|--------|--------------|
| SGS PDF Analiz (20 video) | $5.60 |
| RAG Chat (500 soru) | $0.50 |
| CEO Brief (30 gün) | $0.02 |
| İçerik Scriptleri (20 içerik) | $0.12 |
| Voice / STT | $0.10 |
| **TOPLAM** | **~$6.34/ay** |

**Mevcut sistem için oldukça ekonomik.** Ölçek büyüdükçe izlenmeli.

---

## 4. En Pahalı 3 Çağrı

1. **SGS Storyboard** (`gpt-4o`, ~$0.09/video) — Model gerekçesi: Karmaşık çok-sahne yapısı, eğitim kalitesi GPT-4o gerektirir. Kabul edilebilir.

2. **Video TTS** (tts-1-hd, ~$0.18/video) — Model gerekçesi: Yüksek kalite ses için `tts-1-hd`. Maliyet düşürmek için `tts-1` kullanılabilir (~$0.09/video).

3. **SGS PDF Analizi** (gpt-4o-mini, ~$0.008/PDF) — Zaten mini model, optimize.

---

## 5. Optimizasyon Önerileri

### 5.1 Prompt Caching (Orta Vadeli)
Tekrarlanan sistem promptları için OpenAI Prompt Caching:
- SGS analyzer'da `_LESSON_KEYWORDS` (~1,000 token) her PDF'de tekrar ediliyor
- Caching %50 indirim → aylık tasarruf: ~$0.50

### 5.2 TTS Model Seçimi
`tts-1-hd` → `tts-1` geçişi: %50 maliyet tasarrufu, kalite farkı kulağa göre değişir.
Öneri: A/B testi yap, kullanıcı farkı fark etmiyorsa geç.

### 5.3 Embedding Batch
Birden fazla chunk yükleme sırasında `embed_batch()` zaten kullanılıyor ✅

### 5.4 Paralel TTS
Video sahneleri şu an sıralı TTS yapıyor. Paralel `asyncio.gather()` ile süre %60 kısalır:
```python
import asyncio
async def generate_all_tts(scenes):
    return await asyncio.gather(*[
        asyncio.to_thread(generate_audio, scene["narration"])
        for scene in scenes
    ])
```

---

## 6. Kota ve Tavan Önerileri

| Limit | Değer | Nerede |
|-------|-------|--------|
| Kullanıcı başı günlük PDF analizi | 10/gün | slowapi veya DB counter |
| Kullanıcı başı günlük chat | 100/gün | slowapi |
| Kullanıcı başı günlük storyboard | 5/gün | slowapi |
| İstek başı max PDF boyutu | 50 MB | ✅ Mevcut |
| Aylık OpenAI harcama alarmı | $50 | OpenAI dashboard |

---

## 7. Gecikme Profili

| İşlem | Süre | Darboğaz |
|-------|------|---------|
| SGS PDF analizi | 30-90 sn | GPT token üretimi |
| SGS Storyboard | 20-60 sn | GPT-4o yavaş |
| Video TTS (30 sahne) | 60-120 sn | Sıralı TTS çağrıları |
| RAG chat | 2-5 sn | Embedding + GPT |
| CEO Brief | 3-8 sn | GPT-4o-mini |
| Intent routing | 0.5-1 sn | max_tokens=10, hızlı |

**Frontend 30 sn timeout risk:** SGS analiz + storyboard toplamda 110 sn sürebilir.

**Çözüm:** SGS akışını background task + polling'e çevir (FAZ 3 mimari önerisi).
