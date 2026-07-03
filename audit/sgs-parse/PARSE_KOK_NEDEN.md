# SGS Parse Hattı — Kök Neden Analizi

**Tarih:** 2026-07-03  
**Durum:** FAZ 1 tamamlandı, FAZ 2 düzeltmeleri uygulandı

---

## Özet: Kayıp Noktası Tablosu

| # | Kayıp Noktası | Dosya | Etki | Durum |
|---|---------------|-------|------|-------|
| K-1 | `_MAX_CHARS = 90_000` — büyük PDF kesilmesi | `analyzer.py:88` | Büyük PDF'lerde son sayfalar analiz edilmiyor | ⚠️ Mimari sınır |
| K-2 | `parse_all` — herhangi 1 satır varsa analiz atlıyor | `sgs_repo.py:926` | Kısmi parse gizli kalıyor, düzeltilemiyor | ✅ DÜZELTİLDİ |
| K-3 | Belirsiz sorular sessizce atlanıyor | `sgs_repo.py:566` | `debug` log, hiç bildirim yok | ✅ DÜZELTİLDİ |
| K-4 | `INSERT` satır sayısı doğrulanmıyor | `sgs_repo.py:585,642` | DB yazma hatası gizli kalıyor | ✅ DÜZELTİLDİ |
| K-5 | Supabase 1000 satır varsayılan limiti | `sgs_repo.py:925` | Büyük tabloda `document_id` kümesi eksik | ✅ DÜZELTİLDİ |
| K-6 | TTS 429 — sahne sessizce atlıyor | `video.py:322` | Job `ready_for_review`'da kalıyor, ses eksik | ✅ DÜZELTİLDİ |
| K-7 | Remotion hata → `ready_for_review` (yanıltıcı) | `video.py:371` | Render başarısız görüntüsü gizleniyor | ✅ DÜZELTİLDİ |

---

## Detay: K-1 — PDF Kesme Limiti (Mimari Sınır)

```python
# analyzer.py:17-18
_MAX_CHARS = 90_000
_COMPACT_THRESHOLD = 55_000

# analyzer.py:88
text_chunk = pdf_text[:_MAX_CHARS]  # Sonraki sayfalar kesilir
```

**Etki:** Bir sınav PDF'i ~600-900 karakter/soru ortalama içeriyor.  
- `_MAX_CHARS = 90_000` → ~100–150 soru analiz edilebilir
- PDF 200+ soru içeriyorsa ve >90k karakter ise → son sorular analiz edilmiyor
- Uyarı log'u var (`logger.warning`) ama sonuç kayıp sorular içeriyor

**Log'a bakış:**
```
[sgs-analyzer] PDF çok uzun (...karakter), ilk 90000 karakter kullanılıyor
```
Bu uyarı geldiyse kayıp var demektir.

**Kalıcı çözüm seçenekleri (henüz uygulanmadı):**
1. **Chunk parse:** PDF'i 90k'lık parçalara böl, her parçayı ayrı analiz et, birleştir
2. **İki geçiş:** İlk geçiş sadece soru numaralarını say, ikinci geçiş full analiz
3. **Kullanıcı uyarısı:** Kaç sorunun analiz edilemediğini response'a ekle

**Öneri:** Chunk parse (seçenek 1) en doğru sonucu verir ancak karmaşıktır.  
Kısa vadede: `total_questions` ve analiz edilen soru sayısını karşılaştır,  
fark varsa kullanıcıya "PDF çok büyük, bölüp tekrar yükleyin" mesajı ver.

---

## Detay: K-2 — Kısmi Parse Atlanıyor (DÜZELTİLDİ)

**Eski kod:**
```python
# Herhangi 1 satır varsa → TÜM analiz atlanıyor
already_parsed = {r["document_id"] for r in (parsed_ids_resp.data or [])}
if aid in already_parsed:
    continue
```

**Senaryo:** 100 sorulu PDF için 50 soru parse edilmiş, sistem çöktü.  
`parse-all` tekrar çalıştırıldığında → 50/100 sonuç var → "zaten parse edildi" → ATLANIYOR.

**Yeni kod:**
```python
# count-based: sgs_questions count < sgs_analyses.questions count ise yeniden parse
if expected > 0 and already >= expected:
    skipped += 1
    continue
```

---

## Detay: K-3 — Belirsiz Sorular (DÜZELTİLDİ)

AI'ın `lesson_confidence < 0.6` dediği sorular `subject = "Belirsiz"` olarak işaretlenir.  
Parse anında `_resolve_lesson_for_topic(topic, "")` çözüm bulamazsa → `continue` (kayıp).

**Eski davranış:** `logger.debug` → production loglarında görünmüyor.  
**Yeni davranış:** `logger.warning` + `belirsiz_skipped` sayacı response'a eklendi:
```json
{
  "questions_created": 95,
  "failed_count": 5,
  "belirsiz_skipped": 5
}
```

---

## Detay: K-4 — INSERT Doğrulanmıyor (DÜZELTİLDİ)

**Eski kod:**
```python
supabase.table("sgs_questions").insert(to_insert).execute()
# Kaç satır yazıldı? Bilinmiyor.
```

**Yeni kod:**
```python
insert_resp = supabase.table("sgs_questions").insert(to_insert).execute()
inserted = len(insert_resp.data or [])
if inserted < len(to_insert):
    logger.warning(f"INSERT eksik: beklenen={len(to_insert)}, yazılan={inserted}")
```

**Not:** Supabase PostgREST büyük payload'larda (> ~5MB) 413 döner.  
`to_insert` her satır ~200 byte → 10.000 soru ≈ 2MB → sınır uzak ama izlenmeli.

---

## Detay: K-5 — Supabase 1000 Satır Limiti (DÜZELTİLDİ)

**Eski kod:**
```python
parsed_ids_resp = supabase.table("sgs_questions").select("document_id").execute()
# PostgREST varsayılan: ilk 1000 satır döner
```

Eğer `sgs_questions` > 1000 satır içeriyorsa, bazı `document_id`'ler `already_parsed` kümesine girmez  
→ o analizler "parse edilmemiş" sayılır → gereksiz yeniden parse.

**Yeni kod:**
```python
sq_resp = supabase.table("sgs_questions").select("document_id").limit(50000).execute()
```

---

## Detay: K-6 — TTS 429 Silent Skip (DÜZELTİLDİ)

**Production log:**
```
[video] 87415ddf-... sahne 0 TTS hatası: Error code: 429 - insufficient_quota
```

**Eski davranış:**
- Exception yakalanıyor
- Sadece `logger.error` yazıyor
- Sahne durumu güncellenmiyordu
- Job `rendering` statüsüne geçiyor, ses eksik video oluşturulmaya çalışılıyor

**Yeni davranış:**
```python
except OpenAIRateLimitError as quota_err:
    logger.error(f"[video] {job_id} TTS kota hatası (429): {quota_err}")
    _set_status(job_id, "failed", {
        "error_message": "OpenAI TTS kotası tükendi (429 insufficient_quota). API kota limitinizi kontrol edin."
    })
    return  # Pipeline hemen durduruluyor
except Exception as e:
    logger.error(...)
    sb.table("video_scenes").update({"status": "tts_failed"}).eq("id", scene_row["id"]).execute()
```

---

## Detay: K-7 — Remotion `ready_for_review` Yanılgısı (DÜZELTİLDİ)

**Production log:**
```
[video] Health check başarısız: The read operation timed out
[video] Remotion render hatası: Remotion sunucusuna ulaşılamıyor (...)
```

**Eski davranış:**
- Status: `ready_for_review` + error_message
- Frontend: "Video incelemeye hazır" gösteriyor
- Kullanıcı: video bekleniyor, gerçekte render başarısız

**Yeni davranış:**
- Status: `failed` + açık hata mesajı
- Kullanıcı net olarak hatayı görüyor
- "Yeniden Dene" butonuna tıklayabilir

---

## Parse Hattı — Soru Sayı Akışı

```
PDF Dosyası
    ↓
load_pdf() → pdf_text (tüm sayfalar)
    ↓
analyze_sgs_pdf() → text_chunk[:90_000]   ← K-1 KESİM NOKTASI
    ↓
OpenAI LLM → questions[] (JSON)
    ↓ subject="Belirsiz" olanlar
    ↓ lesson_confidence < 0.6
    ↓
create_analysis() → sgs_analyses.questions (JSONB)   ← Tam analiz burada
    ↓
parse_questions_by_ranges()
    ↓ Belirsiz+topic_map eşleşmesi yoksa → skip   ← K-3
    ↓ INSERT → sgs_questions table               ← K-4 doğrulama
    ↓
Dashboard (get_areas_from_sgs_questions)
```

---

## Eylem Listesi

| # | Eylem | Öncelik | Durum |
|---|-------|---------|-------|
| A-1 | K-2 düzeltmesi deploy et | P0 | ✅ Hazır |
| A-2 | K-3/K-4/K-5 düzeltmesi deploy et | P0 | ✅ Hazır |
| A-3 | TTS 429 fix deploy et | P0 | ✅ Hazır |
| A-4 | Remotion fail fix deploy et | P1 | ✅ Hazır |
| A-5 | `parse-all` çalıştır (kısmi parse'ları tamamla) | P0 | Bekliyor |
| A-6 | `reclassify` çalıştır (topic_map güncellemesi) | P1 | Bekliyor |
| A-7 | Chunk parse implementasyonu (K-1) | P2 | Planlanıyor |
