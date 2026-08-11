"""
SGS motivasyon içerik bankası — B.2/B.3 (konu ve kapanış bankası).

NEDEN VAR: B.0 sorunu — jenerik motivasyon metinleri ("Yalnız değilsin",
"Birçok öğrenci benzer sıkıntılar yaşıyor") herhangi bir sınav videosu olabilir,
SGS'ye özgü hiçbir şey yok. Bu modül LLM'e somut, SGS'ye özgü ham malzeme
(konu + duygu + somut adım + SGS gerçeği) verir; kapanış cümlesi ise LLM'in
UYDURMASINA izin verilmez, sabit onaylı bankadan seçilir (pazarlama uyumu —
check_marketing_compliance ile aynı disiplin).

content_history tablosu (content_dedup.py) zaten her motivasyon job'unun
topic'ini kaydediyor — "son 60 günde kullanılmayan" seçimi bunu sorgular,
ayrı bir kullanım-takip tablosu gerekmiyor.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

# ── B.2 — Konu bankası (18 konu, 4 kategori) ──────────────────────
TOPIC_BANK: list[dict] = [
    # DERS BAZLI
    {"id": 1, "category": "ders_bazli", "title": "Finansal muhasebe netlerin düşük",
     "feeling": "yetersizlik", "action": "yevmiye kaydı mantığını tekrar et, borç-alacak dengesinden başla",
     "sgs_fact": "FM en çok soru gelen ders, 3 net sıralamayı değiştirir"},
    {"id": 2, "category": "ders_bazli", "title": "Ticaret hukuku ezber gibi geliyor",
     "feeling": "sıkılma", "action": "madde ezberleme, kavram haritası çıkar: tacir, işletme, şirket",
     "sgs_fact": "TTK mantık dersi, ezber değil sistem"},
    {"id": 3, "category": "ders_bazli", "title": "Maliyet muhasebesi formülleri karışıyor",
     "feeling": "kafa karışıklığı", "action": "formül listesi değil akış şeması yap",
     "sgs_fact": "maliyet soruları hep aynı 5 kalıptan çıkıyor"},
    {"id": 4, "category": "ders_bazli", "title": "Denetim soyut geliyor",
     "feeling": "uzaklık", "action": "her kavramı gerçek bir olayla eşleştir",
     "sgs_fact": "denetim netleri en hızlı yükselen alan"},
    {"id": 5, "category": "ders_bazli", "title": "Vergi hukuku çok geniş",
     "feeling": "ezilme", "action": "tüm kanunu değil, çıkmış sorulardaki konuları önceliklendir",
     "sgs_fact": "son 5 yılda soruların çoğu aynı konulardan"},
    {"id": 6, "category": "ders_bazli", "title": "Hukuk dersleri birbirine karışıyor",
     "feeling": "bulanıklık", "action": "her hukuk dersine ayrı gün ayır",
     "sgs_fact": "borçlar-ticaret-meslek hukuku ayrı mantıklar"},
    # DENEME VE ÖLÇME
    {"id": 7, "category": "deneme_olcme", "title": "Deneme netin düştü",
     "feeling": "umutsuzluk", "action": "yanlış analizi yap, konu bazında 3 madde çıkar",
     "sgs_fact": "deneme netleri dalgalanır, trend önemli"},
    {"id": 8, "category": "deneme_olcme", "title": "Deneme sonuçların dalgalı",
     "feeling": "belirsizlik", "action": "son 5 denemenin ortalamasını al",
     "sgs_fact": "SGS'de istikrar sıralamadan önemli"},
    {"id": 9, "category": "deneme_olcme", "title": "Çıkmış soruları çözmeye korkuyorsun",
     "feeling": "erteleme", "action": "bugün tek yıl çöz, puanına bakma, formatı gör",
     "sgs_fact": "SGS soru kalıpları yıllar içinde çok değişmiyor"},
    {"id": 10, "category": "deneme_olcme", "title": "Süre yetmiyor, soruları bitiremiyorsun",
     "feeling": "panik", "action": "soru başına 1 dakika, takılırsan geç",
     "sgs_fact": "100 soru, netini süre yönetimi belirliyor"},
    # PLANLAMA VE SÜREKLİLİK
    {"id": 11, "category": "planlama_sureklilik", "title": "Çalışma programın bozuldu",
     "feeling": "suçluluk", "action": "kaçırdığın günleri telafi etme, bugünden devam et",
     "sgs_fact": "SGS'yi kazananların çoğu da en az bir kez bıraktı"},
    {"id": 12, "category": "planlama_sureklilik", "title": "Konu listesi bitmiyor gibi",
     "feeling": "ezilme", "action": "listeyi haftalara böl, sadece bu haftayı yaz",
     "sgs_fact": "SGS müfredatı sonlu, 8 ders"},
    {"id": 13, "category": "planlama_sureklilik", "title": "Sınava 30 gün kaldı, neye odaklanmalı",
     "feeling": "acele", "action": "yeni konu yok, sadece tekrar ve deneme",
     "sgs_fact": "son ay öğrenme değil pekiştirme ayı"},
    {"id": 14, "category": "planlama_sureklilik", "title": "Her gün soru çözme alışkanlığı kuramıyorsun",
     "feeling": "isteksizlik", "action": "günde 10 soru, sabit saat",
     "sgs_fact": "günde 10 soru, ayda 300 soru demek"},
    {"id": 15, "category": "planlama_sureklilik", "title": "Telefon dikkatini dağıtıyor",
     "feeling": "öz-eleştiri", "action": "25 dakika uçak modu, sonra 5 dakika serbest",
     "sgs_fact": "bir SGS sorusu ortalama 1 dakika"},
    # KAYGI VE SÜREÇ
    {"id": 16, "category": "kaygi_surec", "title": "İlk kez giriyorsun, formatı bilmiyorsun",
     "feeling": "kaygı", "action": "bir deneme çöz, puanına bakma, yapıyı tanı",
     "sgs_fact": "SGS 100 soru, 8 ders"},
    {"id": 17, "category": "kaygi_surec", "title": "Herkes senden ilerideymiş gibi",
     "feeling": "kıyas", "action": "kendi ilerleme çizelgeni tut",
     "sgs_fact": "SGS bireysel bir sınav"},
    {"id": 18, "category": "kaygi_surec", "title": "Staja giriş sonrası ne olacak kaygısı",
     "feeling": "belirsizlik", "action": "önce sınav, staj planı sonra",
     "sgs_fact": "staja giriş bir kapı, açılınca yol netleşir"},
]

# ── B.3 — Kapanış bankası (cta_text) — LLM UYDURMAZ, buradan seçer ──
CLOSING_BANK: list[str] = [
    "SGS yolculuğunda birlikte ilerleyelim. Takipte kal.",
    "Planlamayı birlikte yapalım. Her hafta bir konu.",
    "Bu konuyu birlikte bitirelim. Takip et, kaçırma.",
    "SGS'ye hazırlanırken yalnız değilsin. Buradayız.",
    "Hangi ders zorluyorsa yoruma yaz, birlikte çalışalım.",
    "Sıradaki konu için takipte kal. Adım adım gidiyoruz.",
    "Bugün bir adım. Yarın devamı. SGS'de görüşürüz.",
    "Programını birlikte kuralım. Takip et, başlayalım.",
]

# ── B.4 — Hook formülleri (SGS bağlamıyla) ─────────────────────────
HOOK_FORMULAS: list[dict] = [
    {"type": "durum_tespiti", "example": "Finansal muhasebe netin üç denemedir aynı yerde."},
    {"type": "sayi_ile", "example": "SGS'de en çok kaybedilen 8 net, hep aynı iki dersten."},
    {"type": "inanc_kirma", "example": "Ticaret hukuku ezber değil. Yanlış çalışıyorsun."},
    {"type": "soru", "example": "Deneme netin neden yükselmiyor, biliyor musun?"},
    {"type": "zaman_baskisi", "example": "SGS'ye 30 gün kaldı. Yeni konuya başlama."},
    {"type": "karsitlik", "example": "Konuyu biliyorsun. Soruyu bilmiyorsun. Fark bu."},
]

# ── B.1 — SGS unsuru tespiti (>= 2 farklı unsur zorunlu) ───────────
SGS_COURSE_NAMES: list[str] = [
    "finansal muhasebe", "ticaret hukuku", "maliyet muhasebesi", "denetim",
    "vergi hukuku", "borçlar hukuku", "meslek hukuku",
    "iş ve sosyal güvenlik hukuku", "mali tablolar analizi", "muhasebe standartları",
]
SGS_EXAM_FACTS: list[str] = [
    "deneme neti", "konu listesi", "çıkmış soru", "sınav formatı",
    "100 soru", "baraj", "staja giriş", "smmm stajı",
]
SGS_TIME_PHRASES: list[str] = [
    "son ay", "son hafta", "tekrar dönemi",
    # "sınava X gün kala" — ayrı regex ile yakalanır (motivation_generator.py)
]

# ── B.1 — Yasak jenerik ifadeler → somut karşılık ─────────────────
GENERIC_BANNED_PHRASES: dict[str, str] = {
    "birçok öğrenci": "birçok SGS adayı",
    "bu sınav": "SGS / staja giriş sınavı",
    "hedefine ulaş": "somut hedef: SGS'yi geç, stajına başla",
    "başarabilirsin": "tek başına yetmez — somut bir adımla birlikte kullan",
}


def select_topic(exclude_recent_days: int = 60) -> dict:
    """
    B.6.3: kullanıcı konu girmezse bankadan, son N günde KULLANILMAYAN
    konulardan seçilir. content_history.topic ile bankanın title'ı eşleştirilir
    (save_content_fingerprint zaten her motivasyon job'unda topic kaydediyor —
    ayrı bir "kullanım günlüğü" tablosu gerekmiyor).
    """
    used_titles: set[str] = set()
    try:
        from app.db.supabase import get_supabase_client
        sb = get_supabase_client()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=exclude_recent_days)).isoformat()
        rows = (
            sb.table("content_history")
            .select("topic")
            .gte("created_at", cutoff)
            .execute().data or []
        )
        used_titles = {r["topic"] for r in rows if r.get("topic")}
    except Exception:
        pass  # sorgu başarısızsa tüm banka havuzda kalır (tekrar riski, durma riskinden iyi)

    eligible = [t for t in TOPIC_BANK if t["title"] not in used_titles]
    if not eligible:
        eligible = TOPIC_BANK  # tüm banka son N günde kullanıldı — döngü baştan başlar
    return random.choice(eligible)


def format_topic_for_prompt(topic_entry: dict) -> str:
    """Banka girdisini LLM prompt'una geçecek tek bir 'topic' string'ine çevirir."""
    return (
        f"{topic_entry['title']} (duygu: {topic_entry['feeling']}; "
        f"somut adım: {topic_entry['action']}; "
        f"SGS gerçeği: {topic_entry['sgs_fact']})"
    )
