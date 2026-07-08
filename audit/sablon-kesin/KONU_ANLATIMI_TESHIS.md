# Konu Anlatımı Endpoint Teşhis Raporu

**Tarih:** 2026-07-08  
**Hata:** NameError: name 'get_supabase_client' is not defined  
**Endpoint:** POST /api/v1/sgs/topics/{topic}/generate-konu-anlatimi  
**Railway log satırı:** File "/app/app/api/routes/sgs.py", line 869

---

## Kök Neden

`generate_konu_anlatimi` ve `topic_source_content` fonksiyonları,  
diğer fonksiyonlar gibi `from app.db.supabase import get_supabase_client` yerel  
import'unu yapmadan doğrudan `get_supabase_client()` çağırıyordu.

`sgs.py` top-level import'larında `get_supabase_client` yoktur —  
tüm diğer fonksiyonlar bunu local import ile alır.

## Düzeltme (2026-07-08)

Her iki fonksiyonun ilk satırına eklendi:
```python
from app.db.supabase import get_supabase_client
```

## Statik Analiz Sonucu

AST tabanlı kontrol çalıştırıldı — `get_supabase_client` eksik çağrısı kalmadı:
```
OK: topic_source_content has local import + calls at [794]
OK: generate_konu_anlatimi has local import + calls at [871]
No missing get_supabase_client imports found
```

## Süreç İhlali

Bu endpoint canlıda test edilmeden "tamamlandı" raporlandı.  
**Kural (kalıcı):** Yeni eklenen her endpoint, rapordan önce canlıda en az 1 kez çağrılmalı ve yanıt rapora eklenmeli.

## Canlı Test Sonrası Beklenti

```bash
curl -X POST "https://adimos-production.up.railway.app/api/v1/sgs/topics/Anonim%20%C5%9Eirket/generate-konu-anlatimi" \
  -H "Authorization: Bearer ..."
```

Beklenen yanıt (kaynak varsa):
```json
{"job_id": "...", "status": "...", "chunk_count": N, ...}
```

Kaynak yoksa:
```json
{"detail": "'Anonim Şirket' konusuna ait kaynak içerik bulunamadı. Önce bu konuya ait PDF yükleyin."}
```

## Downstream Akış

1. NameError yok → endpoint çalışıyor
2. Kaynak kontrolü: `sgs_questions` → `document_id` → `chunks`
3. Chunk varsa: `video_jobs` INSERT (production_type=konu_anlatimi, status=pending)
4. Video prodüksiyon sayfasında iş görünür
5. Kaynak yoksa: 422 + "PDF yükleyin" mesajı (Ticaret Hukuku için muhtemelen bu)
