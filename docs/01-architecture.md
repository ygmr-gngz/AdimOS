# Sistem Mimarisi

## Genel Yapı

```
┌─────────────────────────────────────────────────────┐
│                   İstemci Katmanı                   │
│  Next.js 15 (Vercel)                                │
│  ├── Dashboard (yönetici paneli)                    │
│  ├── Asistan Widget (floating chat + ses)           │
│  └── Web Sitesi Chatbotu (/widget — iframe embed)   │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / REST
┌────────────────────▼────────────────────────────────┐
│                  Uygulama Katmanı                   │
│  FastAPI (Railway)                                  │
│  ├── /api/v1/documents   — doküman işleme           │
│  ├── /api/v1/chat        — RAG soru-cevap           │
│  ├── /api/v1/voice       — STT + TTS               │
│  ├── /api/v1/agents      — agent yönetimi           │
│  ├── /api/v1/dashboard   — istatistik + özet        │
│  ├── /api/v1/crm         — lead yönetimi            │
│  ├── /api/v1/academy     — öğrenci yönetimi         │
│  ├── /api/v1/automation  — içerik otomasyonu        │
│  └── /api/v1/website     — chatbot konuşmaları      │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
┌────────▼───┐ ┌─────▼────┐ ┌───▼──────────┐
│  Supabase  │ │  OpenAI  │ │   Redis      │
│  PostgreSQL│ │  GPT-4o  │ │   (kuyruk)   │
│  pgvector  │ │  Whisper │ └──────────────┘
│  Storage   │ │  TTS     │
└────────────┘ └──────────┘
```

## Klasör Yapısı

```
backend/app/
├── main.py                  # FastAPI app, CORS, router
├── core/
│   ├── config.py            # Env değişkenleri (pydantic-settings)
│   ├── exceptions.py        # Özel HTTP hata sınıfları
│   ├── logging.py           # Yapılandırılmış loglama
│   └── security.py          # JWT doğrulama (Supabase auth)
├── db/
│   ├── supabase.py          # Supabase client
│   ├── storage.py           # Dosya yükleme/indirme
│   └── repositories/        # Ham veritabanı sorguları
├── schemas/                 # Pydantic request/response modelleri
├── modules/                 # İş mantığı katmanı
│   ├── knowledge/           # PDF → chunk → embedding → RAG
│   ├── voice/               # STT → intent → TTS
│   ├── agents/              # LangGraph agent'ları
│   ├── crm/                 # Lead skorlama, follow-up
│   ├── dashboard/           # Brief generator
│   ├── automation/          # Sosyal medya içerik akışı
│   └── academy/             # Öğrenci analizi
└── api/
    ├── router.py            # Tüm route'ları birleştirir
    └── routes/              # Her modül için endpoint dosyası
```

## Veri Akışı — RAG

```
PDF yükleme:
  Upload → Storage → PyPDF metin çıkar → Tiktoken chunk →
  OpenAI Embedding → pgvector kaydet → status: indexed

Soru sorma:
  Soru → Embedding → pgvector benzerlik ara (top-5) →
  GPT-4o (context + soru) → Kaynaklı cevap
```

## Veri Akışı — Sesli Asistan

```
Ses kaydı → Whisper STT → metin →
Intent Router → doğru agent → RAG cevap →
OpenAI TTS → base64 ses → frontend oynatır
```

## Teknoloji Kararları

| Karar | Neden |
|---|---|
| Supabase pgvector | Ayrı vektör DB kurmadan PostgreSQL içinde embedding |
| LangGraph | Agent'lar arası durum yönetimi, koşullu yönlendirme |
| Railway backend | Dockerfile ile direkt deploy, env yönetimi kolay |
| Vercel frontend | Next.js için optimize, CDN, preview deployment |
| base64 ses | Frontend'e ayrı dosya URL'i vermek yerine direkt embed |
