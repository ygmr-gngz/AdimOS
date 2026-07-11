# Gerçek Kayıp Dosyalar

**Tarih:** (doldurulacak)  
**Kaynak:** GET /storage-integrity → `gercek_kayip` dizisi

Gerçek kayıp = storage'da hiçbir yerde yok (ne slug'la ne ham isimle).
Bu dosyalar için kullanıcının PDF'i tekrar bulup "Yeniden Yükle" butonu ile bağlaması gerekir.

---

## Kayıp Dosya Listesi (doldurulacak)

| Doküman ID | Dosya Adı | Yükleme Tarihi | Neden Kayıp |
|------------|-----------|----------------|-------------|
| (storage-integrity sonucundan gelecek) | | | |

---

## Olası Nedenler

1. **Eski upload akışı crash'i**: `upload_document` DB kaydı oluşturup storage'a yazarken
   exception aldı → kayıt kaldı, dosya girilmedi. Düzeltme: storage başarısızsa kaydı sil.

2. **Signed URL PUT başarısız**: `create_upload_url` çağrıldı (kayıt oluştu), ama frontend
   PUT isteği başarısız oldu → `register_upload` çağrılmadı veya çağrıldı ama dosya yoktu.

3. **Elle silme**: Dosya storage'dan manuel olarak silindi ama DB kaydı kaldı.

---

## Kullanıcı Aksiyonu

Kart üzerinde "Yeniden Yükle" turuncu butonuna tıkla → aynı PDF'i yükle.
Sorular ve seçimler korunur — sadece kaynak dosya yeniden bağlanır, yeniden indekslenir.
