# Yayılım Kontrolü Raporu

**Tarih:** 2026-07-07  
**Tetikleyici:** Konu Dağılımı ekranında "Denklem/Denklemler", "Matematik (konu)" ve "? (30)" gözlemlendi.

---

## Canlıda Ne Var, Ne Yok?

| Özellik | Durum | Kanıt |
|---------|-------|-------|
| Ders (lesson) kapalı listesi (17 ders) | ✅ CANLI | `analyzer.py:SGS_LESSONS` — LLM bu listeden seçiyor |
| Ders → konu haritası (`_TOPIC_LESSON_MAP`) | ✅ CANLI | `sgs_repo.py` 130+ giriş, `reclassify_all_questions` + `parse_questions_by_ranges` çağrıyor |
| **Konu adı normalizasyonu** (canonical topic) | ❌ CANLI DEĞİLDİ | `_TOPIC_CANONICAL_MAP` bu sprint'te eklendi |
| "?" (Belirsiz) soru yönetim UI'ı | ❌ YOK | Endpoint eklendi; UI sprint kapsamı dışında |
| Topic adı başlık harfi normalizasyonu | ❌ CANLI DEĞİLDİ | `_canonical_topic()` bu sprint'te eklendi |

---

## Neden "Denklem" + "Denklemler" Ayrı Görünüyor?

`_TOPIC_LESSON_MAP` yalnızca **topic → ders** eşlemesi yapar. İki konu adı da Matematik dersine doğru atanıyor ama `sgs_questions.topic` alanı LLM'nin ürettiği serbest metin olarak kalıyor. "denklemler" → "Matematik" doğru ders, ama `topic` alanı "Denklemler" olarak yazılıyor.

**Düzeltme:** `_TOPIC_CANONICAL_MAP` + `_canonical_topic()` fonksiyonu eklendi. `reclassify_all_questions()` artık hem dersi hem konu adını normalize ediyor.

---

## Neden "Matematik" Konu Olarak Görünüyor?

LLM bazen konu adı üretmek yerine ders adını yazıyor. `_TOPIC_LESSON_MAP`'te `"matematik": "Matematik"` girişi dersi doğru eşleştiriyor ama `sgs_questions.topic = "Matematik"` olarak kalıyor.

**Düzeltme:** `_TOPIC_CANONICAL_MAP`'e `"matematik": None` eklendi. `_canonical_topic("Matematik")` → `"Belirsiz"` döner. `reclassify_all_questions()` çalışınca bu soru "Belirsiz" konuya taşınır.

---

## Neden "oran" Küçük Harf?

LLM küçük harf üretiyor. `_canonical_topic("oran")` → `"Oran-Orantı"` dönecek (artık haritada var). `reclassify_all_questions()` çalışınca normalize olur.

---

## Sonraki Adım

`POST /api/v1/sgs/questions/reclassify` çalıştırılmalı. Bu endpoint:
1. Tüm `sgs_questions` satırlarını tarar
2. Yanlış ders → doğru derse taşır
3. Varyant konu adları → canonical forma çevirir
4. Rapor döner (kaç satır değişti, hangi hareket)

**Dry-run için:** `GET /api/v1/sgs/topics/dry-run-merge` önce çalıştırılabilir (veri değişmez).
