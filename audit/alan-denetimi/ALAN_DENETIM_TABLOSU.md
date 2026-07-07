# Alan Denetim Tablosu

**Tarih:** 2026-07-07  
**Durum:** CANLI VERİ — 56 doküman, 271 soru

---

## Ders Bazında Soru Dağılımı (DB'de olan)

| Ders | Soru Sayısı (DB) | Durum |
|------|-----------------|-------|
| Türkçe | 37 | ✅ |
| Mali Tablolar Analizi | 36 | ✅ |
| Matematik | 31 | ✅ |
| Tarih - Genel Kültür | 30 | ✅ |
| İktisat | 30 | ✅ |
| Muhasebe Standartları | 28 | ✅ |
| İngilizce | 22 | ✅ |
| Maliye | 22 | ✅ |
| Maliyet Muhasebesi | 15 | ✅ |
| Vergi Hukuku | 13 | ✅ |
| Finansal Muhasebe | 6 | ⚠️ Az |
| Almanca | 1 | ⚠️ Az |
| **Ticaret Hukuku** | **0** | ❌ Eksik |
| **Borçlar Hukuku** | **0** | ❌ Eksik |
| **İş ve Sosyal Güvenlik Hukuku** | **0** | ❌ Eksik |
| **Meslek Hukuku** | **0** | ❌ Eksik |
| **Muhasebe Denetimi** | **0** | ❌ Eksik |

---

## Doküman Sayımı

| Kategori | Sayı |
|----------|------|
| Toplam doküman | 56 |
| SGS analizli | 35 |
| SGS analizsiz | **21** |

---

## SGS Analizsiz Dokümanlar (Kök Neden Araştırması Gerekli)

| Dosya Adı | Kaynak | Olası Neden |
|-----------|--------|-------------|
| SGS-TİCARET HUKUKU-FUAT HOCA.pdf | knowledge_center | Taranmış PDF veya pipeline hatası |
| SGS.FİN.TAB.ANALİZİ FUAT HOCA.pdf | knowledge_center | Türkçe dosya adı encoding |
| SGS-MALİYE.pdf | knowledge_center | Olası duplicate (sgs_academy'de de var) |
| SGS-İKTİSAT.pdf | knowledge_center | Olası duplicate |
| 10.MUH.STANDARTLARI-FUAT HOCA.pdf | knowledge_center | Pipeline hatası |
| 9.VERGİ.HUK.-FUAT HOCA.pdf | knowledge_center | Pipeline hatası |
| 4-MALİYET-FUAT HOCA.pdf | knowledge_center | Pipeline hatası |
| 1.FİNANSAL MUHASEBE-FUAT HOCA.pdf | knowledge_center | Pipeline hatası |
| 7.MESLEK HUKUKU-FUAT HOCA.pdf | knowledge_center | Pipeline hatası |
| 2.FİN.TAB.ANALİZİ FUAT HOCA.pdf | knowledge_center | Pipeline hatası |
| SGS-İKTİSAT.pdf | sgs_academy | SGS Akademi kayıtlı (veri içeriyor?) |
| 3.DENETİM-FUAT HOCA.pdf | knowledge_center | Pipeline hatası |
| 10.MUH.STANDARTLARI-FUAT_HOCA.pdf | sgs_academy | SGS Akademi kayıtlı |
| 8-İŞ VE SOS.GÜV.HUKUKU.pdf (x2) | knowledge_center | Duplicate kayıt! |
| SGS-MALİYE.pdf | sgs_academy | SGS Akademi kayıtlı |
| 6.TİCARET HUKUKU-FUAT HOCA.pdf | knowledge_center | Pipeline hatası |
| SGS-MALİYET-FUAT HOCA.pdf (x3) | knowledge_center | Duplicate kayıt! |
| SGS-MALİYET-FUAT_HOCA.pdf | knowledge_center | Duplicate kayıt! |

---

## Uyuşmazlık Deseni Analizi

### Desen 1: Doküman var, soru 0 → Pipeline bu dokümanları işlemedi
- **Kök neden A:** Yükleme sırasında `_sgs_pipeline_background` arka planda hata verdi; log'da izlendi ama kullanıcıya görünmedi
- **Kök neden B:** Taranmış PDF — `pypdf` metin çıkaramadı (`len(text) < 100`)
- **Kök neden C:** Dosya adı encode sorunu — `_SAFE_NAME_RE.sub` ile Türkçe karakterler `_` oldu, `find_analysis_by_pdf_name` başka PDF zanetti

### Desen 2: Duplicate dokümanlar
- `8-İŞ VE SOS.GÜV.HUKUKU.pdf` 2 kayıt, `SGS-MALİYET-FUAT HOCA.pdf` 3+ kayıt
- Aynı dosya defalarca yüklenmiş, her seferinde `sgs_analysis_id=null` olarak kalmış

---

## Eksik Dersler → Backfill Planı

Sıfır soru olan 5 ders için ilgili dokümanları `POST /api/v1/documents/{doc_id}/reindex` ile yeniden işle.

**Öncelik sırası:**
1. İş ve Sosyal Güvenlik Hukuku → `8-İŞ VE SOS.GÜV.HUKUKU.pdf`
2. Ticaret Hukuku → `SGS-TİCARET HUKUKU-FUAT HOCA.pdf`
3. Meslek Hukuku → `7.MESLEK HUKUKU-FUAT HOCA.pdf`
4. Muhasebe Denetimi → `3.DENETİM-FUAT HOCA.pdf`
5. Borçlar Hukuku → PDF henüz yüklenmemiş (Sorun 1 ile bağlantılı)
