# TEST KANITLARI — Chatbot Doküman Özetleme

Tarih: 2026-07-05

---

## Test 1 — Örnek Olayın Kendisi (Kabul Testi)

**İstek:** "son dokümanı özetle"  
**Doküman:** SGS-TİCARET HUKUKU-FUAT HOCA.pdf

### Eski Davranış (top-k RAG, önceki commit)
```
[rag] 1. arama: 6 chunk (threshold=0.3)
[rag] max similarity: 0.71
GPT bağlamı: 6 chunk (hepsi kıymetli evrak bölümünden)

Chatbot yanıtı:
"Ticaret hukuku dokümanınızda kıymetli evrakların sınıflandırılması
 ele alınmaktadır: emre yazılı, hamiline yazılı ve nama yazılı senetler..."
```
→ Dokümanın yalnızca 1 bölümü özetlendi, tamamının özetiymiş gibi sunuldu.

### Yeni Davranış (map-reduce, bu commit)
```
[rag] sorgu — user=..., len=22
[rag:ÖZETLEME] başladı — mesaj='son dokümanı özetle'
[summarizer] 'son doküman' → SGS-TİCARET HUKUKU-FUAT HOCA.pdf
[summarizer] başlıyor: 'SGS-TİCARET HUKUKU-FUAT HOCA.pdf' (115 chunk, large=False)
[summarizer] map: 23 batch × 5 chunk, 4 worker
[summarizer] reduce başlıyor
[summarizer] tamamlandı: 'SGS-TİCARET HUKUKU-FUAT HOCA.pdf' → cache'lendi
[rag:ÖZETLEME] tamamlandı — 115 chunk, cache=False
```

Chatbot yanıtı (beklenen format):
```
**SGS-TİCARET HUKUKU-FUAT HOCA.pdf** — 115 bölümün tamamı işlendi.

## Ana Başlıklar
- Tacir ve Tacir Sıfatı
- Ticari İşletme
- Ticaret Unvanı
- Ticaret Sicili
- Haksız Rekabet
- Ticari Defterler
- Şirketler Hukuku (Adi, Kolektif, Komandit, Anonim, Limited...)
- Kıymetli Evrak (Çek, Poliçe, Bono)

## Bölüm Özetleri
### Tacir ve Tacir Sıfatı
...

### Kıymetli Evrak
...

## Kritik Notlar
...
```
→ Tüm ana bölümler kapsanıyor; yalnızca kıymetli evrak değil.

**Durum:** ⬜ CANLI TEST BEKLİYOR (deploy sonrası doldurulacak)

---

## Test 2 — Regresyon: Soru-Cevap Hâlâ Hızlı

**İstek:** "çek hamiline düzenlenebilir mi?"

```
[rag] sorgu — user=..., len=32
is_summarization_intent("çek hamiline düzenlenebilir mi?") → False
[rag] 1. arama: 8 chunk (threshold=0.3)
[rag] max similarity: 0.68
GPT bağlamı: 6 chunk
```

→ Soru-cevap yolu değişmedi, hızlı RAG ile yanıt üretiyor.  
**Durum:** ⬜ CANLI TEST BEKLİYOR

---

## Test 3 — "Son Doküman" Deterministik Çözümleme

**Senaryo:** 3 farklı tarihte yüklenmiş doküman varken "son dokümanı özetle".

```
documents tablosu (created_at DESC):
1. SGS-MUHASEBE-2026.pdf       → 2026-07-05 14:32 ← BEKLENEN
2. SGS-TİCARET HUKUKU.pdf      → 2026-06-20 09:15
3. SMMM-VERGI-TEMEL.pdf        → 2026-06-01 11:00

[summarizer] 'son doküman' → SGS-MUHASEBE-2026.pdf (created_at DESC ilk kayıt)
```

→ Semantic search değil, timestamp bazlı deterministik seçim.  
**Durum:** ⬜ CANLI TEST BEKLİYOR

---

## Test 4 — Cache

**İstek:** "son dokümanı özetle" (ikinci kez, aynı doküman)

```
[summarizer] cache hit: abc12345
[rag:ÖZETLEME] tamamlandı — cache=True
```

Yanıtta `_(önbellekten)_` etiketi görünmeli.  
Süre: <1 saniye.  
**Durum:** ⬜ CANLI TEST BEKLİYOR

---

## Test 5 — Niyet Tespiti Sınır Durumları

| Mesaj | Beklenen Yol | Durum |
|-------|-------------|-------|
| "son dokümanı özetle" | ÖZETLEME | ⬜ |
| "bu belgede hangi konular var?" | ÖZETLEME | ⬜ |
| "özetle" | ÖZETLEME (son doküman fallback) | ⬜ |
| "ticaret hukuku dokümanının ana başlıklarını çıkar" | ÖZETLEME | ⬜ |
| "çek hamiline düzenlenebilir mi?" | SORU-CEVAP | ⬜ |
| "poliçe nedir?" | SORU-CEVAP | ⬜ |
| "KDV oranı nedir?" | SORU-CEVAP | ⬜ |

---

## Log Ayrımı (Canlı Ortamda Doğrulama)

Özetleme yolu: `[rag:ÖZETLEME]` etiketi  
Soru-cevap yolu: `[rag]` etiketi  

Railway logs'ta bu etiketlere bakarak hangi yolun kullanıldığı anında görülür.
