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
    Her sahne: narration (TTS'e gider) + display_lines (ekranda görünür) AYRI.
    content_type: video | short | question_solution | topic_explanation
    category: smmm | sgs | genel
    """
    cat_ctx = {
        "sgs":   "SGS hazırlık sınavı — SGS mevzuatı, iş hukuku, SGS prosedürleri",
        "smmm":  "SMMM/YMM sınavı — muhasebe, vergi, KDV, gelir vergisi, SGK, ticaret hukuku",
        "genel": "Adım Müşavir genel içerik — muhasebe, vergi, girişimcilik",
    }.get(category, "SMMM/YMM sınavı")

    if content_type == "question_solution":
        scene_format = """Sahneler ŞÖYLE OLMALI (tam bu sırayla):
1. intro — "Bugün X sorusunu çözüyoruz" (kısa giriş)
2. question — soruyu yüksek sesle oku, şıkları tanıt
3. concept — soru için gerekli temel kavramı anlat
4. option_analysis — yanlış şıkları neden yanlış oldukları ile ele al
5. answer — doğru cevabı ver ve açıkla
6. exam_tip — sınavda dikkat noktası
7. cta — abone ol, beğen, takip et

JSON:
{
  "title": "Başlık (YouTube SEO)",
  "description": "YouTube açıklaması",
  "tags": [...],
  "scenes": [
    {
      "type": "intro",
      "title": "Giriş",
      "narration": "TTS metni — doğal konuşma dili, 2-3 cümle",
      "display_lines": ["Başlık satırı", "Alt başlık"]
    },
    {
      "type": "question",
      "title": "Soru",
      "narration": "Soruyu okuyalım...",
      "display_lines": ["Soru başlığı"],
      "question_text": "Tam soru metni",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."]
    },
    {
      "type": "concept",
      "title": "Kavram Analizi",
      "narration": "Bu soruyu çözmek için bilmemiz gereken kavram...",
      "display_lines": ["Kavram:", "• madde", "• madde"]
    },
    {
      "type": "option_analysis",
      "title": "Şık Analizi",
      "narration": "Şıklara bakalım. A şıkkı yanlış çünkü...",
      "display_lines": ["Şık Analizi", "• A yanlış: ...", "• B yanlış: ...", "• C doğru: ..."]
    },
    {
      "type": "answer",
      "title": "Doğru Cevap",
      "narration": "Doğru cevap X'dir. Çünkü...",
      "display_lines": [],
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_option": "A",
      "explanation": "Açıklama metni"
    },
    {
      "type": "exam_tip",
      "title": "Sınav Püf Noktası",
      "narration": "Sınavda dikkat...",
      "tip": "Kısa ve net püf nokta metni"
    },
    {
      "type": "cta",
      "title": "Son",
      "narration": "Videoyu beğendiyseniz abone olmayı unutmayın. Adım Müşavir ile sınava hazırlanın.",
      "display_lines": []
    }
  ]
}"""
    elif content_type == "short":
        scene_format = """Sahneler (Reels/Shorts format — toplam 45-90 sn):
1. hook — dikkat çekici ilk 3-5 saniye, tek güçlü cümle
2. content — 3-5 madde, hızlı tempo
3. cta — kısa çağrı

JSON:
{
  "title": "Başlık (max 8 kelime)",
  "description": "Caption",
  "tags": [...],
  "scenes": [
    {"type": "hook", "title": "Hook", "narration": "15-20 kelime max", "display_lines": ["Tek güçlü cümle"]},
    {"type": "content", "title": "İçerik", "narration": "40-60 kelime max", "display_lines": ["• madde", "• madde", "• madde"]},
    {"type": "cta", "title": "CTA", "narration": "Takip et, beğen, adimmusavir.com", "display_lines": []}
  ]
}"""
    else:
        # video veya topic_explanation
        scene_format = f"""Sahneler ŞÖYLE OLMALI (tam bu sırayla):
1. intro — başlık + "Bu videodan sonra X'i anlayacaksınız"
2. hook — "Bu konuyu neden bilmen gerekiyor?" (dikkat çek)
3. content × 3-5 — her bölüm bir kavram/kural/örnek, her biri BAĞIMSIZ sahne
4. summary — özet tablo (3-5 satır)
5. cta — abone ol, beğen, adimmusavir.com

JSON:
{{
  "title": "Başlık (YouTube SEO, max 70 karakter)",
  "description": "YouTube açıklaması (500 karakter)",
  "tags": [...],
  "scenes": [
    {{
      "type": "intro",
      "title": "Giriş başlığı",
      "narration": "TTS — 2-3 cümle, doğal konuşma",
      "display_lines": ["Video başlığı", "Alt başlık"]
    }},
    {{
      "type": "hook",
      "title": "Neden Önemli?",
      "narration": "2-3 cümle merak uyandır",
      "display_lines": ["⚡ Dikkat!", "Önemli not satırı"]
    }},
    {{
      "type": "content",
      "title": "Bölüm Başlığı",
      "narration": "3-5 cümle, öğretici anlatım — bu sahnenin içeriğini seslendirmek için yeterli",
      "display_lines": ["Ana başlık", "• Madde 1", "• Madde 2", "• Madde 3"]
    }},
    {{
      "type": "summary",
      "title": "Özet",
      "narration": "Özetleyelim...",
      "rows": [{{"label": "Kavram", "value": "Açıklama"}}, ...]
    }},
    {{
      "type": "cta",
      "title": "Son",
      "narration": "Videoyu beğendiyseniz abone olmayı unutmayın.",
      "display_lines": []
    }}
  ]
}}"""

    prompt = f"""{_BRAND_CTX}

Hedef kategori: {cat_ctx}
Konu: "{topic}"
Video tipi: {content_type}

{scene_format}

KURALLAR:
- narration: TTS'e gider — doğal konuşma dili, kısa ve net cümleler
- display_lines: EKRANDA görünür — max 5 satır, her satır max 50 karakter
- Her sahne için narration MUTLAKA yazılsın (boş bırakma)
- Intro + CTA dahil toplam 5-8 sahne olsun
- Sadece JSON döndür, başka açıklama ekleme
"""
    r = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.4,
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
