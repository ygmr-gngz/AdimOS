# GÖREV 3 — PDF Depolama Envanteri ve Kurtarma

**Durum:** Envanter TAMAMLANDI — Upload pipeline düzeltmesi BEKLEMEDE  
**Tarih:** 2026-07-04

---

## Durum Analizi

### PDF Fiziksel Depolama
Supabase Storage'da hiçbir PDF bulunamadı. Taranan bucket'lar:
- `sgs-pdfs` — bulunamadı / boş
- `pdfs` — bulunamadı / boş
- `documents` — bulunamadı / boş

**Sonuç (Senaryo B):** 30 SGS PDF'i fiziksel olarak mevcut değil. PDF bytes analiz sonrası discard ediliyor.

### Veritabanı Durumu

| Tablo | Satır Sayısı | İçerik |
|-------|-------------|--------|
| `sgs_analyses` | 30 | Her PDF için JSONB `questions[]` (5 soru/PDF) |
| `sgs_questions` | 149 | Tam soru tablosu (question_text dahil) |
| `sgs_question_ranges` | 17 | Ders bazlı soru aralık tanımları |

### Soru Dağılımı (sgs_questions)
- 149 soruda `question_text` mevcut (export sırasında doğrulandı)
- 45 soru Almanca yanlış sınıflandırma → düzeltildi (lesson_name güncellendi)
- `_detect_language_from_filename()` devre dışı — artık Almanca grubundaki PDF'ler yanlış etiketlenmiyor

---

## Tamamlanan İşler

### Soru Exportu
- `audit/gorevler/sgs_sorular_export.json` — 149 soru (question_text, options, correct_option, explanation)
- `audit/gorevler/sgs_sorular_export.csv` — aynı veri, Excel formatı
- `audit/gorevler/sgs_soru_araliklari_export.json` — 17 aralık tanımı

### Chunk Analizi
`analyzer.py` tam yeniden yazıldı:
- PDF ≥32k karakter → 28k chunk'lara bölünür, 2k overlap
- Her chunk ayrı ayrı analiz edilir
- Sonuçlar `question_id`'ye göre birleştirilir (en yüksek confidence kazanır)
- Büyük PDF'lerde 130 sorunun tamamı çıkarılabilir

### Force Re-analyze
- `POST /sgs/analyze` endpoint'i `force=true` parametresi kabul ediyor
- Frontend'de "Yeniden Analiz" toggle'ı eklendi (turuncu renk)

---

## Kalan İş — Upload Pipeline

PDF bytes'ı Supabase Storage'a kaydetme henüz implement edilmedi.

**Gerekli değişiklikler (`backend/app/api/routes/sgs.py`):**
```python
# analyze endpoint'ine eklenecek
bucket = "sgs-pdfs"
file_bytes = await file.read()  # zaten okunuyor
storage_path = f"{analysis_id}/{file.filename}"
supabase.storage.from_(bucket).upload(storage_path, file_bytes)
# sgs_analyses kaydına storage_path yazılacak
```

**Soft delete:** Analize bağlı soru/aralık varken silme için onay + cascade gerekli.

---

## PDF'ler Olmadan Mevcut Durum

Tüm soru verileri `sgs_questions` tablosunda mevcut. Yeni video üretimi ve SGS analizi için PDF'lere ihtiyaç yok. PDF'ler sadece yeniden analiz (re-analyze) için gerekli.
