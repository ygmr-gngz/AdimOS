"""
EducationalReel120 Storyboard Üretici — GPT-4o ile ~120 saniyelik SGS eğitim Reels.

Spec Section 9 akışı:
  0-5s    hook    — güçlü kanca, sürpriz istatistik
  5-20s   context — konunun önemi, sınav bağlantısı
  20-45s  content — 1. bilgi / çözüm adımı (bullet_points)
  45-70s  content — 2. bilgi / örnek / detay
  70-95s  mistake — sık yapılan hata (common_mistake)
  95-110s tip     — sınav ipucu (exam_tip)
  110-120s outro  — özet + CTA + kanal yönlendirmesi

Her sahne EducationalReelScene component'ine yüklenecek.
İçerik serisi (content_series) başlık şablonunu belirler.
"""
import json
import logging
import re
import unicodedata
from openai import OpenAI
from app.core.config import settings
from app.core.content_constants import TR_SPS, CHARS_PER_SYLLABLE, budget_params, scene_count_for_budget

logger = logging.getLogger(__name__)
_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _parse_turkish_amount(raw: str) -> float | None:
    """'10.000' -> 10000.0, '10.000,50' -> 10000.5. Placeholder (XXX/YYY, rakamsız) -> None."""
    if not raw or not re.search(r"\d", raw):
        return None
    s = raw.strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _check_journal_balance(scenes: list[dict]) -> list[str]:
    """
    AccountCardScene/JournalEntryScene sahnelerinde borç toplamı = alacak
    toplamı mı? A.3 — borç≠alacak olan bir kayıt öğrenciye yanlış muhasebe
    öğretir; sessizce geçilmez, HARD kapı (math_validation_failed).
    Döner: sorun varsa açıklama metinleri, yoksa boş liste.
    """
    problems: list[str] = []
    for s in scenes:
        entries = s.get("journalEntry")
        if not entries:
            continue
        debit_total = 0.0
        credit_total = 0.0
        has_placeholder = False
        for line in entries:
            amt = _parse_turkish_amount(str(line.get("amount", "")))
            if amt is None:
                has_placeholder = True
                continue
            if line.get("side") == "debit":
                debit_total += amt
            elif line.get("side") == "credit":
                credit_total += amt
        if has_placeholder:
            problems.append(
                f"sahne {s.get('id', '?')}: journalEntry tutarları placeholder "
                f"(XXX/YYY) içeriyor, gerçek rakam olmalı"
            )
        elif abs(debit_total - credit_total) > 0.01:
            problems.append(
                f"sahne {s.get('id', '?')}: borç toplamı ({debit_total:.0f}) != "
                f"alacak toplamı ({credit_total:.0f})"
            )
    return problems

# İçerik serisi başlık şablonları (Section 11)
SERIES_TITLE_TEMPLATES: dict[str, str] = {
    "cikmis_soru":      "{topic} — Çıkmış Soru Çözümü",
    "iki_dakikada_sgs": "2 Dakikada SGS: {topic}",
    "sik_hata":         "SGS'de {topic} Hakkında Sık Yapılan Hatalar",
    "bir_soruda_ogren": "Bir Soruda Öğren: {topic}",
    "konu_anlatimi":    "{topic} Konu Anlatımı — SGS",
    "motivasyon":       "{topic} | Adım Müşavir Motivasyon",
}

# TR_SPS (hece/saniye) ve CHARS_PER_SYLLABLE (karakter/hece) artık
# shared/content-types.json'dan geliyor (app.core.content_constants) — tek
# kaynak, backend/app/api/routes/video.py ile paylaşılır.
# OpenAI structured outputs strict:true bile string maxLength'i zorlamıyor
# (doğrulandı, bkz. OpenAI docs: "pattern, minLength, format ... not enforced
# by the model in strict mode"), o yüzden şema yerine üretim sonrası
# deterministik kontrol + 1 yeniden deneme kullanılıyor (bkz.
# generate_educational_reel_storyboard).

_SYSTEM = """Sen Türkiye'nin en iyi SGS (Özel Güvenlik) ve SMMM sınav koçusun.
2 dakikalık Instagram Reels eğitim videoları üretiyorsun.
Her video 7 sahneden oluşur, akıcı Türkçe anlatım yapar, sınavda çıkan bilgilere odaklanır.

KURALLAR:
- Tüm çıktılar Türkçe.
- Sadece geçerli JSON döndür.
- voice_text uzunluğu kullanıcı promptundaki HECE BÜTÇESİ ve KARAKTER SINIRI
  talimatına göre belirlenir — bu talimatlardaki SAYI her zaman bağlayıcıdır.
  Aşağıdaki örnek JSON'daki voice_text metinleri hem alan yapısını hem de
  YAKLAŞIK hedef uzunluğu gösterir; onlardan çok daha kısa yazma.
- hook sahnesinde hook_text kısa ve çarpıcı olsun (maksimum 10 kelime, 2 satır).
- highlight_stat rakam veya yüzde içermeli (örn: "%73", "5 yıl", "3 gün").
- bullet_points maksimum 4 madde, her madde 8-12 kelime.
- common_mistake ve exam_tip 1-2 cümle.
- cta_text kanal adına yönlendirme içermeli: "@adimmusavir".
- Yasaklı ifadeler: "Teşekkür ederim", "Hoşçakalın", "İzlediğiniz için".
"""

# Sahne başına örnek voice_text parçaları — _build_scene_schema bunları
# hedef karakter aralığına (min_chars/max_chars) göre birleştirir/keser.
# Sabit uzunlukta tek bir örnek DEĞİL — few-shot çıpası çağrılan bütçeye göre
# değişir (örn. 30s/4 sahne ile 120s/15 sahne aynı örnek uzunluğunu kullanmamalı).
_SCENE_EXAMPLE_PARTS: dict[int, list[str]] = {
    1: [  # hook
        "SGS sınavına girenlerin yaklaşık yüzde yetmişi bu soruyu yanlış yapıyor.",
        "Sen de aynı hataya düşmeden önce bu kuralı birlikte netleştirelim.",
        "Çünkü bu konu neredeyse her dönem karşımıza çıkıyor ve gözden kaçıyor.",
    ],
    2: [  # context
        "Bu konu her dönem sınavda karşına çıkıyor ve çoğu aday puan kaybediyor.",
        "Teorik bilgiyle pratik uygulamayı birbirine karıştırdığı için hata yapılıyor.",
        "Bu yüzden konuyu baştan sağlam öğrenmek uzun vadede zaman kazandırır.",
    ],
    3: [  # content 1
        "Kanunun ilgili maddesi net bir süre ve şart tanımlıyor.",
        "Bu süre dolmadan gerekli işlemi yapmazsan yetki belgen geçersiz sayılır.",
        "Geçersiz belgeyle görev yapmak hem senin hem kurumun sorumluluğunu artırır.",
    ],
    4: [  # content 2
        "Örneğin bir aday süresini kaçırdığında yeniden başvuru sürecine girer.",
        "Bu hem zaman hem de ek belge kaybı anlamına gelir, dikkatli olmak gerekir.",
        "Sınavda bu tür örnek senaryolar sorularak bilgin pratikte test edilir.",
    ],
    5: [  # mistake
        "Adayların çoğu 'süre dolsa da görevime devam ederim' sanıyor.",
        "Bu tamamen yanlış — geçersiz belgeyle çalışmak kanuna aykırıdır.",
        "Bu hatanın cezai sonucu olabilir, bu yüzden süreyi asla göz ardı etme.",
    ],
    6: [  # tip
        "Soru kökünde süreyle ilgili bir ifade görürsen önce ilgili maddeyi hatırla.",
        "Sonra şıklardaki sayılara değil kurala odaklanarak cevap ver.",
        "Bu yöntemle benzer sorularda da hızlıca doğru şıkka ulaşabilirsin.",
    ],
    7: [  # outro / cta
        "Özetle: süreyi takip et, belgeni zamanında yenile ve kuralı ezbere değil mantığıyla öğren.",
        "Daha fazla soru için @adimmusavir'i takip etmeyi unutma.",
        "Her hafta yeni bir SGS konusunu birlikte netleştiriyoruz.",
    ],
}


def _fit_example_text(parts: list[str], target_min: int, target_max: int) -> str:
    """
    parts'i [target_min, target_max] karakter aralığına en yakın olacak
    şekilde birleştirir/keser. Kısa kalırsa parça ekler, uzarsa kelime
    sınırında keser — few-shot örneği çağrılan bütçeye göre ölçeklenir.
    """
    text = parts[0]
    for extra in parts[1:]:
        if len(text) >= target_min:
            break
        text = f"{text} {extra}"
    if len(text) > target_max:
        truncated = text[:target_max]
        last_space = truncated.rfind(" ")
        if last_space > target_max * 0.5:
            truncated = truncated[:last_space]
        text = truncated.rstrip(".,;: ") + "."
    return text


def _build_scene_schema(min_chars: int, max_chars: int, target_scene_count: int = 7, min_card_scenes: int | None = None) -> str:
    _min_cards = min_card_scenes if min_card_scenes is not None else min_card_scenes_for(target_scene_count)
    ex = {i: _fit_example_text(parts, min_chars, max_chars) for i, parts in _SCENE_EXAMPLE_PARTS.items()}
    return f"""
Storyboard JSON formatı — aşağıdaki 7 sahne SADECE İÇERİK TÜRLERİNİN (hook,
context, content, mistake, tip, cta) BİRER ÖRNEĞİDİR, sabit bir sahne sayısı
DEĞİLDİR. Gerçek hedef {target_scene_count} sahne — eksikse 3./4. "content"
tipi sahneleri (ek bilgi, ek örnek, ek kart bileşeni) çoğaltarak tamamla.
ÖNEMLİ: Aşağıdaki voice_text ÖRNEKLERİ hem İÇERİK TÜRÜNÜ hem de HEDEF
UZUNLUĞU (yaklaşık {min_chars}-{max_chars} karakter) gösterir — model somut
örnekleri taklit eder. Kendi konunla değiştir ama YAKLAŞIK AYNI UZUNLUKTA
yaz; asıl bağlayıcı sayı prompt'taki HECE BÜTÇESİ / KARAKTER SINIRI
talimatıdır, bu örnekler değil.

{{
  "scenes": [
    {{
      "id": 1,
      "component": "ReelHookScene",
      "visual_source": "text_only",
      "hook_text": "Kısa çarpıcı kanca (2 satır, maks 10 kelime)",
      "highlight_stat": "Dikkat çeken rakam/yüzde",
      "voice_text": {json.dumps(ex[1], ensure_ascii=False)}
    }},
    {{
      "id": 2,
      "component": "ReelConceptScene",
      "visual_source": "card",
      "title": "Neden bilmen gerekiyor?",
      "bullet_points": ["Madde 1", "Madde 2", "Madde 3"],
      "voice_text": {json.dumps(ex[2], ensure_ascii=False)}
    }},
    {{
      "id": 3,
      "component": "ReelConceptScene",
      "visual_source": "card",
      "title": "Ana Kural / Birinci Bilgi",
      "bullet_points": ["Madde 1", "Madde 2", "Madde 3", "Madde 4"],
      "voice_text": {json.dumps(ex[3], ensure_ascii=False)}
    }},
    {{
      "id": 4,
      "component": "ReelConceptScene",
      "visual_source": "card",
      "title": "İkinci Bilgi / Örnek",
      "bullet_points": ["Madde 1", "Madde 2", "Madde 3"],
      "voice_text": {json.dumps(ex[4], ensure_ascii=False)}
    }},
    {{
      "id": 5,
      "component": "ReelMistakeScene",
      "visual_source": "card",
      "title": "Dikkat!",
      "common_mistake": "Sık yapılan hatanın 1-2 cümlelik açıklaması",
      "voice_text": {json.dumps(ex[5], ensure_ascii=False)}
    }},
    {{
      "id": 6,
      "component": "ReelExamTipScene",
      "visual_source": "card",
      "title": "Sınav İpucu",
      "exam_tip": "Sınava özel pratik ipucu — 1-2 cümle",
      "voice_text": {json.dumps(ex[6], ensure_ascii=False)}
    }},
    {{
      "id": 7,
      "component": "ReelCtaScene",
      "visual_source": "text_only",
      "title": "Özet",
      "bullet_points": ["Özet madde 1", "Özet madde 2", "Özet madde 3"],
      "cta_text": "Daha fazla SGS sorusu için @adimmusavir'i takip et!",
      "voice_text": {json.dumps(ex[7], ensure_ascii=False)}
    }}
  ]
}}

YUKARIDAKİ 7 SAHNE ÖRNEKTİR, ÇIKTI DEĞİLDİR. Gerçek "scenes" dizin
{target_scene_count} eleman içermeli — 7'den azsa content/concept tipi
sahneleri çoğaltarak tamamla.

{_component_routing_rule(_min_cards, target_scene_count)}
AccountCardScene örneği:
{json.dumps(_ACCOUNT_CARD_EXAMPLE, ensure_ascii=False, indent=2)}
{ACCOUNT_CARD_FIELD_RULES}

JournalEntryScene örneği:
{json.dumps(_JOURNAL_ENTRY_EXAMPLE, ensure_ascii=False, indent=2)}

TableScene örneği:
{json.dumps(_TABLE_SCENE_EXAMPLE, ensure_ascii=False, indent=2)}

CommonMistakeScene örneği:
{json.dumps(_COMMON_MISTAKE_EXAMPLE, ensure_ascii=False, indent=2)}

RuleBoxScene örneği:
{json.dumps(_RULE_BOX_EXAMPLE, ensure_ascii=False, indent=2)}
"""

# AccountCardScene alan uzunluk kuralları — A.3. "hesap tanımı" segmenti için
# hangi component'in seçileceği (routing) A.5'in işi; bu kurallar alan
# ŞEKLİNİN kendisi, routing'den bağımsız.
ACCOUNT_CARD_FIELD_RULES = """
ACCOUNTCARDSCENE ALAN KURALLARI (component: "AccountCardScene" seçildiyse ZORUNLU):
- accountName: en fazla 4 kelime.
- purpose: 12-25 kelime arası (ne çok kısa kart boş kalır, ne çok uzun taşar).
- tip: 10-22 kelime arası.
- entryCaption: en fazla 6 kelime.
- journalEntry: en fazla 4 satır.
- journalEntry[].amount: GERÇEK rakam — "XXX"/"YYY" gibi placeholder YASAK.
  Türkçe binlik ayraçla yaz (nokta): "10.000". Yuvarlak, sade sayılar tercih
  et (10.000 / 2.000 / 12.000 gibi) — öğrenci kafası karışmasın.
- journalEntry toplam BORÇ (side="debit") tutarı = toplam ALACAK (side="credit")
  tutarı ZORUNLU. Eşit değilse üretim kod tarafında reddedilir (math_validation_failed).
- Borç/Alacak kural cümlesini YAZMA — bu alan koddan (nature'dan) türetilir,
  props'tan gelmez.
"""

_ACCOUNT_CARD_EXAMPLE = {
    "id": 99,
    "component": "AccountCardScene",
    "visual_source": "card",
    "accountCode": "191",
    "accountName": "İndirilecek KDV",
    "nature": "A",
    "purpose": "Alış faturalarında hesaplanan ve satış KDV'sinden indirilecek olan katma değer vergisini izlemek için kullanılan bir hesaptır.",
    "journalEntry": [
        {"code": "153", "name": "TİCARİ MALLAR", "side": "debit", "amount": "10.000"},
        {"code": "191", "name": "İNDİRİLECEK KDV", "side": "debit", "amount": "2.000"},
        {"code": "320", "name": "SATICILAR", "side": "credit", "amount": "12.000"},
    ],
    "entryCaption": "(Mal alış kaydı, KDV dahil)",
    "tip": "İndirilecek KDV bir varlık hesabıdır ve daima borç bakiye verir.",
    "voice_text": "İndirilecek KDV, alış faturalarındaki vergiyi izlediğin bir hesap.",
}

CARD_COMPONENTS = {
    "AccountCardScene", "JournalEntryScene", "TableScene",
    "RuleBoxScene", "CommonMistakeScene",
}


def min_card_scenes_for(scene_count: int) -> int:
    """Hedef sahne sayısına göre minimum kart bileşeni sayısı.

    2026-08-08 bulgusu: sahne sayısı 8→11'e çıkarılınca (NATURAL_SCENE_SECONDS
    kalibrasyonu) A.5'in sabit "2-4 kart" kuralı ORANLA ölçeklenmedi — 11
    sahnede 1 kart (%9) üretildi, önceki 8 sahnelik denemelerde 4-5 kart
    (%50-63) üretiliyordu. Sabit sayı yerine orana bağlandı.
    """
    return max(3, round(scene_count * 0.4))


# A.5 — segment → component YÖNLENDİRME kuralı. Model hangi içerik için hangi
# bileşeni seçeceğini burada öğrenir; _ALLOWED_COMPONENTS zaten izin veriyordu
# ama hiçbir yerde NE ZAMAN kullanılacağı anlatılmıyordu (A.4 sonrası boşluk).
def _component_routing_rule(min_card_scenes: int, scene_count: int) -> str:
    return f"""
BİLEŞEN SEÇİMİ (segment içeriğine göre) — varsayılan ReelConceptScene/ReelHookScene/
ReelCtaScene YERİNE, içerik aşağıdaki türlerden biriyse özel kart bileşenini seç:
  - Bir hesabı TANITIYORSA (kod, nitelik, amaç, tipik kayıt)  → AccountCardScene
  - Sadece bir YEVMİYE KAYDI örneği veriyorsa (hesap tanıtımı yok) → JournalEntryScene
  - İki hesap/kavramı YAN YANA KARŞILAŞTIRIYORSA               → TableScene
  - Sık yapılan bir hatayı Yanlış/Doğru ÇİFTİ olarak gösteriyorsa → CommonMistakeScene
  - Borç/Alacak ÇALIŞMA MANTIĞINI (kural listesi) özetliyorsa   → RuleBoxScene
  - Kanca (0-5s) veya kapanış/CTA ise                           → ReelHookScene / ReelCtaScene
Yukarıdakilerden hiçbiri uymuyorsa ReelConceptScene/ReelExampleScene kullan.
KART SAYISI (ZORUNLU): {scene_count} sahnenin EN AZ {min_card_scenes} tanesi yukarıdaki
5 kart bileşeninden biri OLMALI (AccountCardScene/JournalEntryScene/TableScene/
CommonMistakeScene/RuleBoxScene) — hepsi ReelConceptScene/ReelHookScene/ReelCtaScene
olmasın. Konuda hesap/yevmiye/karşılaştırma/hata/kural içeriği varsa bunu kart
bileşenine ÇEVİR, düz metin sahnesi olarak bırakma.
"""

_JOURNAL_ENTRY_EXAMPLE = {
    "id": 98,
    "component": "JournalEntryScene",
    "visual_source": "card",
    "title": "Mal Satış Kaydı",
    "journalEntry": [
        {"code": "120", "name": "ALICILAR", "side": "debit", "amount": "12.000"},
        {"code": "600", "name": "YURT İÇİ SATIŞLAR", "side": "credit", "amount": "10.000"},
        {"code": "391", "name": "HESAPLANAN KDV", "side": "credit", "amount": "2.000"},
    ],
    "entryCaption": "(Vadeli satış kaydı)",
    "explanation": "Satış anında KDV alacak tarafına yazılır — hesaplanan KDV bir borçtur.",
    "voice_text": "Bir satış yaptığında yevmiyeye böyle kaydedersin.",
}

_TABLE_SCENE_EXAMPLE = {
    "id": 97,
    "component": "TableScene",
    "visual_source": "card",
    "title": "191 ile 391 Arasındaki Fark",
    "subtitle": "İndirilecek KDV vs Hesaplanan KDV",
    "headers": ["Özellik", "191", "391"],
    "rows": [["Nitelik", "Aktif", "Pasif"], ["Doğar", "Alışta", "Satışta"], ["Bakiye", "Borç", "Alacak"]],
    "voice_text": "İki KDV hesabını yan yana koyunca fark hemen görünüyor.",
}

_COMMON_MISTAKE_EXAMPLE = {
    "id": 96,
    "component": "CommonMistakeScene",
    "visual_source": "card",
    "title": "Sık Yapılan Hata",
    "common_mistake": "İndirilecek KDV ile Hesaplanan KDV karıştırılıyor.",
    "wrong_example": "İndirilecek KDV her zaman alacak hesabıdır.",
    "correct_example": "İndirilecek KDV aktif bir hesaptır, borç bakiye verir.",
    "explanation": "Aktif hesaplar borç artar mantığıyla çalışır.",
    "voice_text": "Bu ikisini karıştırmak sınavda en çok net kaybettiren hatalardan biri.",
}

_RULE_BOX_EXAMPLE = {
    "id": 95,
    "component": "RuleBoxScene",
    "visual_source": "card",
    "title": "Borç-Alacak Çalışma Mantığı",
    "nature": "A",
    "rules": [
        {"label": "Aktif", "left": "Borç → ARTAR", "right": "Alacak → AZALIR"},
        {"label": "Pasif", "left": "Borç → AZALIR", "right": "Alacak → ARTAR"},
    ],
    "voice_text": "Bu dört satırı ezberlersen tüm yevmiye kayıtları kolaylaşır.",
}


# segment_type → component adı eşlemesi (post-processing fallback)
_SEGMENT_COMPONENT: dict[str, str] = {
    "hook":    "ReelHookScene",
    "context": "ReelConceptScene",
    "content": "ReelConceptScene",
    "mistake": "ReelMistakeScene",
    "tip":     "ReelExamTipScene",
    "outro":   "ReelCtaScene",
}
_ALLOWED_COMPONENTS = set(_SEGMENT_COMPONENT.values()) | {
    "AccountCardScene", "JournalEntryScene", "TableScene",
    "RuleBoxScene", "CommonMistakeScene", "ReelExampleScene",
    "EducationalReelScene",
}

# component → visual_source. 2026-08-07 postmortem: backend reels sahnelerine
# visual_source hiç YAZMIYORDU (yalnızca motivasyon jeneratörü yazıyordu,
# video.py _attach_visual_assets). LLM'in few-shot örnekten kopyalaması umuluyordu
# ama context/content/mistake/tip örnekleri (id 2-6, _build_scene_schema) hiç
# visual_source göstermiyordu — model çoğu zaman bu alanı boş bırakıyordu.
# Sonuç: EducationalReelScene.tsx'teki A.6 kapısı (visual_content_missing) fotoğrafsız
# VE visual_source='text_only' olmayan her metin-sahnede ateşliyordu. Değerler
# migrations/014_p0_schema_fixes.sql'deki video_scenes_visual_source_check CHECK
# kısıtıyla birebir eşleşmeli ('photo','card','table','journal','board','text_only').
# "EducationalReelScene" (bare, geriye dönük uyumluluk adı) burada YOK — gerçek
# görsel ihtiyacı segment_type'a göre değişir, tek bir sabit değere indirgenemez;
# bu isim gelirse de sessizce varsayılan atamak yerine hata verilir.
VISUAL_SOURCE_BY_COMPONENT: dict[str, str] = {
    "AccountCardScene":   "card",
    "JournalEntryScene":  "journal",
    "TableScene":         "table",
    "CommonMistakeScene": "card",
    "RuleBoxScene":       "board",
    "ReelHookScene":      "text_only",
    "ReelCtaScene":       "text_only",
    "ReelConceptScene":   "text_only",
    "ReelExampleScene":   "text_only",
    "ReelExamTipScene":   "text_only",
    "ReelMistakeScene":   "text_only",
}


def _apply_series_title(title: str, topic: str, content_series: str | None) -> str:
    """İçerik serisine göre video başlığını şablondan üretir."""
    if not content_series or content_series not in SERIES_TITLE_TEMPLATES:
        return title
    template = SERIES_TITLE_TEMPLATES[content_series]
    return template.format(topic=topic or title)


def generate_educational_reel_storyboard(
    title: str,
    topic: str,
    subject: str,
    content_series: str | None = None,
    description: str = "",
    brand: dict | None = None,
    budget_seconds: float | None = None,
    syllable_feedback: str | None = None,
    scene_count: int | None = None,
) -> dict:
    """
    EducationalReel120 composition için storyboard üretir.
    scene_count verilmezse content_constants.scene_count_for_budget ile hesaplanır
    (NATURAL_SCENE_SECONDS=5.5 — tek kaynak, video.py._syllable_budget_params ile
    aynı fonksiyonu kullanır; önceden burada ayrıca "8.0" hardcode edilmişti).
    voice_text karakter sınırı üretim sonrası deterministik kontrol edilir ve
    aşılırsa 1 kez yeniden denenir — OpenAI structured outputs strict:true bile
    string maxLength'i şema seviyesinde zorlamıyor (bkz. CHARS_PER_SYLLABLE notu),
    o yüzden şemaya güvenmek yerine burada ölçülüyor.
    Döner: tam storyboard dict (video_type, scenes, brand vb.)
    """
    from app.modules.content.pronunciation_dict import latex_to_spoken_turkish  # noqa: F401

    series_label = ""
    if content_series and content_series in SERIES_TITLE_TEMPLATES:
        series_label = f"İçerik serisi: {SERIES_TITLE_TEMPLATES[content_series].replace('{topic}', topic)}\n"

    desc_note = f"Ek bağlam / yönetmen notu: {description}\n" if description else ""

    min_chars: int | None = None
    max_chars: int | None = None
    target_chars: int | None = None
    budget_note = ""
    if budget_seconds is not None:
        _sc = scene_count if (scene_count and scene_count > 0) else scene_count_for_budget(budget_seconds, "reels_short")
        _sc = max(1, _sc)
        # Tek kaynak: hece bütçesi kapısı (video.py _check_syllable_budget) ve
        # buradaki karakter sınırı artık AYNI fonksiyondan geliyor. Önceki hata:
        # ikisi bağımsız hesaplanıyordu ve farklı budget_seconds/scene_count
        # değerlerinden sistematik olarak sapıyordu (bkz. budget_params docstring).
        _total_syl, _syl_per_scene, min_chars, max_chars = budget_params(budget_seconds, _sc, "reels_short")
        _tolerance = max(3, round(_syl_per_scene * 0.15))
        target_chars = round(_syl_per_scene * CHARS_PER_SYLLABLE)
        budget_note = (
            f"\nHECE BÜTÇESİ (ZORUNLU): Toplam {_total_syl} hece "
            f"({budget_seconds:.0f}s × {TR_SPS:.2f} hece/s, {_sc} sahne).\n"
            f"Her sahne voice_text'inde yaklaşık {_syl_per_scene} hece kullan "
            f"(±{_tolerance} tolerans, yani {_syl_per_scene - _tolerance}–{_syl_per_scene + _tolerance} arası).\n"
            f"Türkçede hece = metindeki ünlü harf sayısı (a,e,ı,i,o,ö,u,ü).\n"
            f"KARAKTER UZUNLUĞU: Her sahne voice_text'i YAKLAŞIK {target_chars} karakter "
            f"olmalı (boşluklar dahil, ±%15 — yani {min_chars}-{max_chars} arası kabul "
            f"edilir ama HEDEFİN {target_chars} olduğunu unutma). Aralığın alt ucuna "
            f"yapışma — tam {target_chars}'i hedefle.\n"
        )
    else:
        _sc = scene_count if (scene_count and scene_count > 0) else 7
        # budget_seconds verilmediğinde de few-shot örneği makul bir uzunlukta
        # olmalı — DEFAULT_DURATION_SECONDS (Remotion tarafı, 15s/sahne) ile
        # tutarlı bir orta değer.
        _, _default_syl_per_scene, min_chars, max_chars = budget_params(15 * _sc, _sc, "reels_short")

    _sc_min = _sc - 2
    _sc_max = _sc + 3
    _min_cards = min_card_scenes_for(_sc)
    _scene_schema = _build_scene_schema(min_chars, max_chars, _sc, _min_cards)

    def _attempt(extra_feedback: str) -> list[dict]:
        """Tek bir GPT üretim denemesi — prompt kur, çağır, sahneleri normalize et."""
        combined = f"{syllable_feedback or ''}\n{extra_feedback}".strip()
        feedback_note = f"\nDÜZELTME GEREKLİ (önceki üretimden): {combined}\n" if combined else ""

        # Sahne sayısı talimatı hem BAŞTA (primacy) hem SONDA (recency) tekrarlanıyor —
        # 2026-08-07 bulgusu: talimat yalnızca promptun en sonunda, aşağıdaki 7 sahnelik
        # somut JSON örneğinden SONRA geliyordu; model tutarlı biçimde örnekteki 7-8
        # sahne yapısına çıpalanıp sayı talimatını görmezden geliyordu.
        _scene_count_instruction = (
            f"SAHNE SAYISI (ZORUNLU): {_sc_min}–{_sc_max} sahne üret, hedef {_sc}. "
            f"Aşağıdaki JSON örneği yalnızca İÇERİK TÜRÜ ve UZUNLUK göstergesidir — "
            f"7 sahnelik SABİT bir şablon DEĞİLDİR. {_sc} sahneye ulaşmak için "
            f"'content'/'concept' tipi sahneleri (3. bilgi, 4. bilgi, ek örnek, ek kart "
            f"bileşeni gibi) ÇOĞALT. Örnekteki sahne sayısından AZ üretme."
        )

        prompt = f"""Aşağıdaki SGS konusu için EducationalReel120 storyboard üret.

{_scene_count_instruction}

Konu: {topic}
Ders / Alan: {subject}
Video başlığı: {title}
{series_label}{desc_note}{budget_note}{feedback_note}
{_scene_schema}

ÖNEMLİ (tekrar): {_sc_min}–{_sc_max} sahne üret (hedef {_sc}). Her sahnede voice_text zorunlu. Sadece JSON döndür.
"""
        logger.info(
            "[reel-prompt] bütçe=%ss hedef_sahne=%d aralık=%d-%d hedef_karakter=%s "
            "prompt_uzunluk=%d karakter",
            budget_seconds, _sc, _sc_min, _sc_max, target_chars, len(prompt),
        )
        logger.debug("[reel-prompt] tam metin:\n%s", prompt)
        try:
            raw = _client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                temperature=0.45,
                max_tokens=4000,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user",   "content": prompt},
                ],
            )
            data = json.loads(raw.choices[0].message.content)
            _scenes = data.get("scenes", [])
        except Exception as exc:
            logger.error(f"[reel_storyboard] GPT hatası: {exc}")
            raise RuntimeError(f"EducationalReel storyboard üretilemedi: {exc}") from exc

        # Unicode NFC normalleştirme
        def _norm(obj):
            if isinstance(obj, str):
                return unicodedata.normalize("NFC", obj)
            if isinstance(obj, list):
                return [_norm(i) for i in obj]
            if isinstance(obj, dict):
                return {k: _norm(v) for k, v in obj.items()}
            return obj
        _scenes = _norm(_scenes)

        # id'leri sırayla ata, component'i doğrula/düzelt
        _default_types = ["hook", "context", "content", "content", "mistake", "tip", "outro"]
        for i, s in enumerate(_scenes, 1):
            s["id"] = i
            # LLM bilinmeyen bileşen ürettiyse segment_type'dan türet
            if s.get("component") not in _ALLOWED_COMPONENTS:
                _raw_component = s.get("component")
                seg = s.get("segment_type") or (_default_types[i - 1] if i <= len(_default_types) else "content")
                s["component"] = _SEGMENT_COMPONENT.get(seg, "ReelConceptScene")
                logger.warning(
                    "[reel-component-map] sahne=%d LLM geçersiz component üretti (%r) — "
                    "segment_type=%s üzerinden %s'e düşüldü (A.5 yönlendirme kuralı izlenmedi)",
                    i, _raw_component, seg, s["component"],
                )
            # segment_type eksikse component'tan çıkar (reverse map)
            if not s.get("segment_type"):
                _rev = {v: k for k, v in _SEGMENT_COMPONENT.items()}
                s["segment_type"] = _rev.get(s["component"], "content")
            # voice_text eksikse basit fallback
            if not (s.get("voice_text") or "").strip():
                s["voice_text"] = s.get("hook_text") or s.get("title") or topic
        return _scenes

    scenes = _attempt("")

    if not (_sc_min <= len(scenes) <= _sc_max):
        logger.warning(
            "[reel-scene-count] istenen=%d (%d-%d) üretilen=%d — model sahne sayısı "
            "talimatına uymadı, fark=%+d",
            _sc, _sc_min, _sc_max, len(scenes), len(scenes) - _sc,
        )
    else:
        logger.info(
            "[reel-scene-count] istenen=%d (%d-%d) üretilen=%d — OK",
            _sc, _sc_min, _sc_max, len(scenes),
        )

    # ── kart bileşeni sayısı — 1 yeniden deneme ──────────────────────────
    # 2026-08-08 bulgusu: sahne sayısı 8→11'e çıkarılınca A.5'in sabit "2-4 kart"
    # kuralı ORANLA ölçeklenmedi, 11 sahnede 1 kart üretildi (%9, önceki 8
    # sahnelik denemelerde %50-63'tü). min_card_scenes_for ile orana bağlandı;
    # eşiğin altında kalırsa journal-balance/voice-text-length ÖNCESİ (yapıyı
    # önce düzelt, sonra içerik/uzunluk kontrolüne geç) bir kez geri beslenir.
    # Hâlâ yetersizse hard fail YOK (içerik-kalitesi kaygısı, doğruluk kapısı
    # değil) — yalnızca loglanır, tıpkı önceki card_scene_count==0 uyarısı gibi.
    # _min_cards yukarıda (_scene_schema kurulurken) zaten hesaplandı.
    _card_count_now = sum(1 for s in scenes if s.get("component") in CARD_COMPONENTS)
    if _card_count_now < _min_cards:
        logger.warning(
            "[reel-card-count] deneme=1/2 istenen_min=%d üretilen=%d/%d — yeniden deneniyor",
            _min_cards, _card_count_now, len(scenes),
        )
        scenes = _attempt(
            f"Önceki üretimde yalnızca {_card_count_now} sahne kart bileşeni kullandı, "
            f"en az {_min_cards} olmalıydı. Hesap tanımı/yevmiye kaydı/karşılaştırma/"
            f"sık hata/borç-alacak kuralı içeren 'content' tipi sahneleri "
            f"AccountCardScene/JournalEntryScene/TableScene/CommonMistakeScene/"
            f"RuleBoxScene'e ÇEVİR — düz metin (ReelConceptScene) olarak bırakma."
        )
        _card_count_now = sum(1 for s in scenes if s.get("component") in CARD_COMPONENTS)
        if _card_count_now < _min_cards:
            logger.warning(
                "[reel-card-count] deneme=2/2 istenen_min=%d üretilen=%d/%d — hâlâ yetersiz, "
                "hard fail yok (içerik kalitesi kaygısı, doğrulama kapısı değil)",
                _min_cards, _card_count_now, len(scenes),
            )
        else:
            logger.info(
                "[reel-card-count] deneme=2/2 istenen_min=%d üretilen=%d/%d — düzeldi",
                _min_cards, _card_count_now, len(scenes),
            )
    else:
        logger.info(
            "[reel-card-count] istenen_min=%d üretilen=%d/%d — OK",
            _min_cards, _card_count_now, len(scenes),
        )

    # ── journalEntry borç=alacak doğrulaması — HARD kapı (math_validation_failed) ──
    # Karakter uzunluğu kontrolünün aksine sessizce loglanıp geçilmez: borç≠alacak
    # olan bir kayıt öğrenciye yanlış bilgi öğretir, video durdurulmalı.
    for _bal_attempt in (1, 2):
        balance_problems = _check_journal_balance(scenes)
        if not balance_problems:
            if _bal_attempt > 1:
                logger.info("[journal-balance] deneme=%d/2 düzeltildi", _bal_attempt)
            break
        logger.warning("[journal-balance] deneme=%d/2 sorunlar: %s", _bal_attempt, balance_problems)
        if _bal_attempt == 1:
            scenes = _attempt(
                "Önceki üretimde journalEntry borç/alacak dengesi hatalıydı: "
                + "; ".join(balance_problems)
                + ". Tüm journalEntry tutarlarını GERÇEK rakamla ver (XXX/YYY yasak) "
                  "ve borç toplamı = alacak toplamı olacak şekilde düzelt."
            )
        else:
            from app.errors.registry import PipelineErrorException
            raise PipelineErrorException(
                "math_validation_failed",
                admin_detail={"reason": "journal_balance_mismatch", "problems": balance_problems},
                stage="llm",
            )

    # ── voice_text karakter aralığı — deterministik kontrol + 1 yeniden deneme ──
    # Şema seviyesinde zorlanamıyor (bkz. yukarıdaki not); sessizce geçilmiyor —
    # her deneme loglanır. Hem TAVAN (aşım) hem TABAN (kısa kalma) denetlenir —
    # yalnızca tavan kontrolü modelin tavanın çok altında (sabit ~155 hece)
    # takılıp kalmasını yakalayamıyordu. 2. denemede de aralık dışındaysa
    # downstream hece bütçesi kapısı (_check_syllable_budget / duration_validation_failed)
    # son savunma.
    if max_chars is not None and min_chars is not None:
        for attempt in (1, 2):
            out_of_range = [
                (s.get("id", i + 1), len(s.get("voice_text") or ""))
                for i, s in enumerate(scenes)
                if not (min_chars <= len(s.get("voice_text") or "") <= max_chars)
            ]
            if not out_of_range:
                logger.info(
                    "[voice-text-length] deneme=%d/2 bütçe_saniye=%.1f tüm sahneler aralıkta "
                    "(hedef=%s limit=%d-%d karakter)",
                    attempt, budget_seconds or 0.0, target_chars, min_chars, max_chars,
                )
                break
            for scene_id, n in out_of_range:
                yon = "aşım" if n > max_chars else "kısa"
                sinir = max_chars if n > max_chars else min_chars
                pct = (n / sinir - 1) * 100
                logger.warning(
                    "[voice-text-length] deneme=%d/2 bütçe_saniye=%.1f sahne=%s karakter=%d "
                    "hedef=%s limit=%d-%d yön=%s sapma=%%%.0f",
                    attempt, budget_seconds or 0.0, scene_id, n, target_chars, min_chars, max_chars, yon, pct,
                )
            if attempt == 1:
                too_long = [(sid, n) for sid, n in out_of_range if n > max_chars]
                too_short = [(sid, n) for sid, n in out_of_range if n < min_chars]
                parts = []
                # Tek hedef sayı ver, aralık değil — modeller aralığın alt/üst
                # ucuna yapışıyor (bkz. prompt notu). "En az/en fazla" yerine
                # "TAM {target_chars}'e getir" diyerek aynı prensip retry'de de uygulanıyor.
                if too_long:
                    parts.append(
                        "ÇOK UZUN: " + "; ".join(f"sahne {sid}: {n} karakter" for sid, n in too_long) +
                        f" — TAM {target_chars} karaktere KISALT (üst sınıra değil, hedefe getir)."
                    )
                if too_short:
                    parts.append(
                        "ÇOK KISA: " + "; ".join(f"sahne {sid}: {n} karakter" for sid, n in too_short) +
                        f" — TAM {target_chars} karaktere UZAT (alt sınıra değil, hedefe getir; "
                        f"daha fazla ayrıntı/örnek ekle)."
                    )
                scenes = _attempt(
                    "Önceki üretimde şu sahnelerin voice_text'i hedeften saptı. "
                    + " ".join(parts)
                )
            else:
                logger.error(
                    "[voice-text-length] 2 denemede de karakter hedefi sağlanamadı — "
                    "downstream hece bütçesi kapısı son savunma."
                )

    # visual_source ataması — component adından deterministik türetilir (LLM'e
    # bırakılmıyor, bkz. VISUAL_SOURCE_BY_COMPONENT tanımı). Eşlemede olmayan
    # bileşen adı = kod hatası (yeni component eklenip burası güncellenmemiş) —
    # sessiz varsayılan YOK, hard fail.
    for s in scenes:
        comp = s.get("component", "?")
        if comp not in VISUAL_SOURCE_BY_COMPONENT:
            raise RuntimeError(
                f"visual_source_mapping_missing: component={comp!r} (sahne {s.get('id', '?')}) "
                f"VISUAL_SOURCE_BY_COMPONENT eşlemesinde yok — yeni bir bileşen eklenmiş "
                f"olabilir, educational_reel_storyboard.py'de eşlemeyi güncelleyin."
            )
        s["visual_source"] = VISUAL_SOURCE_BY_COMPONENT[comp]

    # A.5/A.6 doğrulaması — her sahnenin bir bileşene eşlendiğini logla.
    # A.6'da sessiz fallback kaldırılmadan önce bu logun gerçek bir dağılım
    # göstermesi (hepsi ReelConceptScene DEĞİL) gerekir. Bu, kart-sayısı
    # yeniden deneme(ler)inden SONRAKİ nihai dağılımı yansıtır.
    _component_counts: dict[str, int] = {}
    for s in scenes:
        comp = s.get("component", "?")
        _component_counts[comp] = _component_counts.get(comp, 0) + 1
        logger.info(
            "[reel-component-map] sahne=%s component=%s segment_type=%s kart_mi=%s visual_source=%s",
            s.get("id", "?"), comp, s.get("segment_type", "?"), comp in CARD_COMPONENTS, s.get("visual_source"),
        )
    _card_scene_count = sum(v for k, v in _component_counts.items() if k in CARD_COMPONENTS)
    logger.info(
        "[reel-component-map] ÖZET topic=%r toplam_sahne=%d kart_sahne=%d (min=%d) dağılım=%s",
        topic, len(scenes), _card_scene_count, _min_cards, _component_counts,
    )
    if _card_scene_count < _min_cards:
        logger.warning(
            "[reel-component-map] UYARI: kart sahnesi hedefin altında (%d/%d) — "
            "A.5 yönlendirme kuralı 2 denemede de tam çalışmadı.",
            _card_scene_count, _min_cards,
        )

    if len(scenes) < 5:
        logger.warning(f"[reel_storyboard] Yetersiz sahne üretildi: {len(scenes)}/7")

    final_title = _apply_series_title(title, topic, content_series)

    default_brand = {
        "primary_color": "#0B2A4A", "secondary_color": "#C9A96E",
        "background_color": "#FAF7F0", "font_heading": "Playfair Display",
        "font_body": "Lato", "handle": "@adimmusavir",
    }
    if brand:
        default_brand.update(brand)

    return {
        "video_type":    "reel",
        "title":         final_title,
        "lesson_name":   subject,
        "topic":         topic,
        "format":        "9:16",
        "language":      "tr",
        "brand":         default_brand,
        "content_series": content_series,
        "scenes":        scenes,
    }
