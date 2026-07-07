# Sorgu Hijyeni Envanteri

**Tarih:** 2026-07-07  
**Sprint:** Sorgu Hijyeni v1  
**Tetikleyici:** Production WriteTimeout — `generated_contents` limitsiz SELECT * (17:11 canlı traceback)

---

## Liste endpoint'leri — Risk Değerlendirmesi

| Tablo | Fonksiyon | Endpoint | Öncesi | Sonrası | Risk | Durum |
|-------|-----------|----------|--------|---------|------|-------|
| `generated_contents` | `list_contents()` | `GET /api/v1/content` | `select("*")` limitsiz | `select(_LIST_FIELDS)` + `range(0,49)` | **KRİTİK** — WriteTimeout kanıtlı | ✅ DÜZELTİLDİ |
| `video_jobs` | `list_jobs()` | `GET /api/v1/video/jobs` | `select(_LIST_FIELDS)` + `limit(50)` | değişmedi | Zaten güvenli | ✅ SORUN YOK |
| `documents` | `get_documents()` | `GET /api/v1/documents` | `select("*")` limitsiz | `select("*")` + `limit(200)` | Orta — tablo büyüyor | ✅ DÜZELTİLDİ |
| `notifications` (liste) | satır içi | `GET /api/v1/notifications` | `select("*")` + `limit(80)` | değişmedi | Kabul edilebilir | ✅ SORUN YOK |
| `notifications` (sayaç) | satır içi | `GET /api/v1/notifications/unread-count` | `select("id")` + Python `len()` | `select("id", count="exact")` + `resp.count` | Düşük — ama DB count doğru yöntem | ✅ DÜZELTİLDİ |
| `leads` | `list_leads()` | `GET /api/v1/crm/leads` | `select("*")` limitsiz | — | Düşük (CRM tablosu küçük) | ⚠️ İZLENİYOR |
| `briefs` | `list_briefs()` | `GET /api/v1/briefs` | `select("*")` limitsiz | — | Düşük (tablo küçük) | ⚠️ İZLENİYOR |
| `students` | `list_students()` | `GET /api/v1/students` | `select("*")` limitsiz | — | Düşük (tablo küçük) | ⚠️ İZLENİYOR |
| `sgs_questions` | `get_similar_questions()` | iç çağrı | `select("*")` limitsiz | — | Orta — soru havuzu büyüyebilir | ⚠️ İZLENİYOR |
| `sgs_question_ranges` | çeşitli | iç çağrı | `select("*")` limitsiz | — | Düşük (konfigürasyon tablosu, satır sayısı sabite yakın) | ✅ SORUN YOK |
| `conversations` | `list_conversations()` | agent endpoint | `select("*")` limitsiz | — | Düşük (kullanıcı başına az konuşma) | ⚠️ İZLENİYOR |
| `messages` | `list_messages()` | agent endpoint | `select("*")` limitsiz | — | Orta — konuşma başına çok mesaj olabilir | ⚠️ İZLENİYOR |
| `chunks` | `get_chunks_by_document()` | iç çağrı | `select("*")` limitsiz | — | Düşük — document_id filtreli; büyük chunk varsa risk | ⚠️ İZLENİYOR |
| `instagram_conversations` | satır içi | webhook | `select("*")` limitsiz | — | Düşük (küçük tablo) | ⚠️ İZLENİYOR |
| `instagram_messages` | satır içi | webhook | `select("*")` limitsiz | — | Orta — büyüyebilir | ⚠️ İZLENİYOR |
| `user_profiles` | satır içi | `GET /api/v1/users` | `select("*")` limitsiz | — | Düşük (tek kullanıcı sistemi) | ✅ SORUN YOK |

---

## Detay endpoint'leri — Durum

Tekil kayıt döndüren endpoint'lerde `select("*")` kabul edilebilir; `eq("id", ...)` filtresi zaten tek satır döndürür.

| Fonksiyon | Tablo | Değerlendirme |
|-----------|-------|---------------|
| `get_content(id)` | `generated_contents` | ✅ Doğru — detay için tam veri |
| `get_document(id)` | `documents` | ✅ Doğru |
| `get_lead(id)` | `leads` | ✅ Doğru |
| `get_analysis(id)` | `sgs_analyses` | ✅ Doğru |

---

## Sayaç sorguları — Durum

| Endpoint | Öncesi | Sonrası |
|----------|--------|---------|
| `GET /notifications/unread-count` | `select("id")` → Python `len()` | `select("id", count="exact")` → `resp.count` |

Supabase `count="exact"` parametresi PostgreSQL `COUNT(*)` sorgusuna dönüşür; satırları transfer etmez.

---

## Genel Koruma Katmanı

**`main.py` exception handler genişletildi:**
- Öncesi: sadece `LocalProtocolError` / `ConnectionTerminated` yakalanıyordu
- Sonrası: `httpx.TimeoutException` de yakalanıyor → istemciye 504 + sade mesaj; ham traceback sızması engellendi

**Önerilen ama bu sprint'e alınmayan:**
- Supabase istemcisinde global timeout ayarı (varsayılan = sonsuz) — `app/db/supabase.py` içinde `timeout=httpx.Timeout(10.0)` eklenmesi önerilir
- `conversations` / `messages` tabloları için limit + sütun diyeti (agent UI kullanımı arttıkça)
