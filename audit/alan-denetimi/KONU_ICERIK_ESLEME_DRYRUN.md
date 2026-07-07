# Konu-İçerik Eşleme Dry-Run

**Tarih:** 2026-07-07  
**Durum:** KOD HAZIR — Veri değişikliği yok (mevcut `chunks` tablosu kullanılıyor)

---

## Mevcut Durum

| Tablo | Kayıt Sayısı |
|-------|-------------|
| `chunks` | 4,716 |
| `sgs_questions` | 271 |
| `documents` | 56 |

`chunks` tablosu: `id`, `document_id`, `chunk_index`, `chunk_data`, `embedding`, `created_at`  
Konuya bağlı chunk yoktu — şimdi topic-document ilişkisi `sgs_questions.document_id` üzerinden kuruldu.

---

## Eşleme Mantığı (Migration Gerekmez)

```
topic → sgs_questions (topic = X) → document_id listesi → chunks
```

1. `sgs_questions` tablosunda `topic = 'Kıdem Tazminatı'` → `document_id` setini al
2. `chunks` tablosunda `document_id IN (...)` → metin parçaları
3. Bu parçalar konu anlatımı videosunun hammaddesi

**Halüsinasyon koruması:** Kaynak parça yoksa (`chunk_count = 0`) üretim başlamıyor.

---

## Konulara Göre Kaynak Durumu (Örnek — API'den alınacak)

```
GET /api/v1/sgs/topics/{topic}/source-content
```

Beklenen çıktı:
```json
{
  "topic": "Kıdem Tazminatı",
  "lesson_name": "İş ve Sosyal Güvenlik Hukuku",
  "source_available": true,
  "chunk_count": 12,
  "document_count": 1,
  "documents": [{"id": "...", "name": "8-İŞ VE SOS.GÜV.HUKUKU.pdf"}],
  "chunks": [...]
}
```

Kaynak yoksa:
```json
{
  "source_available": false,
  "chunk_count": 0,
  "warning": "Bu konuya ait soru bağlantılı doküman bulunamadı."
}
```

---

## Backfill Sayım Taahhüdü

Mevcut eşleme yeni tablo oluşturmuyor — sadece mevcut tabloları okuyarak ilişki kuruyor.  
`chunks` sayısı: önce = sonra = **4,716** (değişmez).

---

## Gelecek Sprint: Kalıcı Eşleme Tablosu

İleride `topic_document_links` tablosu eklenebilir:

```sql
CREATE TABLE topic_document_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic TEXT NOT NULL,
  lesson_name TEXT,
  document_id UUID REFERENCES documents(id),
  relevance_score FLOAT DEFAULT 1.0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(topic, document_id)
);
```

Bu tablo sayesinde: kullanıcı manuel olarak "bu konuya bu doküman bağlı" ilişkisi kurabilir.
