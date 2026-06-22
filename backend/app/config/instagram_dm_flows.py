"""Instagram DM karşılama ve menü akış tanımları.

Sonraki aşamada panelden düzenlenebilir hale getirilecek.
Şimdilik bu dosyadan yönetilir.
"""

WELCOME_MESSAGE = """Merhaba 🌿 Adım Müşavir-SGS/Eğitim Koçu'na hoş geldiniz.

Mesajınız bize ulaştı. Ekibimiz en kısa sürede sizinle ilgilenecek ve dönüş sağlayacaktır.

Bu sırada aşağıdaki seçeneklerden size uygun olanı seçebilirsiniz:

1️⃣ Randevu Almak İstiyorum
2️⃣ Eğitimler Hakkında Bilgi Almak İstiyorum
3️⃣ Çıkmış Sorulara Ulaşmak İstiyorum
4️⃣ Web Sitesini İncelemek İstiyorum
5️⃣ YouTube Kanalını Ziyaret Etmek İstiyorum

Ayrıca beklerken web sitemizi ve eğitim içeriklerimizi inceleyebilirsiniz:

🌐 https://www.adimmusavir.com/

🎥 https://www.youtube.com/@adimmusavir

Size yardımcı olmaktan memnuniyet duyarız. 😊"""

FALLBACK_MESSAGE = """Mesajınızı aldık 🌿 Size daha doğru yardımcı olabilmemiz için lütfen aşağıdaki seçeneklerden birini yazın:

1️⃣ Randevu
2️⃣ Bilgi
3️⃣ Çıkmış Sorular
4️⃣ Web Sitesi
5️⃣ YouTube"""

# Her flow: keywords (küçük harf, stripped), crm_status, crm_interest, response
FLOWS = [
    {
        "keywords": ["1", "randevu", "randevu almak istiyorum", "randevu al", "randevu istiyorum"],
        "crm_status": "appointment_requested",
        "crm_interest": "randevu",
        "response": "Elbette 🌿 Randevu oluşturabilmemiz için adınızı, telefon numaranızı ve görüşmek istediğiniz konuyu yazabilir misiniz?",
    },
    {
        "keywords": ["2", "bilgi", "eğitim", "bilgi almak istiyorum", "bilgi istiyorum", "eğitim hakkında"],
        "crm_status": "info_requested",
        "crm_interest": "bilgi",
        "response": """Tabii 🌿 Hangi konuda bilgi almak istersiniz?

• SGS Akademi
• SMMM/YMM hazırlık
• Mali müşavirlik danışmanlığı
• Şirket kuruluşu / muhasebe hizmetleri""",
    },
    {
        "keywords": ["3", "çıkmış sorular", "soru", "sorular", "çıkmış", "çıkmış sorulara ulaşmak istiyorum"],
        "crm_status": "document_requested",
        "crm_interest": "cikmis_sorular",
        "response": """Elbette 🌿 Çıkmış sorular için hangi alanı istiyorsunuz?

• SGS
• SMMM
• YMM
• Genel Muhasebe
• Vergi Hukuku""",
    },
    {
        "keywords": ["4", "web sitesi", "site", "web", "website"],
        "crm_status": None,
        "crm_interest": None,
        "response": "Web sitemizi buradan inceleyebilirsiniz 🌐\nhttps://www.adimmusavir.com/",
    },
    {
        "keywords": ["5", "youtube", "kanal", "video", "youtube kanalı"],
        "crm_status": None,
        "crm_interest": None,
        "response": "YouTube kanalımızdan eğitim ve bilgilendirme içeriklerimizi takip edebilirsiniz 🎥\nhttps://www.youtube.com/@adimmusavir",
    },
]
