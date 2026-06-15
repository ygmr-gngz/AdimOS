# Veritabanı Yapısı

## Supabase Tabloları

### documents
PDF ve doküman kayıtları.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | uuid | Primary key |
| file_name | text | Orijinal dosya adı |
| storage_path | text | Supabase Storage'daki yol |
| status | text | uploaded / processing / indexed / failed |
| created_at | timestamptz | Yüklenme zamanı |

### document_chunks
PDF'lerden çıkarılan metin parçaları ve embedding'leri.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | uuid | Primary key |
| document_id | uuid | documents.id FK |
| content | text | Metin parçası |
| embedding | vector(1536) | OpenAI embedding |
| chunk_index | int | Kaçıncı parça |
| page_number | int | PDF sayfa numarası |

### leads
CRM — potansiyel müşteriler.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | uuid | Primary key |
| name | text | Ad soyad |
| email | text | E-posta |
| phone | text | Telefon |
| status | text | new / contacted / qualified / converted / lost |
| score | int | AI lead skoru (0-100) |
| notes | text | Notlar |
| created_at | timestamptz | Oluşturma zamanı |

### students
SGS Akademi öğrencileri.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | uuid | Primary key |
| name | text | Ad |
| surname | text | Soyad |
| email | text | E-posta |
| phone | text | Telefon |
| status | text | active / inactive / graduated / failed |
| created_at | timestamptz | Kayıt zamanı |

### exam_attempts
Öğrenci sınav denemeleri.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | uuid | Primary key |
| student_id | uuid | students.id FK |
| exam_name | text | Sınav adı |
| score | float | Puan |
| attempted_at | timestamptz | Deneme zamanı |

### agent_runs
Agent çalışma geçmişi.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | uuid | Primary key |
| agent_type | text | knowledge / voice / ceo / crm / followup / learning / automation |
| status | text | idle / running / completed / failed |
| result_summary | text | Kısa sonuç özeti |
| started_at | timestamptz | Başlama zamanı |
| finished_at | timestamptz | Bitiş zamanı |

### daily_briefs
CEO Agent günlük özetleri.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | uuid | Primary key |
| content | text | Özet metni |
| created_at | timestamptz | Oluşturma zamanı |

### website_conversations
Web sitesi chatbot konuşmaları.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | uuid | Primary key |
| site_id | text | Hangi site (embed kodu data-site-id) |
| visitor_id | text | Ziyaretçi session ID |
| visitor_name | text | Opsiyonel isim |
| status | text | active / closed |
| started_at | timestamptz | Başlama zamanı |
| last_message_at | timestamptz | Son mesaj zamanı |

### website_messages
Web sitesi chatbot mesajları.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | uuid | Primary key |
| conversation_id | uuid | website_conversations.id FK |
| role | text | visitor / assistant |
| content | text | Mesaj metni |
| input_type | text | text / voice / file |
| created_at | timestamptz | Gönderim zamanı |

## pgvector Kurulumu

Supabase SQL editöründe:

```sql
-- pgvector extension
create extension if not exists vector;

-- document_chunks tablosu
create table document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references documents(id) on delete cascade,
  content text not null,
  embedding vector(1536),
  chunk_index int,
  page_number int,
  created_at timestamptz default now()
);

-- Benzerlik araması için index
create index on document_chunks
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);
```

## Supabase Storage Buckets

```
documents/   → PDF dosyaları
audio/       → Ses kayıtları (geçici)
```

## pgvector Benzerlik Araması

```sql
-- En yakın 5 chunk'ı getir
select content, page_number, 1 - (embedding <=> '[...query embedding...]') as similarity
from document_chunks
order by embedding <=> '[...query embedding...]'
limit 5;
```
