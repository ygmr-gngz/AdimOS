from openai import OpenAI
from app.core.config import settings
import json

_client = OpenAI(api_key=settings.OPENAI_API_KEY)

_BRAND_CTX = """
Kanal: Adım Müşavir
Hedef kitle: SMMM / YMM sınavına hazırlanan adaylar, muhasebe meraklıları, yeni girişimciler, şirket kurucu adayları
Konu alanları: Mali müşavirlik, muhasebe, vergi (KDV, gelir, kurumlar), SGK, şirket kuruluşu, ticaret hukuku, e-fatura, SGS sınavı
Ton: Güven veren, öğretici, net — abartısız ve samimi
CTA: "Detaylı bilgi ve danışmanlık için Adım Müşavir ile iletişime geçin → adimmusavir.com"
Dil: Türkçe, anlaşılır ve sade
"""


def generate_video_script(topic: str, duration_minutes: int = 5) -> dict:
    prompt = f"""{_BRAND_CTX}

"{topic}" konusunda {duration_minutes} dakikalık YouTube eğitim/konu anlatım videosu için script yaz.

Format: JSON
{{
    "title": "SEO uyumlu, merak uyandıran başlık (max 70 karakter)",
    "description": "YouTube video açıklaması (500 karakter, CTA + hashtag dahil)",
    "tags": ["muhasebe", "vergi", ...],
    "sections": [
        {{
            "title": "Bölüm başlığı (kısa, net)",
            "content": "Seslendirilecek metin — doğal konuşma dili, sade Türkçe"
        }}
    ]
}}

Kurallar:
- Toplam ~{duration_minutes * 130} kelime (dakikada 130 kelime)
- Her bölüm max 90 saniye
- Giriş: konunun önemi ve izleyiciye ne kazandıracağı
- Gelişme: adım adım açıklama, somut örnekler
- Sonuç: özet + güçlü CTA
- Teknik terimleri kısa açıkla
- Maddeler halinde listele, soru-cevap formatını kullan
"""

    r = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(r.choices[0].message.content)


def generate_shorts_script(topic: str) -> dict:
    prompt = f"""{_BRAND_CTX}

"{topic}" konusunda 45-60 saniyelik YouTube Shorts / Instagram Reels script yaz.

Başarılı format seçeneklerinden birini kullan:
A) "Bu hatayı yapıyorsanız dikkat!" — yanlış yapılan şeyi göster, doğrusunu ver
B) "X adımda Y nasıl yapılır?" — pratik, hızlı bilgi
C) "Bilmeden imzaladığınız sözleşmede bu var" — merak + güven
D) Soru çözümü özeti — bir kavramı 30 saniyede aç

JSON:
{{
    "title": "Kısa, merak uyandıran başlık (max 8 kelime)",
    "hook": "İlk 3 saniye — şok, merak veya aciliyetle başla (max 15 kelime)",
    "content": "Ana içerik (max 70 kelime, liste veya adım formatı, hızlı tempo)",
    "cta": "Güçlü çağrı (max 20 kelime) — adimmusavir.com veya takip et",
    "caption": "Instagram/YouTube caption (emoji, hashtag, max 220 karakter)",
    "tags": ["smmm", "muhasebe", "vergi", "sgs", ...]
}}
"""

    r = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(r.choices[0].message.content)


def generate_question_solution_script(topic: str, question_text: str = "") -> dict:
    q_hint = f"\nSoru: {question_text}" if question_text else ""

    prompt = f"""{_BRAND_CTX}

"{topic}" konusunda SMMM/YMM/SGS sınav sorusu çözüm videosu için script yaz.{q_hint}

Bu format kullanılacak:
1. Giriş — "Bugün hangi konuyu çözeceğiz?"
2. Soruyu ekranda göster + kısa konuyu aç (15 sn)
3. Kavramı kısaca anlat (30 sn)
4. Şıkları değerlendir — yanlışları neden yanlış (45 sn)
5. Doğru cevabı ver + açıkla (30 sn)
6. Sınavda dikkat edilecek püf nokta (15 sn)
7. CTA

JSON:
{{
    "title": "Başlık: '[Konu] Soru Çözümü | SMMM Sınavı'",
    "question_text": "Soru metni (varsa senin ürettiğin, yoksa boş bırak)",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_option": "A",
    "sections": [
        {{"title": "Bölüm adı", "content": "Seslendirilecek metin"}},
        ...
    ],
    "puf_nokta": "Sınavda dikkat: ...",
    "cta": "Daha fazla soru çözümü için Adım Müşavir'i takip edin → adimmusavir.com",
    "tags": ["smmm", "soru-çözüm", "muhasebe", ...],
    "description": "YouTube açıklaması"
}}
"""

    r = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(r.choices[0].message.content)


def generate_topic_explanation_script(topic: str) -> dict:
    prompt = f"""{_BRAND_CTX}

"{topic}" konusunda konu anlatım videosu için script yaz.

Format (sabit akış):
1. Konu başlığı + "Bu videodan sonra X'i anlayacaksınız"
2. Tanım — sade Türkçe
3. Temel kurallar (madde madde, en fazla 5)
4. Örnek senaryo (gerçek hayat)
5. Sınavda nasıl sorulur / pratikte ne işe yarar
6. Kısa özet tablosu
7. CTA

JSON:
{{
    "title": "Konu anlatım başlığı — YouTube SEO uyumlu",
    "sections": [
        {{"title": "Bölüm adı", "content": "Seslendirilecek metin — sade, öğretici"}},
        ...
    ],
    "summary_table": [
        {{"label": "Tanım", "value": "..."}},
        {{"label": "Kural", "value": "..."}},
        {{"label": "Sınav notu", "value": "..."}}
    ],
    "cta": "Daha fazlası için Adım Müşavir → adimmusavir.com",
    "tags": ["muhasebe", "vergi", "smmm", ...],
    "description": "YouTube açıklaması (500 karakter, hashtag dahil)"
}}
"""

    r = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(r.choices[0].message.content)


def generate_storyboard(topic: str, content_type: str = "video", category: str = "smmm") -> dict:
    """
    Sahne bazlı storyboard üretir.
    Her sahne: narration (TTS) + display_lines (ekran) AYRI.
    Yeni scene type'lar: definition, concept, comparison, example, hook, option_analysis
    content_type: video | short | question_solution | topic_explanation
    category: smmm | sgs | genel
    """
    cat_ctx = {
        "sgs":   "SGS hazırlık sınavı — iş mevzuatı, sağlık güvenliği, SGS prosedürleri, risk değerlendirme",
        "smmm":  "SMMM/YMM sınavı — muhasebe, vergi, KDV, gelir vergisi, SGK, ticaret hukuku",
        "genel": "Adım Müşavir genel içerik — muhasebe, vergi, girişimcilik, mali müşavirlik",
    }.get(category, "SMMM/YMM sınavı")

    # Scene type reference for GPT
    scene_types_ref = """
KULLANILABILIR SAHNE TİPLERİ:
• intro      — Başlık kartı, giriş (ekran: başlık + alt başlık)
• hook       — Dikkat çekici güçlü ifade, tam ekran büyük metin
• definition — Bir terimin tanımı (ekran: term + tanım maddeleri)
• concept    — Numara sıralı kavram açıklaması (ekran: numaralı liste)
• content    — Madde madde içerik (ekran: başlık + bullet listesi)
• comparison — İki kavramın karşılaştırması (ekran: sol/sağ split)
• example    — Gerçek hayat örneği (ekran: senaryo + detaylar)
• question   — Çoktan seçmeli soru (fields: question_text, options[])
• option_analysis — Şık analizi: hangisi neden yanlış (ekran: analiz)
• answer     — Doğru cevap + açıklama (fields: options[], correct_option, explanation)
• exam_tip   — Sınav püf noktası (field: tip)
• summary    — Özet tablo (field: rows[{label, value}])
• cta        — Son sahne, abone çağrısı
"""

    if content_type == "question_solution":
        scene_format = f"""{scene_types_ref}

Sahne AKIŞI (bu sırayla, tam 7 sahne):
1. intro   — "Bugün şu soruyu çözüyoruz: [konu]"
2. question — soruyu oku, şıkları göster (question_text + options zorunlu)
3. concept  — soruyu çözmek için gereken temel kavram (numara sıralı)
4. option_analysis — yanlış şıkları neden yanlış analiz et
5. answer   — doğru cevabı ver (options + correct_option + explanation zorunlu)
6. exam_tip — sınavda dikkat noktası (tip zorunlu)
7. cta      — abone ol çağrısı

JSON formatı:
{{
  "title": "Başlık (YouTube SEO, max 70 karakter)",
  "description": "YouTube açıklaması (500 karakter)",
  "tags": ["smmm", "soru-çözüm", ...],
  "scenes": [
    {{
      "type": "intro",
      "title": "Giriş",
      "narration": "Merhaba, bugün şu soruyu çözeceğiz: [konu]. 2-3 cümle.",
      "display_lines": ["Soru Çözümü", "[Konu Adı]"]
    }},
    {{
      "type": "question",
      "title": "Soru",
      "narration": "Sorumuzu okuyalım. [soruyu oku ve şıkları seslendir]",
      "display_lines": ["Soru"],
      "question_text": "Tam soru metni burada",
      "options": ["A) Birinci şık", "B) İkinci şık", "C) Üçüncü şık", "D) Dördüncü şık"]
    }},
    {{
      "type": "concept",
      "title": "Temel Kavram",
      "narration": "Bu soruyu çözmek için şu kavramı bilmemiz gerekiyor: [kavram açıkla]",
      "display_lines": ["Temel Kavram", "1. Birinci madde", "2. İkinci madde", "3. Üçüncü madde"]
    }},
    {{
      "type": "option_analysis",
      "title": "Şık Analizi",
      "narration": "Şıkları tek tek değerlendirelim. A şıkkı yanlış çünkü... [analiz et]",
      "display_lines": ["• A yanlış: kısa açıklama", "• B yanlış: kısa açıklama", "• C doğru: neden doğru"],
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_option": "C"
    }},
    {{
      "type": "answer",
      "title": "Doğru Cevap",
      "narration": "Doğru cevap C şıkkıdır. [detaylı açıkla]",
      "display_lines": [],
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_option": "C",
      "explanation": "Doğru cevabın açıklaması burada"
    }},
    {{
      "type": "exam_tip",
      "title": "Sınav Püf Noktası",
      "narration": "Sınavda bu konuyla ilgili dikkat etmeniz gereken nokta: [açıkla]",
      "tip": "Sınavda dikkat: kısa ve net püf nokta"
    }},
    {{
      "type": "cta",
      "title": "Son",
      "narration": "Videoyu beğendiyseniz abone olmayı unutmayın. Adım Müşavir ile sınava hazır olun.",
      "display_lines": []
    }}
  ]
}}"""

    elif content_type == "short":
        scene_format = f"""{scene_types_ref}

Sahne AKIŞI (Reels/Shorts — toplam 45-90 sn, TAM 3 sahne):
1. hook    — İlk 3-5 sn: çok güçlü tek cümle, merak veya şok
2. content — Ana içerik: 3-5 madde, hızlı tempo
3. cta     — 5 sn son

JSON formatı:
{{
  "title": "Başlık (max 8 kelime, merak uyandıran)",
  "description": "Caption (emoji + hashtag, max 220 karakter)",
  "tags": ["smmm", "muhasebe", ...],
  "scenes": [
    {{
      "type": "hook",
      "title": "Hook",
      "narration": "15-20 kelime max — şok veya soru ile başla",
      "display_lines": ["Tek güçlü cümle (max 50 karakter)"]
    }},
    {{
      "type": "content",
      "title": "Öğren",
      "narration": "40-60 kelime max — 3-4 madde",
      "display_lines": ["• Madde 1 (max 45 karakter)", "• Madde 2", "• Madde 3"]
    }},
    {{
      "type": "cta",
      "title": "CTA",
      "narration": "Beğen, takip et, adimmusavir.com",
      "display_lines": []
    }}
  ]
}}"""

    else:
        # video / topic_explanation — full educational video
        scene_format = f"""{scene_types_ref}

Sahne AKIŞI (Konu Anlatım — 7-10 sahne, içerik derinliğine göre):
1. intro       — Başlık kartı + "Bu videodan sonra X'i öğreneceksiniz"
2. hook        — "Bu konuyu neden bilmen şart?" — güçlü motivasyon
3. definition  — Temel terimin tanımı (varsa)
4. concept     — İlk kavram/kural/adım (numara sıralı)
5. comparison  — İki kavramı karşılaştır (varsa karıştırılan bir şey)
6. example     — Gerçek hayat veya sınav örneği
7. content × 1-3 — Kalan kurallar/maddeler
8. summary     — Özet tablo
9. cta         — Abone çağrısı

JSON formatı:
{{
  "title": "Başlık (YouTube SEO, max 70 karakter)",
  "description": "YouTube açıklaması (500 karakter, CTA + hashtag)",
  "tags": [...],
  "scenes": [
    {{
      "type": "intro",
      "title": "Başlık",
      "narration": "Merhaba! Bu videoda [konu] konusunu öğreneceğiz. [2-3 cümle]",
      "display_lines": ["Ana Başlık (max 45 karakter)", "Alt başlık veya hedef"]
    }},
    {{
      "type": "hook",
      "title": "Neden Önemli?",
      "narration": "Peki bu konuyu neden bilmen gerekiyor? [motivasyon, 2-3 cümle]",
      "display_lines": ["⚡ Dikkat!", "Bu konuyu bilmeden... kısa uyarı"]
    }},
    {{
      "type": "definition",
      "title": "[Terim Adı]",
      "narration": "[Terimi doğal dille açıkla, 2-3 cümle]",
      "display_lines": ["• Birinci tanım maddesi", "• İkinci madde", "• Üçüncü madde"]
    }},
    {{
      "type": "concept",
      "title": "Temel Kurallar",
      "narration": "[Kavramları sırala ve açıkla]",
      "display_lines": ["1. Birinci kural", "2. İkinci kural", "3. Üçüncü kural"]
    }},
    {{
      "type": "comparison",
      "title": "Karşılaştırma",
      "narration": "[İki kavramı karşılaştır]",
      "display_lines": ["Sol kavram maddesi 1", "Sol kavram maddesi 2", "Sağ kavram maddesi 1", "Sağ kavram maddesi 2"],
      "left_title": "Kavram A",
      "right_title": "Kavram B"
    }},
    {{
      "type": "example",
      "title": "Gerçek Örnek",
      "narration": "[Örneği anlat, hikaye gibi]",
      "scenario": "Örnek senaryo cümlesi (max 80 karakter)",
      "display_lines": ["• Detay 1", "• Detay 2", "• Sonuç"]
    }},
    {{
      "type": "summary",
      "title": "Özet",
      "narration": "Özetleyelim. [ana noktaları tekrar et]",
      "rows": [
        {{"label": "Tanım", "value": "Kısa açıklama"}},
        {{"label": "Kural", "value": "Kısa kural"}},
        {{"label": "Sınav notu", "value": "Dikkat noktası"}}
      ]
    }},
    {{
      "type": "cta",
      "title": "Son",
      "narration": "Videoyu beğendiyseniz abone olmayı unutmayın. Adım Müşavir ile fark yaratın.",
      "display_lines": []
    }}
  ]
}}"""

    prompt = f"""{_BRAND_CTX}

Hedef kategori: {cat_ctx}
Konu: "{topic}"
Video tipi: {content_type}

{scene_format}

KRİTİK KURALLAR:
- narration: TTS'e gider — doğal konuşma Türkçesi, kısa cümleler, teknik ama anlaşılır
- display_lines: EKRANDA görünür — max 5 satır, HER SATIR max 50 karakter
- Comparison sahnesinde left_title ve right_title ZORUNLU
- Example sahnesinde scenario alanı ZORUNLU (max 80 karakter)
- Question ve Answer sahnelerinde options[] ve correct_option ZORUNLU
- Exam_tip sahnesinde tip alanı ZORUNLU
- Summary sahnesinde rows[] ZORUNLU
- Her sahne için narration MUTLAKA doldurulsun — boş bırakma
- Sadece JSON döndür, başka açıklama ekleme
"""
    r = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.35,
    )
    return json.loads(r.choices[0].message.content)


def generate_post_content(topic: str) -> dict:
    prompt = f"""{_BRAND_CTX}

"{topic}" konusunda Instagram bilgilendirici post içeriği yaz.

JSON:
{{
    "title": "Post başlığı",
    "question": "Takipçiyi düşündürecek soru (başlık olarak kullanılacak)",
    "answer_points": ["Madde 1", "Madde 2", "Madde 3", "Madde 4", "Madde 5"],
    "caption": "Instagram caption (emoji + hashtag, max 300 karakter, CTA dahil)",
    "image_text": "Görselde çok kısa özetle ne anlatılıyor (max 12 kelime)"
}}
"""

    r = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(r.choices[0].message.content)
