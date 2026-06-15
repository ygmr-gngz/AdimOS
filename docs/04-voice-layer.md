# Ses Katmanı

## Genel Akış

```
Kullanıcı mikrofona basar
        ↓
MediaRecorder API (tarayıcı) → webm blob
        ↓
POST /api/v1/voice  (multipart/form-data)
        ↓
Whisper STT → transcript (metin)
        ↓
Intent Router → hangi agent?
        ↓
Agent → RAG → GPT-4o → cevap metni
        ↓
OpenAI TTS → mp3 ses
        ↓
base64 encode → JSON response
        ↓
Frontend → Audio() → oynat
```

## Modüller

### modules/voice/stt.py
Whisper ile ses → metin:
```python
# openai.audio.transcriptions.create()
# model: whisper-1
# language: tr (Türkçe zorunlu)
```

### modules/voice/tts.py
Metin → ses:
```python
# openai.audio.speech.create()
# model: tts-1
# voice: onyx (erkek, profesyonel)
# response_format: mp3
```

### modules/voice/intent_router.py
Transcript'e bakarak hangi agent'a yönlendireceğini belirler:
```
"doküman", "bilgi", "hakkında"  → Knowledge Agent
"müşteri", "lead", "takip"      → CRM Agent
"özet", "bugün", "rapor"        → CEO Agent
"öğrenci", "sınav", "SGS"       → Learning Agent
diğer                           → Knowledge Agent (varsayılan)
```

### modules/voice/service.py
Tüm adımları bir araya getirir:
```python
async def process_voice(audio_blob) -> VoiceResponse:
    transcript = await stt(audio_blob)
    agent = intent_router(transcript)
    answer = await agent.run(transcript)
    audio_b64 = await tts(answer)
    return VoiceResponse(transcript, answer, audio_b64, agent.name)
```

## Web Sitesi Chatbotu Ses Akışı

Aynı akış, farklı endpoint:
```
POST /api/v1/website/voice
  → site_id + visitor_id ek parametre
  → konuşma Supabase'e kaydedilir
  → aynı STT → Intent → RAG → TTS pipeline
```

## Ses Formatları

| Adım | Format |
|------|--------|
| Tarayıcıdan gelen | audio/webm (MediaRecorder) |
| Whisper'a gönderilen | audio/webm |
| TTS çıktısı | mp3 |
| Frontend'e gönderilen | base64 string |
| Frontend'de oynatılan | `new Audio("data:audio/mpeg;base64,...")` |

## Türkçe Optimizasyonu

- Whisper'a `language="tr"` parametresi gönderilmeli
- TTS voice seçenekleri: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`
- Türkçe için `onyx` veya `nova` önerilir
