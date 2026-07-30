"""
İçerik bankası — ADIM 6 + ADIM 7 (ÖNCELİK HATTI v3 §7, §8).

Motivasyon konu bankası (HAT A: öğrenci), danışan konu bankası (HAT B),
hook formülleri ve CTA bankası.

Storyboard generator'lar bu bankadan seçim yaparak LLM'e konu+ton+CTA iletir.
Bankadan seçim deterministik (job_id hash) veya sırayla (round-robin) yapılır.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# VERİ YAPILARI
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ContentTopic:
    id: str
    topic: str
    emotion: str           # hedef duygu durumu
    concrete_action: str   # videonun önerdiği somut aksiyon
    content_track: str     # 'ogrenci' | 'danisan'
    series: Optional[str] = None   # içerik serisi etiketi


@dataclass
class HookFormula:
    id: str
    template: str
    formula_type: str   # durum_tespiti | sayi | yanlis_inanc | soru | zaman_baskisi | karsilastirma
    example: str
    content_track: str  # 'ogrenci' | 'danisan' | 'her_ikisi'


@dataclass
class CtaEntry:
    id: str
    primary: str          # 8-10 sn'lik son sahneye konulan tek eylem
    pinned_comment: str   # video altına sabitlenecek yorum
    content_track: str    # 'ogrenci' | 'danisan'


# ─────────────────────────────────────────────────────────────────────────────
# MOTİVASYON KONU BANKASI — HAT A (öğrenci)  §7.1
# ─────────────────────────────────────────────────────────────────────────────

MOTIVATION_TOPICS_OGRENCI: list[ContentTopic] = [
    ContentTopic(
        id="mot_ogr_01",
        topic="Programın bozuldu, üç gündür açmadın",
        emotion="suçluluk",
        concrete_action="Bugün sadece 1 konu tekrarı — yarım saatten fazla gerekmez.",
        content_track="ogrenci",
    ),
    ContentTopic(
        id="mot_ogr_02",
        topic="Denemede net düştü",
        emotion="umutsuzluk",
        concrete_action="Yanlış analizini yap; konu bazlı en zayıf 3 maddeyi yaz.",
        content_track="ogrenci",
    ),
    ContentTopic(
        id="mot_ogr_03",
        topic="Konu listesi bitmiyor gibi",
        emotion="ezilme",
        concrete_action="Listeyi haftalara böl, sadece ilk haftanın başlıklarını yaz.",
        content_track="ogrenci",
    ),
    ContentTopic(
        id="mot_ogr_04",
        topic="Son ay, neye odaklanmalı",
        emotion="panik",
        concrete_action="Yeni konu yok — sadece tekrar ve deneme. Bugün 1 deneme çöz.",
        content_track="ogrenci",
    ),
    ContentTopic(
        id="mot_ogr_05",
        topic="Her gün soru çözme alışkanlığı",
        emotion="isteksizlik",
        concrete_action="Günde 10 soru, sabit saat. Yarın da aynı saatte.",
        content_track="ogrenci",
    ),
    ContentTopic(
        id="mot_ogr_06",
        topic="Telefon dikkatini dağıtıyor",
        emotion="öz-eleştiri",
        concrete_action="25 dakika uçak modu. Sadece bugün dene.",
        content_track="ogrenci",
    ),
    ContentTopic(
        id="mot_ogr_07",
        topic="İlk kez sınava giriyorum, korkuyorum",
        emotion="kaygı",
        concrete_action="Sınav formatını tanı: 1 deneme çöz, sadece formatı gör.",
        content_track="ogrenci",
    ),
    ContentTopic(
        id="mot_ogr_08",
        topic="Çalışıyorum ama akılda kalmıyor",
        emotion="yılgınlık",
        concrete_action="Aktif tekrar: kitabı kapat, anlat, kontrol et.",
        content_track="ogrenci",
    ),
    ContentTopic(
        id="mot_ogr_09",
        topic="Herkes benden ilerideymiş gibi",
        emotion="kıyas",
        concrete_action="Kendi ilerleme çizelgeni tut — bugünden geçen haftana bak.",
        content_track="ogrenci",
    ),
    ContentTopic(
        id="mot_ogr_10",
        topic="Bugün hiç çalışamadım",
        emotion="pes etme",
        concrete_action="Yarını kurtaran 20 dakika: şu an başla, 20 dakika sonra bitir.",
        content_track="ogrenci",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# DANIŞAN KONU BANKASI — HAT B  §7.3
# ─────────────────────────────────────────────────────────────────────────────

DANISAN_TOPICS: list[ContentTopic] = [
    ContentTopic(
        id="dan_01",
        topic="Şahıs şirketi mi, limited şirket mi",
        emotion="kararsızlık",
        concrete_action="İkisinin vergi ve sorumluluk farkını öğren; kararını danışarak ver.",
        content_track="danisan",
    ),
    ContentTopic(
        id="dan_02",
        topic="e-Fatura zorunluluğu kimleri kapsıyor",
        emotion="belirsizlik",
        concrete_action="Ciro sınırını kontrol et; e-Fatura kapsamındaysan geçiş takvimini öğren.",
        content_track="danisan",
    ),
    ContentTopic(
        id="dan_03",
        topic="e-ticarette kazanç beyanı",
        emotion="risk farkındalığı",
        concrete_action="Platform gelirlerini nasıl beyan edeceğini öğren; gecikme ceza getirir.",
        content_track="danisan",
    ),
    ContentTopic(
        id="dan_04",
        topic="Defter tutma sınırları ve sınıf değişikliği",
        emotion="bilgi eksikliği",
        concrete_action="Ciro sınırını yılda bir kontrol et; sınıf değişirse yükümlülüklerin değişir.",
        content_track="danisan",
    ),
    ContentTopic(
        id="dan_05",
        topic="Genç girişimci vergi istisnası",
        emotion="fırsat",
        concrete_action="29 yaş altındaysanız şartları öğrenin; beyan etmeyi unutmayın.",
        content_track="danisan",
    ),
    ContentTopic(
        id="dan_06",
        topic="KDV iadesinde en çok yapılan hata",
        emotion="nakit akışı kaygısı",
        concrete_action="İade belgelerini eksiksiz tut; eksik belge iade süresini uzatır.",
        content_track="danisan",
    ),
    ContentTopic(
        id="dan_07",
        topic="Serbest meslek makbuzu ne zaman kesilir",
        emotion="uyum kaygısı",
        concrete_action="Hizmet tesliminde veya ödemede — hangisi önce gerçekleşiyorsa.",
        content_track="danisan",
    ),
    ContentTopic(
        id="dan_08",
        topic="Yıl sonu kapanışında unutulanlar",
        emotion="önlem alma",
        concrete_action="Amortisman, karşılık ve envanter sayımını Aralık'ta kontrol et.",
        content_track="danisan",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# HOOK FORMÜLLERI  §7.2
# ─────────────────────────────────────────────────────────────────────────────

HOOK_FORMULAS: list[HookFormula] = [
    HookFormula(
        id="hook_01",
        template="[Durum tespiti] — kullanıcının tam bugünkü halini adres.",
        formula_type="durum_tespiti",
        example="Üç gündür kitabı açmadın, biliyorum.",
        content_track="ogrenci",
    ),
    HookFormula(
        id="hook_02",
        template="[Sayı + kayıp] — somut rakam, nerede kaybedildiğini göster.",
        formula_type="sayi",
        example="SGS'de en çok kaybedilen 8 net, hep aynı yerden gider.",
        content_track="ogrenci",
    ),
    HookFormula(
        id="hook_03",
        template="[Yanlış inanç kırma] — yaygın kabul görülen ama yanlış olan şey.",
        formula_type="yanlis_inanc",
        example="Çok çalışmak yetmiyor. Yanlış çalışıyorsun.",
        content_track="her_ikisi",
    ),
    HookFormula(
        id="hook_04",
        template="[Soru] — izleyicinin kafasındaki soruyu sen sor.",
        formula_type="soru",
        example="Deneme netin neden yükselmiyor?",
        content_track="ogrenci",
    ),
    HookFormula(
        id="hook_05",
        template="[Zaman baskısı] — takvim + sınırlı aksiyon listesi.",
        formula_type="zaman_baskisi",
        example="Sınava 30 gün kaldı. Şu üç şeyi bırak.",
        content_track="ogrenci",
    ),
    HookFormula(
        id="hook_06",
        template="[Karşıtlık] — iki şeyi bilmek vs. yapabilmek arasındaki uçurum.",
        formula_type="karsilastirma",
        example="Konuyu biliyorsun. Soruyu bilmiyorsun. Fark bu.",
        content_track="her_ikisi",
    ),
    HookFormula(
        id="hook_07",
        template="[Risk + rakam] — iş dünyasında kaçırılan şey veya ceza riski.",
        formula_type="sayi",
        example="e-Fatura'ya geçmeyen işletmelere 2024'te bu ceza kesildi.",
        content_track="danisan",
    ),
    HookFormula(
        id="hook_08",
        template="[Yanlış inanç — iş] — yaygın ama hatalı iş kararı.",
        formula_type="yanlis_inanc",
        example="'Muhasebeci halleder' derken sen ceza yiyorsun.",
        content_track="danisan",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# CTA BANKASI  §8.1
# ─────────────────────────────────────────────────────────────────────────────

CTA_BANK: list[CtaEntry] = [
    CtaEntry(
        id="cta_ogr_01",
        primary="Kaydet, çalışırken lazım olacak.",
        pinned_comment="Hangi konuyu anlatalım? Yoruma yaz. 👇",
        content_track="ogrenci",
    ),
    CtaEntry(
        id="cta_ogr_02",
        primary="Kaydet ve tekrar et — sınav yaklaşıyor.",
        pinned_comment="SGS sınavına ne zaman giriyorsun? Yoruma yaz, planlayalım.",
        content_track="ogrenci",
    ),
    CtaEntry(
        id="cta_ogr_03",
        primary="Takip et, her gün yeni konu geliyor.",
        pinned_comment="Bu konuda başka sorun varsa yoruma yaz, açıklayalım.",
        content_track="ogrenci",
    ),
    CtaEntry(
        id="cta_dan_01",
        primary="Sorunuz varsa yoruma yazın.",
        pinned_comment="Detaylı bilgi almak için profildeki bağlantıyı kullanabilirsiniz.",
        content_track="danisan",
    ),
    CtaEntry(
        id="cta_dan_02",
        primary="Bu durum işinizi etkiliyor mu? Yoruma yazın.",
        pinned_comment="Benzer konular için takip edin — her hafta yeni içerik.",
        content_track="danisan",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# YASAKLI HOOK AÇILIŞLARI (§7.2 — hook kalite kapısı)
# ─────────────────────────────────────────────────────────────────────────────

FORBIDDEN_HOOK_OPENS: list[str] = [
    "merhaba arkadaşlar",
    "merhaba arkadaslar",
    "herkese merhaba",
    "iyi günler arkadaşlar",
    "iyi günler",
    "selam arkadaşlar",
    "bugün sizlere",
    "bu videoda",
    "izlediğiniz için",
    "beğenmeyi unutmayın",
]


def _tr_lower(text: str) -> str:
    """Türkçe büyük harf duyarlı küçük harf dönüşümü (İ→i, I→ı)."""
    return (
        text
        .replace('İ', 'i').replace('I', 'ı')
        .replace('Ö', 'ö').replace('Ü', 'ü')
        .replace('Ğ', 'ğ').replace('Ş', 'ş').replace('Ç', 'ç')
        .lower()
    )


def check_hook_compliance(hook_text: str) -> list[str]:
    """
    Hook metnini spec'e göre doğrular.
    Returns: ihlal mesajları listesi (boş → OK)
    """
    violations: list[str] = []
    low = _tr_lower(hook_text.strip())

    for forbidden in FORBIDDEN_HOOK_OPENS:
        if low.startswith(forbidden):
            violations.append(
                f"Hook yasak açılışla başlıyor: '{forbidden}' — "
                "ilk 2 sn'de konu net olmalı, selamlama yasak."
            )

    word_count = len(hook_text.split())
    if word_count > 14:
        violations.append(
            f"Hook çok uzun: {word_count} kelime (maks. 14) — "
            "hook kısa ve çarpıcı olmalı."
        )

    return violations


# ─────────────────────────────────────────────────────────────────────────────
# SEÇİM FONKSİYONLARI
# ─────────────────────────────────────────────────────────────────────────────

def _hash_pick(items: list, job_id: str, salt: str = "") -> object:
    """Deterministik seçim — job_id + salt hash'i kullanır."""
    if not items:
        return None
    raw = f"{job_id}|{salt}"
    h = int(hashlib.sha256(raw.encode()).hexdigest(), 16)
    return items[h % len(items)]


def pick_motivation_topic(
    job_id: str,
    content_track: str = "ogrenci",
    exclude_ids: Optional[list[str]] = None,
) -> Optional[ContentTopic]:
    """
    İçerik bankasından motivasyon konusu seçer.
    Son 60 günde kullanılan konular `exclude_ids` ile dışlanır (§8.3 dedup).
    """
    exclude_ids = exclude_ids or []

    if content_track == "danisan":
        pool = [t for t in DANISAN_TOPICS if t.id not in exclude_ids]
    else:
        pool = [t for t in MOTIVATION_TOPICS_OGRENCI if t.id not in exclude_ids]

    if not pool:
        # Tüm konular kullanılmışsa kısıtı kaldır
        pool = DANISAN_TOPICS if content_track == "danisan" else MOTIVATION_TOPICS_OGRENCI

    return _hash_pick(pool, job_id, salt="topic")


def pick_hook_formula(
    job_id: str,
    content_track: str = "ogrenci",
) -> Optional[HookFormula]:
    """Uygun hook formülü seçer."""
    pool = [
        h for h in HOOK_FORMULAS
        if h.content_track in (content_track, "her_ikisi")
    ]
    return _hash_pick(pool, job_id, salt="hook")


def pick_cta(
    job_id: str,
    content_track: str = "ogrenci",
) -> Optional[CtaEntry]:
    """CTA bankasından seçer."""
    pool = [c for c in CTA_BANK if c.content_track == content_track]
    if not pool:
        pool = CTA_BANK
    return _hash_pick(pool, job_id, salt="cta")


def get_bank_summary() -> dict:
    """İçerik bankasının doluluk özetini döner (yönetim paneli için)."""
    return {
        "motivation_ogrenci": len(MOTIVATION_TOPICS_OGRENCI),
        "danisan_topics": len(DANISAN_TOPICS),
        "hook_formulas": len(HOOK_FORMULAS),
        "cta_entries": len(CTA_BANK),
        "forbidden_hook_opens": len(FORBIDDEN_HOOK_OPENS),
    }
