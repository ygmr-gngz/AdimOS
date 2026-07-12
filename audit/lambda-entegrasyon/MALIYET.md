# Lambda Entegrasyon — Maliyet

**Tarih:** 2026-07-12

---

## Bileşen Maliyetleri

| Bileşen | Birim | Açıklama |
|---------|-------|----------|
| Lambda işlem | $0.0000166667 / GB-sn | 3 GB × ~120s/video ≈ $0.006/video |
| S3 storage (bundle) | ~$0.001/ay | ~50 MB bundle, kalıcı |
| S3 render çıktısı | eser | Lifecycle 7 gün sonra siler |
| Supabase storage | mevcut plan | video-outputs bucket |
| Railway Remotion | ~$5/ay | 256 MB → mevcut 8 GB'dan düşürülecek |

**Tahmini toplam (50 video/ay):** ~$5.30/ay (eski: ~$40/ay + crash)

---

## Günlük Guardrail

`DAILY_COST_LIMIT_USD=5.0` env değişkeni ile yönetilir.  
Aşıldığında `/render` endpoint'i `429` döner ve log çıkar:

```
[lambda] GUARDRAIL Günlük maliyet $5.023 — limit $5.0
```

Limiti artırmak için Railway → Remotion → Variables → `DAILY_COST_LIMIT_USD=10`.

---

## Gerçek Maliyet Takibi

Lambda Bridge her render sonunda maliyet loglar:

```
[lambda] render tamam (87s): composition=QuizVideo maliyet=$0.0062 günlük=$0.0124
```

İleride `video_jobs.cost_lambda_usd` kolonu (migration 011) DB'ye yazılacak.  
Backend callback handler'ında `cost_lambda_usd` alanını kaydet:

```python
# video.py — render-callback handler
if payload.get("cost_lambda_usd"):
    supabase.table("video_jobs").update({
        "cost_lambda_usd": payload["cost_lambda_usd"]
    }).eq("id", job_id).execute()
```

---

## Kota Artışı Maliyeti

| Senaryo | MAX_CONCURRENT | framesPerLambda (25dk) | Render süresi |
|---------|---------------|----------------------|---------------|
| Şu an (kota 8) | 8 | 5625 | ~8 dk |
| Kota 200 sonrası | 200 | 225 | ~2 dk |

Kota onaylanınca `MAX_CONCURRENT_LAMBDAS=200` yap → tek değişiklik bu.
