# Sınıflandırma Mini-Test Planı

**Tarih:** 2026-07-07  
**Durum:** TANIM HAZIR — Otomatik çalıştırma henüz implement edilmedi

---

## Test Seti (15 Referans Soru)

| # | Soru Özeti | Beklenen Ders | Beklenen Konu |
|---|-----------|---------------|---------------|
| 1 | "Fiilimsi türleri nelerdir?" | Türkçe | Sözcük Türleri |
| 2 | "x² + 5x + 6 = 0 denkleminin kökleri?" | Matematik | Denklem |
| 3 | "Kıdem tazminatı hesabı: 10 yıl..." | İş ve Sosyal Güvenlik Hukuku | Kıdem Tazminatı |
| 4 | "KDV oranı ve hesaplama yöntemi?" | Vergi Hukuku | KDV |
| 5 | "Ticaret sicili tescil şartları?" | Ticaret Hukuku | Ticaret Sicili |
| 6 | "Bilanço eşitliği: Aktif = ?" | Finansal Muhasebe | Bilanço |
| 7 | "TMS 16 maddi duran varlıklar..." | Muhasebe Standartları | TMS |
| 8 | "Atatürk'ün Kurtuluş Savaşı hedefleri?" | Tarih - Genel Kültür | Kurtuluş Savaşı |
| 9 | "Almanca: Der Artikel beim Nomen..." | Almanca | Grammatik |
| 10 | "Olasılık hesabı: iki zar..." | Matematik | Olasılık |
| 11 | "Bağımsız denetim raporunun unsurları?" | Muhasebe Denetimi | Bağımsız Denetim |
| 12 | "İç kontrol sistemi bileşenleri?" | Muhasebe Denetimi | İç Kontrol |
| 13 | "Arz-talep dengesi değiştiğinde..." | İktisat | Arz |
| 14 | "SMMM mesleki sorumluluk sınırları?" | Meslek Hukuku | Mesleki Sorumluluk |
| 15 | "Sipariş maliyeti yöntemi adımları?" | Maliyet Muhasebesi | Sipariş Maliyeti |

---

## Test Çalıştırma Prosedürü (Manuel)

1. SGS Akademi sayfasında yeni bir test PDF'i yükle (yukarıdaki 15 soruyu içeren)
2. `POST /api/v1/sgs/analyze` → analiz ID'sini al
3. `POST /api/v1/sgs/questions/parse-by-ranges` → sorular `sgs_questions`'a yaz
4. `GET /api/v1/sgs/questions?lesson=&topic=` → her soru için sonuç kontrol

**Başarı Kriteri:**  
- 15 sorunun 13+/15 doğru sınıflandırılması (%87+)
- Hiçbir soru hatalı derse gitmemeli (örn. iş hukuku → Almanca)
- Hiçbir soru ders adını konu olarak almamalı (örn. konu="Matematik")

---

## Sorun 2 Regresyon Testi

Test seti #3 sorusu (kıdem tazminatı):
- LLM `subject` çıktısı `"İş ve Sosyal Güvenlik Hukuku"` olmalı
- `_resolve_lesson_for_topic("kıdem tazminatı", ...)` → `"İş ve Sosyal Güvenlik Hukuku"` ✅ haritada var
- Eğer LLM "Almanca" dönerse → `_resolve_lesson_for_topic` yine de "İş ve Sosyal Güvenlik Hukuku"na çeker

---

## Otomatik Test (Gelecek Sprint)

```python
# backend/tests/test_sgs_classification.py
import pytest

CASES = [
    ("Kıdem tazminatı hesabı ...", "İş ve Sosyal Güvenlik Hukuku", "Kıdem Tazminatı"),
    ("x² + 5x + 6 = 0 kökleri ...", "Matematik", "Denklem"),
    ...
]

def test_reclassify_preserves_correct_lesson():
    from app.db.repositories.sgs_repo import _resolve_lesson_for_topic
    assert _resolve_lesson_for_topic("kıdem tazminatı", "Almanca") == "İş ve Sosyal Güvenlik Hukuku"
    assert _resolve_lesson_for_topic("denklem", "Genel") == "Matematik"
    assert _resolve_lesson_for_topic("iş sözleşmesi", "Almanca") == "İş ve Sosyal Güvenlik Hukuku"

def test_canonical_topic():
    from app.db.repositories.sgs_repo import _canonical_topic
    assert _canonical_topic("denklemler") == "Denklem"
    assert _canonical_topic("matematik") == "Belirsiz"
    assert _canonical_topic("oran") == "Oran-Orantı"
    assert _canonical_topic("Anlatım Bozukluğu") == "Anlatım Bozukluğu"  # zaten canonical
```
