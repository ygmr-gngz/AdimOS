# Konu Birleştirme Dry-Run Raporu

**Tarih:** 2026-07-07  
**Durum:** KOD HAZIR — VERİ DEĞİŞİKLİĞİ ONAY BEKLİYOR

---

## Otomatik Birleştirme (Canonical Map — Onay Gerekmez)

`POST /api/v1/sgs/questions/reclassify` komutu şu kanonik dönüşümleri yapar:

| Mevcut Konu Adı | Canonical Karşılığı | Etkilenen Ders |
|-----------------|---------------------|----------------|
| `denklemler` | **Denklem** | Matematik |
| `fonksiyonlar` | **Fonksiyon** | Matematik |
| `problemler` | **Problem** | Matematik |
| `diziler` | **Dizi** | Matematik |
| `matrisler` | **Matris** | Matematik |
| `logaritmalar` | **Logaritma** | Matematik |
| `eşitsizlikler` | **Eşitsizlik** | Matematik |
| `anlatım bozuklukları` | **Anlatım Bozukluğu** | Türkçe |
| `kelime türleri` | **Sözcük Türleri** | Türkçe |
| `oran` | **Oran-Orantı** | Matematik |
| `oran ve orantı` | **Oran-Orantı** | Matematik |
| `yevmiye kayıtları` | **Yevmiye** | Finansal Muhasebe |
| `matematik` (konu olarak) | **Belirsiz** | Matematik |
| `türkçe` (konu olarak) | **Belirsiz** | Türkçe |
| `almanca` (konu olarak) | **Belirsiz** | Almanca |

**Soru sayısı değişmez** — sadece `topic` alanı güncellenir.

---

## Fuzzy Birleştirme (Onay Gerekli)

`GET /api/v1/sgs/topics/dry-run-merge` endpoint'i benzerlik ≥%75 olan konu çiftlerini raporlar.

**Örnek beklenen çıktı (tahmini — canlı veriye göre değişir):**

| Ders | Varyant A | Varyant B | Benzerlik | Önerilen Canonical | Etkilenen |
|------|-----------|-----------|-----------|-------------------|-----------|
| Türkçe | Anlatım Bozukluğu | Anlatım Bozuklukları | 0.94 | Anlatım Bozukluğu | ~? soru |
| Matematik | Denklem | Denklemler | 0.92 | Denklem | ~? soru |
| Finansal Muhasebe | Yevmiye | Yevmiye Kaydı | 0.86 | Yevmiye | ~? soru |

**Gerçek rakamlar canlıdan gelir.** Dry-run endpoint'i çalıştırılınca bu tablo doldurulacak.

---

## Birleştirme Akışı

```
1. GET /sgs/topics/dry-run-merge                    → Raporu gör
2. Onay: hangi fuzzy birleştirmeler yapılsın?       → Kullanıcı onaylar
3. POST /sgs/questions/reclassify                   → Canonical map uygulanır (otomatik)
4. Manuel fuzzy birleştirme için POST /sgs/questions/{id} → Tekil soru güncelleme
5. GET /sgs/topics                                  → Konu listesi kontrol
```

---

## Sayım Eşitliği Taahhüdü

Birleştirme işlemi soru SİLMEZ. Yalnızca `topic` alanını günceller. Toplam soru sayısı değişmez.

```
∑ soru (önce) = ∑ soru (sonra)
```

Her `reclassify` çağrısı `total_rows`, `updated_lessons`, `updated_topics` döner — bu değerler ile doğrulama yapılabilir.
