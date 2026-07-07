# Köprü Teşhisi — Bilgi Merkezi → SGS Akademi

**Tarih:** 2026-07-07  
**Durum:** ❌ Köprü hiç kurulmamış — tam izolasyon

---

## 1. Kanıtlı Kök Neden

Bilgi Merkezi'nden yüklenen PDF'ler SGS Akademi kartlarında **asla** görünmez çünkü iki sistem arasında **hiçbir veri akışı** yoktur.

### Veri akışı — Bilgi Merkezi yüklemesi

```
POST /api/documents
  → create_document()          → documents tablosu
  → upload_file()              → Supabase Storage (documents/{id}/...)
  → _index_background()        → chunks tablosu (embedding)
  ✗ sgs_analyses tablosuna YAZMIYOR
  ✗ sgs_questions tablosuna YAZMIYOR
```

### Veri akışı — SGS Akademi yüklemesi

```
POST /api/sgs/analyze
  → analyze_pdf_bytes()        → OpenAI ile soru çıkarımı
  → create_analysis()          → sgs_analyses tablosu (questions JSONB)
  → create_document()          → documents tablosu (sgs_analysis_id ile)
  → [frontend] parseQuestions()→ sgs_questions tablosu
```

### SGS Akademi sayfasının veri kaynağı

```
academy/page.tsx
  → sgsService.getAreas()
    → GET /api/sgs/areas
      → get_areas_from_sgs_questions()
        → sgs_questions tablosu  ← YalnIZCA BURADAN OKUR
  
  → sgsService.getLessonTopicAnalysis()
    → GET /api/sgs/lessons/{lesson}/topic-analysis
      → get_lesson_topics_from_sgs_questions()
        → sgs_questions tablosu  ← YalnIZCA BURADAN OKUR
```

**Sonuç:** Bilgi Merkezi yüklemeleri `sgs_questions` tablosuna hiç ulaşamıyor. SGS Akademi `sgs_questions`'tan başka hiçbir şeye bakmıyor.

---

## 2. İki Silosun Karşılaştırması

| Özellik | Bilgi Merkezi | SGS Akademi |
|---------|--------------|-------------|
| Upload endpoint | `POST /api/documents` | `POST /api/sgs/analyze` |
| DB kayıt | `documents` + `chunks` | `sgs_analyses` + `sgs_questions` |
| Processing | PDF → text → embedding | PDF → OpenAI soru çıkarımı |
| Amaç | RAG / arama | Soru analizi / video üretim |
| SGS bağlantısı | ❌ yok | ✅ doğal |

---

## 3. "SGS dışında tut" toggle eksikliği

`documents` tablosunda `exclude_from_sgs` alanı **mevcut değil**.  
Şu an tüm Bilgi Merkezi dokümanları SGS'ye beslenemez (alan yok) ve beslenebilseydi de hangi dokümanların hariç tutulacağını işaretleyecek mekanizma yoktu.

---

## 4. Backfill durumu

`sgs_analyses` tablosundaki analizler:
- `POST /api/sgs/analyze` üzerinden yüklenmiş → `sgs_questions`'a parse edilmiş olanlar ✅
- Yüklendi ama parse edilmedi → `parse_all` ile kurtarılabilir ⚠️
- Yalnızca Bilgi Merkezi üzerinden yüklendi → SGS pipeline'ından tamamen habersiz ❌

`POST /api/documents/sync-sgs` endpoint'i mevcut (`documents.py` line 89):  
Bu endpoint `sgs_analyses`'daki her analiz için `documents` tablosuna kayıt açar — **tersi değil**.  
Dolayısıyla Bilgi Merkezi'nden SGS'ye otomatik besleme hâlâ kurulmamış.

---

## 5. Gerekli Değişiklikler (Plan)

### A. `documents` tablosu — migration
```sql
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS exclude_from_sgs boolean NOT NULL DEFAULT false;
```

### B. `_index_background()` sonunda SGS tetikleyici
```python
# documents.py — _index_background() sonuna eklenecek
def _trigger_sgs_if_applicable(doc_id, file_bytes, source_module):
    if source_module == 'sgs_academy' or (
        source_module != 'knowledge_center'  # ya da exclude_from_sgs=false
    ):
        return
    # Zaten sgs_academy → sgs_analyses zaten var
    # knowledge_center + exclude_from_sgs=false → yeni analiz oluştur
    from app.modules.sgs.analyzer import analyze_sgs_pdf
    from app.modules.knowledge.pdf_loader import load_pdf
    from app.db.repositories.sgs_repo import create_analysis, find_analysis_by_pdf_name
    from app.db.repositories.documents_repo import get_document
    ...
```

### C. Frontend — "SGS dışında tut" toggle
Bilgi Merkezi yükleme formunda toggle → `exclude_from_sgs` alanını Form olarak gönder.

---

## 6. Sonraki Adımlar

1. **Görev 2:** Otomatik besleme pipeline (yukarıdaki plan) — onay sonrası implement
2. **Görev 3:** Topic deduplication dry-run
3. **Görev 4:** Content planning layer
