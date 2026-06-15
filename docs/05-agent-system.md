# Agent Sistemi

## Genel Yapı

7 uzman agent, LangGraph orkestrasyonu altında çalışır. Her agent kendi alt grafiğinde izole çalışır, ortak Supabase state üzerinden haberleşir.

## Agent Listesi

### 1. Knowledge Agent
- **Görev:** Doküman indeksleme ve RAG araması
- **Tetikleyici:** PDF yükleme, kullanıcı sorusu
- **Kullandığı:** pgvector, OpenAI Embedding, GPT-4o
- **Çıktı:** Kaynaklı cevap + citation listesi

### 2. Voice Agent
- **Görev:** Ses girdisini yönlendirme, intent tespiti
- **Tetikleyici:** Sesli soru
- **Kullandığı:** Whisper STT, Intent Router, TTS
- **Çıktı:** Transcript + sesli yanıt (base64)

### 3. CEO Agent
- **Görev:** Günlük/haftalık yönetici özeti
- **Tetikleyici:** Her sabah 08:00 (APScheduler)
- **Kullandığı:** Tüm modüllerin istatistikleri, GPT-4o
- **Çıktı:** Günlük brief (daily_briefs tablosuna kaydedilir)

### 4. CRM Agent
- **Görev:** Lead skorlama, müşteri takibi
- **Tetikleyici:** Yeni lead ekleme, durum değişikliği
- **Kullandığı:** GPT-4o, leads tablosu
- **Çıktı:** Lead skoru (0-100), önerilen aksiyon

### 5. Follow-up Agent
- **Görev:** Otomatik takip mesajları
- **Tetikleyici:** CRM Agent sinyali (lead contacted ama yanıt yok)
- **Kullandığı:** E-posta servisi, leads tablosu
- **Çıktı:** Takip mesajı gönderilir

### 6. Learning Agent
- **Görev:** Öğrenci analizi ve kişiselleştirilmiş öğrenme planı
- **Tetikleyici:** Sınav denemesi kaydı
- **Kullandığı:** exam_attempts tablosu, GPT-4o
- **Çıktı:** Zayıf konular + öğrenme planı

### 7. Automation Agent
- **Görev:** Sosyal medya içerik üretimi
- **Tetikleyici:** Kullanıcı talebi (platform + konu + ton seçimi)
- **Kullandığı:** GPT-4o, YouTube API, Meta Graph API
- **Çıktı:** Script + başlık + hashtag → onay beklenir → yayınlanır

## LangGraph Yapısı

```python
# Her agent BaseAgent'tan türer
class BaseAgent:
    name: str
    async def run(self, input: str) -> str: ...

# Orchestrator agent'a yönlendirir
class AgentOrchestrator:
    agents: dict[AgentType, BaseAgent]
    async def route(self, agent_type, input): ...
```

## Agent → Agent İletişim

```
Yeni lead eklendi
    ↓
CRM Agent → lead skoru hesapla
    ↓
Skor < 30 → Follow-up Agent → takip mesajı gönder
Skor > 70 → yöneticiye bildirim
```

## Zamanlama (APScheduler)

```python
# Her sabah 08:00
scheduler.add_job(ceo_agent.run, "cron", hour=8, minute=0)

# Her Pazartesi 09:00 — haftalık özet
scheduler.add_job(ceo_agent.weekly_summary, "cron", day_of_week="mon", hour=9)
```
