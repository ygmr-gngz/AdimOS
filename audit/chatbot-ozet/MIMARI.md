# MİMARİ — Tam Doküman Özetleme (Map-Reduce)

Tarih: 2026-07-05

---

## Yeni Bileşenler

| Dosya | Değişiklik | Açıklama |
|-------|-----------|----------|
| `backend/app/modules/knowledge/summarizer.py` | YENİ | Map-reduce engine, doküman çözümleme, in-memory cache |
| `backend/app/modules/knowledge/rag.py` | GÜNCELLEME | Niyet ayrımı → özetleme yolu |
| `backend/app/db/repositories/documents_repo.py` | GÜNCELLEME | `get_latest_document()` eklendi |

---

## Akış Diyagramı

```
Kullanıcı mesajı
       │
       ▼
is_summarization_intent(message)
       │
  ┌────┴────┐
  │ EVET    │ HAYIR
  ▼         ▼
summarize_  mevcut RAG
route()     query() ← DOKUNULMADI
  │
  ├─ resolve_document(message)
  │    ├─ "son doküman" → documents ORDER BY created_at DESC LIMIT 1
  │    └─ "X dokümanı" → ILIKE '%X%' eşleşmesi
  │
  ├─ get_chunks_by_document_id(doc_id) → TÜM chunk'lar
  │
  ├─ MAP aşaması (paralel, 4 worker)
  │    chunk[0:5]   → gpt-4o-mini → özet_0
  │    chunk[5:10]  → gpt-4o-mini → özet_1
  │    ...
  │    chunk[n-5:n] → gpt-4o-mini → özet_k
  │
  ├─ REDUCE aşaması
  │    [özet_0, özet_1, ..., özet_k] → gpt-4o-mini → yapılandırılmış özet
  │
  ├─ in-memory cache'e yaz (doc_id → result)
  │
  └─ Yanıt: "**{dosya_adı}** ({N} bölüm işlendi)\n## ..."
```

---

## Niyet Tespiti Kuralları

```python
# summarizer.py — is_summarization_intent()

SUMMARY_VERBS = ["özetle", "özet ver", "özetini ver", "özetini çıkar",
                  "özetler misin", "ne anlatıyor", "ne hakkında",
                  "hangi konular", "hangi bölümler", "ana başlık",
                  "içindekiler", "konuları neler", "bölümleri neler",
                  "summarize", "summary"]

DOC_NOUNS = ["doküman", "belge", "dosya", "pdf", "kitap",
              "ders notu", "son", "yüklediğim", "yüklenen"]

# Tetikleyici: VERB + NOUN → doküman yolu
# Kısa "özetle" komutu da → doküman yolu
# "anlat" tek başına → HAYIR (soru-cevap yolu)
```

---

## Doküman Çözümleme Öncelik Sırası

1. "son doküman" / "en son" / "en yeni" → `created_at DESC LIMIT 1`
2. Dosya adı eşleşmesi ("ticaret hukuku" → `file_name ILIKE '%ticaret%'`)
3. Eşleşme yoksa → `created_at DESC` fallback + "**{dosya}** özetleniyor" bildirimi

---

## Cache Stratejisi

| Kapsam | Yöntem | Geçerlilik |
|--------|--------|-----------|
| Process-level | `dict[doc_id → result]` | Servis yeniden başlatılana kadar |
| Temizleme | `invalidate_summary_cache(doc_id)` | Doküman yeniden işlendiğinde çağrılır |

> Gelecek: `documents` tablosuna `summary_cache JSONB` kolonu → yeniden başlatmada da korunur.

---

## Maliyet / Gecikme Tahmini

| Doküman | Chunk Sayısı | Batch | Paralel (4w) | Reduce | Toplam |
|---------|-------------|-------|-------------|--------|--------|
| ~50 sayfa | ~60 chunk | 12 | ~3 tur × 1s | ~2s | **~5s** |
| ~90 sayfa | ~115 chunk | 23 | ~6 tur × 1s | ~2s | **~8s** |
| ~150 sayfa | ~180 chunk | 36 | ~9 tur × 1s | ~2s | **~12s** |

> 150+ chunk'ta kullanıcıya süre uyarısı verilir.

---

## Dürüstlük Kuralları (sistem promptuna eklendi)

```
DOKÜMAN ÖZETİ KURALI:
Dokümanın YALNIZCA bir bölümünü özetleyip tüm dokümanın özeti gibi sunma.
"Özetle" isteğinde her zaman hangi dokümanın özetlendiğini ve
kaç bölümün işlendiğini belirt.
```

---

## Bağlantılı Yetenekler (Aynı Altyapı)

| İstek | Yol |
|-------|-----|
| "Bu dokümanda hangi konular var?" | `is_summarization_intent()` → reduce çıktısından başlık listesi |
| "Sadece şirketler hukuku bölümünü özetle" | İlgili batch özetini filtrele |
| Taxonomy/konu ağacı girişi | `summarize_document()` çıktısı taxonomy'ye input olabilir |
