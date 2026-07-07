# İz Sürüm Raporları

**Tarih:** 2026-07-07

---

## Sorun 2 — Almanca'daki İş Hukuku Sorusu: Kök Neden

### Yol Haritası

```
PDF yükleme
  → _sgs_pipeline_background
    → analyze_sgs_pdf(text, pdf_name)
      → LLM: subject="Almanca" (kapalı liste — 17 dersten seçti)
             topic="İş Sözleşmesi" (serbest metin)
      → parse_questions_by_ranges(analysis_id)
        → _resolve_lesson_for_topic("İş Sözleşmesi", range_lesson or "Almanca")
           → "iş sözleşmesi" _TOPIC_LESSON_MAP'te var → "İş ve Sosyal Güvenlik Hukuku"
```

### Neden Almanca'ya Düştü?

İki senaryo mümkün:

**A) Aralık yapılandırılmadı:** PDF için `sgs_question_ranges` tanımlanmadıysa `parse_questions_by_ranges` otomatik parse modunda çalışır ve `ai_subject` (LLM'nin "Almanca" yanıtı) kullanılır. Eğer topic "İş Sözleşmesi" ise `_resolve_lesson_for_topic` doğru derse taşır — ama bazı Almanca kelimeleri içeren İş Hukuku soruları için LLM "Almanca" seçmiş ve topic de Almanca dil bilgisi gibi görünmüş olabilir.

**B) Konu haritasında eksik:** Eğer bu sorunun topic alanı "Almanca" (ders adı) ise `_TOPIC_LESSON_MAP`'te `"almanca": "Almanca"` var — yani Almanca olarak kalıyor. Ama artık `_TOPIC_CANONICAL_MAP`'te `"almanca": None` → `_canonical_topic("almanca")` → `"Belirsiz"`, ve `reclassify` dersi de düzeltiyor.

### Teşhis Komutu

```
GET /api/v1/sgs/questions?lesson=Almanca
```

Listelenen sorularda iş hukuku içerikli olanı bulun; topic alanına bakın.

### Düzeltme

```
POST /api/v1/sgs/questions/reclassify
```

Bu, tüm yanlış ders atamalı sorular için `_resolve_lesson_for_topic` uygular. İş hukuku sorusu "İş ve Sosyal Güvenlik Hukuku"na taşınır (topic "iş sözleşmesi" ise haritada var).

Eğer bu sorunun topic'i haritada yoksa:
```
PATCH /api/v1/sgs/questions/{question_id}
{"lesson_name": "İş ve Sosyal Güvenlik Hukuku", "topic": "İş Sözleşmesi"}
```

---

## Sorun 3 — Onaylanan Görsel İçerik Otomasyonu'nda Neden Görünmüyordu?

### Sistem Mimarisi

İki bağımsız tablo:
- `video_jobs` → Video Prodüksiyon sayfası
- `generated_contents` → İçerik Otomasyonu sayfası

### Kök Neden

`POST /video/jobs/{job_id}/approve` → sadece `video_jobs.status = "approved"` güncelliyordu. `generated_contents` tablosuna hiçbir kayıt yazılmıyordu.

### Düzeltme

`approve_job` endpoint'ine `_bridge_to_content_automation(job)` eklendi. Onay anında:
- `generated_contents` tablosuna `status="approved"`, `type=job.type`, `title=job.title`, `topic=f"video_job:{job_id}"` ile kayıt eklenir
- `topic` alanındaki `video_job:{id}` sentinel'i duplicate önleme için kullanılır
- `video_url` varsa (render tamamlandıysa) aktarılır

### Backfill (Geçmiş Onaylı Video Joblar)

Geçmişte onaylanmış ama `generated_contents`'a düşmemiş video job'lar için backfill gerekir.

**Dry-run sorgu (Supabase SQL):**
```sql
SELECT id, title, type, video_url, status
FROM video_jobs
WHERE status = 'approved'
AND id NOT IN (
  SELECT REGEXP_REPLACE(topic, 'video_job:', '')
  FROM generated_contents
  WHERE topic LIKE 'video_job:%'
)
ORDER BY updated_at DESC;
```

Bu sorgu kaç satır döndürüyorsa o kadar kayıt backfill edilmesi gerekir. **Onay sonrası uygularım.**

---

## Sorun 4 — İş Hukuku PDF: 0 Soru

### Teşhis Komutu

```
GET /api/v1/sgs/documents/sgs-status
```

`sgs_diagnosis = "zero_questions"` olan dokümanlar listelenir.

### Olası Nedenler (öncelik sırasıyla)

1. **Taranmış PDF:** `pypdf` metin çıkaramadı → `len(text) < 100` → pipeline sessizce döndü. Log'da: `"PDF metin çıkarılamadı — taranmış/görüntü PDF"`. OCR yoktur; kullanıcı metin katmanlı PDF sağlamalı.

2. **İsim çakışması:** Aynı pdf_name ile başka bir analiz zaten vardı (`find_analysis_by_pdf_name`) → pipeline atladı. **Şimdi düzeltildi:** 0-sorulu mevcut analiz artık yeniden analiz tetikler.

3. **Soru formatı tanınmadı:** LLM "1.", "A)", "a)" gibi formatları tanımadı → `total_questions = 0`. Çözüm: SGS analyze endpoint'ini `force=True` ile doğrudan çalıştırmak.

4. **Dosya adı sanitizasyonu çakışması:** `_SAFE_NAME_RE.sub('_', filename)` → Türkçe karakterler `_` oldu → farklı PDF'ler aynı `safe_name`'e dönüştü.

### Yeniden İşleme Komutu

Mevcut doküman ID'si ile:
```
POST /api/v1/documents/{doc_id}/reindex
```

Veya SGS endpoint'i ile (`force=True`):
```
POST /api/v1/sgs/analyze?force=true   (dosya yeniden yükle)
```

---

## Sorun 5 — PDF Listesinde Eksik Belgeler

### Kök Neden

`knowledge/page.tsx` varsayılan sekme `'knowledge_center'` idi. SGS Akademi sekmesinden veya `sync-sgs` ile oluşturulan dokümanlar `source_module="sgs_academy"` → "Bilgi Merkezi" sekmesinde GÖRÜNMÜYOR.

### Düzeltme

Varsayılan sekme `'all'` olarak değiştirildi. İlk yüklemede tüm dokümanlar görünür.

### Ek Teşhis

```
GET /api/v1/documents?source_module=  (boş = tümü)
```

DB'deki toplam doküman sayısını UI'daki sayıyla karşılaştırın.
