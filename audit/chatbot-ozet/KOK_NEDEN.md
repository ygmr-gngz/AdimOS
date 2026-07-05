# KÖK NEDEN ANALİZİ — Chatbot Doküman Özetleme Sorunu

Tarih: 2026-07-05

---

## Hipotez (Doğrulandı)

> "Özetle" isteği standart RAG soru-cevap yolundan işleniyor: sorgu embedding'iyle en alakalı top-k chunk çekiliyor ve yalnızca onlar özetleniyor.

**Durum: ✅ TAMAMEN DOĞRULANDI**

---

## Kanıt 1 — Tek Yol, Sıfır Niyet Ayrımı

**Dosya:** `backend/app/api/routes/chat.py`  
```python
# satır 51 — tüm mesajlar bu tek fonksiyona düşüyor
result = query(message, history, user_id=user.id)
```

**Dosya:** `backend/app/modules/knowledge/rag.py`  
```python
def query(user_message: str, conversation_history=None, user_id=None) -> dict:
    # satır 260-398: "özetle" için hiçbir if/elif yok
    chunks = retrieve(user_message, match_count=10, ...)  # satır 271
    ...
    for i, chunk in enumerate(chunks[:MAX_CHUNKS_IN_CONTEXT], 1):  # satır 347
```

"Özetle" isteği, "çek hamiline düzenlenebilir mi?" sorusuyla AYNI kod yolundan geçiyor.

---

## Kanıt 2 — Sabit Üst Sınır: 6 Chunk

**Dosya:** `backend/app/modules/knowledge/rag.py`

```python
MAX_CHUNKS_IN_CONTEXT = 6   # satır 16
MAX_CHUNK_CHARS = 1200       # satır 17
```

GPT'ye gönderilen context: **en fazla 6 × 1200 = 7200 karakter**.

SGS-TİCARET HUKUKU-FUAT HOCA.pdf gibi kapsamlı bir ders dokümanı için:
- Chunker parametreleri: `max_tokens=500`, `overlap=50` → her chunk ~375 kelime
- 87 sayfalık PDF → tahminen **~100-130 chunk**
- Kullanılan: **6 / ~115 chunk = %5 kapsama**

→ Chatbot dokümanın %5'ini özetleyip bunu "dokümanın tamamının özeti" gibi sundu.

---

## Kanıt 3 — "Son Doküman" Semantic Search ile Çözülüyor (Yanlış)

**Dosya:** `backend/app/modules/knowledge/rag.py` satır 271:
```python
chunks = retrieve(user_message, match_count=10, match_threshold=SIMILARITY_THRESHOLD)
```

"Son dokümanı özetle" mesajı embedding'e dönüştürülüyor ve cosine benzerliğiyle en yakın chunk'lar çekiliyor. Bu durumda:
- "kıymetli evrak", "poliçe", "çek" gibi terimler içeren chunk'lar yüksek benzerlik skoru aldı (mesajdaki "doküman" + "özetle" kelimeleriyle örtüşen bölüm)  
- Sistem "kıymetli evrak" bölümündeki 6 chunk'ı döndürdü

Timestamp bazlı "son yüklenen doküman" çözümlemesi bulunmuyor.

`documents_repo.py`'daki `get_documents()` → `.order("created_at", desc=True)` var, ama **RAG akışından hiç çağrılmıyor**.

---

## Kanıt 4 — Altyapı Hazır, Kullanılmıyor

```python
# chunks_repo.py satır 17-26 — TÜM chunk'ları sıralı getirir, mevcut
def get_chunks_by_document_id(document_id: str):
    ...
    .order("chunk_index", desc=False)

# documents_repo.py satır 28-34 — timestamp sıralı, mevcut
def get_documents(source_module=None):
    ...
    .order("created_at", desc=True)
```

Map-reduce özetleme için gereken iki fonksiyon zaten var — sadece `query()` içinden çağrılmıyor.

---

## Örnek Olaydaki Hata Akışı

```
Kullanıcı: "son dokümanı özetle"
    ↓
retrieve("son dokümanı özetle", match_count=10) 
    ↓
pgvector cosine search → kıymetli evrak chunk'ları top-10'da
    ↓
GPT'ye gönderilen: 6 chunk (hepsi kıymetli evrak bölümünden)
    ↓
GPT çıktısı: kıymetli evrak özeti
    ↓
Chatbot: "SGS-TİCARET HUKUKU dokümanının özeti: [kıymetli evrak...]"
         ← EKSİK, UYARISIZ, YANILTICI
```

**Beklenen akış:**
```
Kullanıcı: "son dokümanı özetle"
    ↓
Niyet: ÖZETLEME → summarize_route()
    ↓
documents tablosundan en yeni dokümanı çek (created_at DESC)
    ↓
get_chunks_by_document_id(doc_id) → TÜM chunk'lar (ör. 115 adet)
    ↓
Map: 23 grup × 5 chunk → 23 kısmi özet (paralel LLM)
    ↓
Reduce: 23 özeti → yapılandırılmış nihai özet
    ↓
Yanıt: "**SGS-TİCARET HUKUKU-FUAT HOCA.pdf** (115 bölüm işlendi)\n## Tacir..."
```
