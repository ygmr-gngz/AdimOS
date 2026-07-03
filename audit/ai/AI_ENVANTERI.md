# AI Katmanı Envanteri

**Tarih:** 2026-07-03  
**Kapsam:** AdimOS backend — tüm LLM çağrı noktaları, promptlar, ajan mimarisi, RAG hattı

---

## 1. LLM Çağrı Noktaları (Tam Liste)

| # | Dosya | Model | Amaç | Temp | max_tokens | json_mode | retry |
|---|-------|-------|------|------|------------|-----------|-------|
| 1 | `sgs/analyzer.py` | gpt-4o-mini | PDF→soru analizi | 0.1 | 12k–16k | ✅ | ❌→✅* |
| 2 | `sgs/storyboard.py` | **gpt-4o** | SGS video storyboard | 0.4 | 12000 | ✅ | ❌→✅* |
| 3 | `content/script_generator.py` `generate_video_script` | gpt-4o-mini | YouTube video scripti | 0.4 | 3000 | ✅ | ❌→✅* |
| 4 | `content/script_generator.py` `generate_shorts_script` | gpt-4o-mini | Shorts scripti | 0.35 | 1500 | ✅ | ❌→✅* |
| 5 | `content/script_generator.py` `generate_question_solution_script` | gpt-4o-mini | Soru çözüm scripti | 0.35 | 2000 | ✅ | ❌→✅* |
| 6 | `content/script_generator.py` `generate_topic_explanation_script` | gpt-4o-mini | Konu anlatım scripti | 0.35 | 2500 | ✅ | ❌→✅* |
| 7 | `content/script_generator.py` `generate_storyboard` | gpt-4o-mini | Genel video storyboard | 0.35 | — | ✅ | ❌ |
| 8 | `content/script_generator.py` `apply_director_pass` | gpt-4o-mini | Director ikinci geçiş | 0.25 | — | ✅ | ❌ |
| 9 | `content/script_generator.py` `generate_post_content` | gpt-4o-mini | Instagram post | — | — | ✅ | ❌ |
| 10 | `content/motivation_generator.py` | gpt-4o-mini | SGS motivasyon storyboard | 0.88 | 1800 | ✅ | ❌→✅* |
| 11 | `dashboard/brief_generator.py` | gpt-4o-mini | CEO günlük özet | 0.3 | 900 | ❌ | ✅ (fallback) |
| 12 | `knowledge/rag.py` (no-RAG) | gpt-4o-mini | Doküman olmadan sohbet | 0.4 | 1000 | ❌ | ❌→✅* |
| 13 | `knowledge/rag.py` (with-RAG) | gpt-4o-mini | RAG destekli sohbet | 0.3 | 1500 | ❌ | ❌→✅* |
| 14 | `knowledge/embeddings.py` | text-embedding-3-small | Vektör embedding | — | — | — | ❌→✅* |
| 15 | `voice/tts.py` | tts-1 | Ses sentezi (real-time) | — | — | — | ❌ |
| 16 | `voice/stt.py` | whisper-1 | Ses tanıma (tr) | — | — | — | ❌ |
| 17 | `voice/intent_router.py` | gpt-4o-mini | Intent sınıflandırma | 0.0 | 10 | ❌ | ❌→✅* |
| 18 | `agents/base.py` | gpt-4o-mini | Ajan chat (CEO/CRM/Otomasyon) | 0.4 | 1500 | ❌ | ❌→✅* |
| 19 | `academy/learning_plan.py` | gpt-4o-mini | Öğrenci çalışma planı | 0.4 | 1200 | ❌ | ❌ |

**✅* = bu audit'te düzeltildi (`llm_client.py` sarmalayıcısı üzerinden)**

---

## 2. Ajan Mimarisi

```
AdimOS Ajan Ekibi
├── CEOAgent       (agents/ceo_agent.py)   → BaseAgent  → llm_client
├── CRMAgent       (agents/crm_agent.py)   → BaseAgent  → llm_client
├── AutomationAgent(agents/auto_agent.py)  → BaseAgent  → llm_client
├── KnowledgeAgent (knowledge/rag.py)      → pgvector + GPT-4o-mini
├── VoiceAgent     (voice/*)               → Whisper + TTS + IntentRouter
└── SGSAnalyst     (sgs/analyzer.py)       → GPT-4o-mini (soru analizi)
    └── SGSStoryboard(sgs/storyboard.py)   → GPT-4o (storyboard üretimi)
```

**Orkestrasyon:** Sıralı (sequential). Ajan zincirleri yok. Döngü riski yok.  
**LangGraph/LangChain:** Kurulu ama KULLANILMIYOR → kaldırıldı.

---

## 3. PDF → Analiz → Video Hattı (AI Adımları)

```
1. PDF Yükleme
   └── pypdf → metin çıkarma (pdf_loader.py)
       └── İlk 90,000 karakter kullanılıyor (truncation)

2. SGS Analiz (sgs/analyzer.py)
   └── gpt-4o-mini [json_object, temp=0.1, max_tokens=12k-16k]
       Girdi: PDF metni + ders listesi + anahtar kelime rehberi
       Çıktı: {questions[], subjects[], video_plan[]}

3. Soru Sınıflandırma (sgs_repo.py)
   └── _resolve_lesson_for_topic() — kural tabanlı (AI yok)
       _TOPIC_LESSON_MAP ile eşleştirme

4. Storyboard Üretimi (sgs/storyboard.py)
   └── gpt-4o [json_object, temp=0.4, max_tokens=12000]
       Girdi: sorular + konu + ders bilgisi
       Çıktı: {scenes[]} — 2+(Nx6)+2 sahne

5. TTS Üretimi (content/audio_generator.py)
   └── openai.tts-1-hd, voice=onyx, speed=0.93
       Her sahne için ayrı ses dosyası → /tmp/audio/

6. Video Birleştirme (content/video_assembler.py)
   └── moviepy — (Remotion bağlı değilse bu aktif)
```

---

## 4. RAG Pipeline

| Parametre | Değer |
|-----------|-------|
| Vektör Veritabanı | Supabase pgvector |
| Embedding Modeli | text-embedding-3-small (1536 boyut) |
| Chunk Boyutu | 500 token |
| Overlap | 50 token |
| Benzerlik Eşiği | 0.3 (1. arama) |
| İyi Benzerlik Eşiği | 0.5 (altındaysa 2. arama) |
| Top-k | 10 (2. arama: 8) |
| Max Chunk Context | 6 chunk × 1200 karakter |
| Strateji | Semantic + keyword fallback (iterative RAG) |
| Reranking | ❌ Yok |

---

## 5. Sistem Promptları

### 5.1 RAG System Prompt (knowledge/rag.py — `_SYSTEM`)
- **Rol:** AdimOS çok amaçlı AI asistanı (bilgi bankası + muhasebe + CRM + eğitim)  
- **Güçlü noktalar:** Anti-hallüsinasyon kuralları, domain tespiti, kaynak zorunluluğu, XSS koruması (API key döndürme yasağı)
- **Zayıf nokta:** Prompt injection talimatı yok (belge içindeki komutlara uymama)

### 5.2 SGS Analyzer Prompt (sgs/analyzer.py)
- **Rol:** SGS soru analisti  
- **Güçlü:** 17 ders adı liste, keyword rehberi, güven skoru, kompakt mod büyük PDF'ler için
- **Düzeltilen:** PDF içeriği `<PDF_CONTENT>` etiketi içine alındı

### 5.3 SGS Storyboard Prompt (sgs/storyboard.py — `_SYSTEM`)
- **Rol:** 20 yıllık SGS eğitmeni
- **Kalite:** Sahne başına 6 zorunlu bölüm, narration kelime sayısı belirtilmiş, Türkçe zorunlu
- **Not:** GPT-4o kullanımı burada meşru (karmaşık yapısal üretim)

### 5.4 CEO Agent Brief (dashboard/brief_generator.py)
- **Güçlü:** Markdown format sabitlenmiş, fallback metin var
- **Zayıf:** Sistem saati verisi var ama kullanıcı mesajlaşma geçmişi yok

### 5.5 BaseAgent Promptları
| Ajan | Sistem Promptu | Puan |
|------|---------------|------|
| CEOAgent | 1 satır, genel | 2/5 |
| CRMAgent | 1 satır, genel | 2/5 |
| AutomationAgent | 1 satır, genel | 2/5 |
