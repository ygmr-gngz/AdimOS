"""SGS analizleri için Supabase repo."""
import re
import unicodedata
from difflib import SequenceMatcher
from app.db.supabase import get_supabase_client

# Konu adı (lowercase) → doğru ders eşleştirmesi.
# Parse sırasında ve reclassify endpoint'inde kullanılır.
_TOPIC_LESSON_MAP: dict[str, str] = {
    # Türkçe
    "anlam bilgisi": "Türkçe", "sözcükte anlam": "Türkçe", "cümlede anlam": "Türkçe",
    "paragraf": "Türkçe", "yazım kuralları": "Türkçe", "noktalama": "Türkçe",
    "anlatım bozukluğu": "Türkçe", "ses bilgisi": "Türkçe", "dil bilgisi": "Türkçe",
    "sözcük türleri": "Türkçe", "cümle bilgisi": "Türkçe", "cümle öğeleri": "Türkçe",
    "kelime türleri": "Türkçe", "kelime anlamı": "Türkçe",
    "metin türleri": "Türkçe", "okuduğunu anlama": "Türkçe",
    "sözcük": "Türkçe", "kelime": "Türkçe",
    "deyimler": "Türkçe", "atasözleri": "Türkçe",
    "fiil çekimi": "Türkçe", "eylem": "Türkçe",
    "dilbilgisi": "Türkçe", "imla": "Türkçe",
    # Matematik — AI'nin üretebileceği tüm varyantlar
    "denklemler": "Matematik", "denklem": "Matematik",
    "fonksiyonlar": "Matematik", "fonksiyon": "Matematik",
    "problemler": "Matematik",
    "sayılar": "Matematik", "doğal sayılar": "Matematik", "tam sayılar": "Matematik",
    "rasyonel sayılar": "Matematik", "gerçek sayılar": "Matematik", "sayı sistemleri": "Matematik",
    "kümeler": "Matematik", "küme teorisi": "Matematik",
    "oran orantı": "Matematik", "yüzdeler": "Matematik", "yüzde hesabı": "Matematik",
    "olasılık": "Matematik", "istatistik": "Matematik",
    "geometri": "Matematik", "analitik geometri": "Matematik", "düzlem geometri": "Matematik",
    "logaritma": "Matematik", "üslü ifadeler": "Matematik", "köklü ifadeler": "Matematik",
    "permütasyon": "Matematik", "kombinasyon": "Matematik",
    "eşitsizlik": "Matematik", "mutlak değer": "Matematik",
    "diziler": "Matematik", "seriler": "Matematik",
    "trigonometri": "Matematik", "vektörler": "Matematik", "matrisler": "Matematik",
    "limit": "Matematik", "türev": "Matematik", "integral": "Matematik",
    "polinomlar": "Matematik", "çarpanlara ayırma": "Matematik",
    "aritmetik": "Matematik", "cebir": "Matematik",
    "kesirler": "Matematik", "ondalık sayılar": "Matematik",
    # Tarih - Genel Kültür
    "cumhuriyet tarihi": "Tarih - Genel Kültür", "atatürk ilkeleri": "Tarih - Genel Kültür",
    "inkılap tarihi": "Tarih - Genel Kültür", "osmanlı tarihi": "Tarih - Genel Kültür",
    "genel kültür": "Tarih - Genel Kültür", "kurtuluş savaşı": "Tarih - Genel Kültür",
    "türk tarihi": "Tarih - Genel Kültür",
    # İngilizce
    "grammar": "İngilizce", "vocabulary": "İngilizce", "tense": "İngilizce",
    "reading comprehension": "İngilizce", "sentence completion": "İngilizce",
    "word formation": "İngilizce", "cloze test": "İngilizce", "reading": "İngilizce",
    # Almanca
    "grammatik": "Almanca", "leseverstehen": "Almanca", "vokabeln": "Almanca",
    "textverständnis": "Almanca",
    # Finansal Muhasebe
    "yevmiye": "Finansal Muhasebe", "defter-i kebir": "Finansal Muhasebe",
    "mizan": "Finansal Muhasebe", "amortisman": "Finansal Muhasebe",
    "aktif / pasif hesaplar": "Finansal Muhasebe", "dönem sonu": "Finansal Muhasebe",
    "stoklar": "Finansal Muhasebe", "kasa ve banka": "Finansal Muhasebe",
    "aktif hesaplar": "Finansal Muhasebe", "pasif hesaplar": "Finansal Muhasebe",
    # Mali Tablolar Analizi
    "bilanço": "Mali Tablolar Analizi", "gelir tablosu": "Mali Tablolar Analizi",
    "nakit akım tablosu": "Mali Tablolar Analizi", "fon akım tablosu": "Mali Tablolar Analizi",
    "oran analizi": "Mali Tablolar Analizi", "likidite": "Mali Tablolar Analizi",
    # Muhasebe Bilgi Sistemi
    "tekdüzen hesap planı": "Muhasebe Bilgi Sistemi",
    "muhasebe bilgi sistemi": "Muhasebe Bilgi Sistemi",
    # Maliyet Muhasebesi
    "maliyet": "Maliyet Muhasebesi", "üretim maliyeti": "Maliyet Muhasebesi",
    "sipariş maliyeti": "Maliyet Muhasebesi", "safha maliyeti": "Maliyet Muhasebesi",
    "standart maliyet": "Maliyet Muhasebesi",
    # Muhasebe Standartları
    "tms": "Muhasebe Standartları", "tfrs": "Muhasebe Standartları",
    "muhasebe standartları": "Muhasebe Standartları",
    # Muhasebe Denetimi
    "denetim": "Muhasebe Denetimi", "iç kontrol": "Muhasebe Denetimi",
    "bağımsız denetim": "Muhasebe Denetimi", "iç denetim": "Muhasebe Denetimi",
    # Ticaret Hukuku
    "tacir": "Ticaret Hukuku", "ticari işletme": "Ticaret Hukuku",
    "ticaret unvanı": "Ticaret Hukuku", "ticaret sicili": "Ticaret Hukuku",
    "haksız rekabet": "Ticaret Hukuku", "ticaret şirketleri": "Ticaret Hukuku",
    "çek": "Ticaret Hukuku", "senet": "Ticaret Hukuku", "poliçe": "Ticaret Hukuku",
    # Borçlar Hukuku
    "sözleşme": "Borçlar Hukuku", "borç ilişkisi": "Borçlar Hukuku",
    "temerrüt": "Borçlar Hukuku", "haksız fiil": "Borçlar Hukuku",
    "zamanaşımı": "Borçlar Hukuku",
    # İş ve Sosyal Güvenlik Hukuku
    "iş sözleşmesi": "İş ve Sosyal Güvenlik Hukuku", "sgk": "İş ve Sosyal Güvenlik Hukuku",
    "kıdem tazminatı": "İş ve Sosyal Güvenlik Hukuku",
    "ihbar tazminatı": "İş ve Sosyal Güvenlik Hukuku", "emeklilik": "İş ve Sosyal Güvenlik Hukuku",
    # Vergi Hukuku
    "gelir vergisi": "Vergi Hukuku", "kdv": "Vergi Hukuku",
    "kurumlar vergisi": "Vergi Hukuku", "vergi usul": "Vergi Hukuku",
    "beyanname": "Vergi Hukuku", "stopaj": "Vergi Hukuku",
    # Maliye
    "bütçe": "Maliye", "kamu maliyesi": "Maliye", "maliye politikası": "Maliye",
    # İktisat
    "arz": "İktisat", "talep": "İktisat", "enflasyon": "İktisat",
    "para politikası": "İktisat", "büyüme": "İktisat", "piyasa": "İktisat", "gsyh": "İktisat",
    # Meslek Hukuku
    "smmm": "Meslek Hukuku", "ymm": "Meslek Hukuku",
    "meslek etiği": "Meslek Hukuku", "mesleki sorumluluk": "Meslek Hukuku",
    # ── Ders adlarının kendisi konu olarak gelirse (AI fallback davranışı) ──
    # AI bazen konu adı yerine ders adını yazar — bunları da yakala
    "matematik": "Matematik",
    "türkçe": "Türkçe",
    "tarih - genel kültür": "Tarih - Genel Kültür", "genel kültür dersi": "Tarih - Genel Kültür",
    "i̇ngilizce": "İngilizce", "ingilizce": "İngilizce",
    "almanca": "Almanca",
    "finansal muhasebe": "Finansal Muhasebe",
    "muhasebe standartları": "Muhasebe Standartları",
    "muhasebe bilgi sistemi": "Muhasebe Bilgi Sistemi",
    "maliyet muhasebesi": "Maliyet Muhasebesi",
    "mali tablolar analizi": "Mali Tablolar Analizi",
    "muhasebe denetimi": "Muhasebe Denetimi",
    "i̇ktisat": "İktisat", "iktisat": "İktisat",
    "maliye": "Maliye",
    "meslek hukuku": "Meslek Hukuku",
    "i̇ş ve sosyal güvenlik hukuku": "İş ve Sosyal Güvenlik Hukuku",
    "iş ve sosyal güvenlik hukuku": "İş ve Sosyal Güvenlik Hukuku",
    "vergi hukuku": "Vergi Hukuku",
    "ticaret hukuku": "Ticaret Hukuku",
    "borçlar hukuku": "Borçlar Hukuku",
    # Kısaltmalar ve yaygın AI varyantları
    "muhasebe": "Finansal Muhasebe",
    "hukuk": "Meslek Hukuku",
    "vergi": "Vergi Hukuku",
    "denetim ve standartlar": "Muhasebe Denetimi",
    "standartlar": "Muhasebe Standartları",
    "maliyet": "Maliyet Muhasebesi",
}


def _resolve_lesson_for_topic(topic: str, range_lesson: str) -> str:
    """Topic adına bakarak doğru dersi döndür. Kural yoksa range_lesson döner.
    Önce exact match, sonra substring match (min 5 karakter — kısa token false positive'i önler).
    """
    t_lower = (topic or "").lower().strip()
    if not t_lower:
        return range_lesson
    if t_lower in _TOPIC_LESSON_MAP:
        return _TOPIC_LESSON_MAP[t_lower]
    # Substring: uzun anahtar → kısa anahtar sırasıyla dene (en spesifik önce)
    for key in sorted(_TOPIC_LESSON_MAP.keys(), key=len, reverse=True):
        if len(key) >= 5 and key in t_lower:
            return _TOPIC_LESSON_MAP[key]
    return range_lesson


def save_range(document_name, start_no, end_no, lesson_name, notes="", document_id=None):
    supabase = get_supabase_client()
    payload = {
        "document_name": document_name,
        "start_question_no": int(start_no),
        "end_question_no": int(end_no),
        "lesson_name": lesson_name,
        "notes": notes or "",
    }
    if document_id:
        payload["document_id"] = document_id
    resp = supabase.table("sgs_question_ranges").insert(payload).execute()
    return resp.data[0] if resp.data else None


def get_ranges(document_name=None):
    supabase = get_supabase_client()
    query = supabase.table("sgs_question_ranges").select("*").order("start_question_no")
    if document_name:
        query = query.eq("document_name", document_name)
    resp = query.execute()
    return resp.data if resp.data else []


def delete_range(range_id):
    supabase = get_supabase_client()
    supabase.table("sgs_question_ranges").delete().eq("id", range_id).execute()


def find_lesson_for_question(document_name, question_no):
    supabase = get_supabase_client()
    resp = (
        supabase.table("sgs_question_ranges")
        .select("lesson_name")
        .eq("document_name", document_name)
        .lte("start_question_no", question_no)
        .gte("end_question_no", question_no)
        .limit(1)
        .execute()
    )
    return resp.data[0]["lesson_name"] if resp.data else None


def _norm_name(name: str) -> str:
    """PDF ismi normalize — Türkçe karakter, noktalama, uzantı standartlaştır."""
    name = (name or "").strip()
    # Türkçe I/İ/ı özel durumları (Python lower() yanlış sonuç verebilir)
    name = name.replace("İ", "I").replace("ı", "i")
    name = name.lower()
    name = name.removesuffix(".pdf").strip()
    # Diacritic kaldır: ş→s, ç→c, ğ→g, ö→o, ü→u, vb.
    name = "".join(c for c in unicodedata.normalize("NFD", name)
                   if unicodedata.category(c) != "Mn")
    # Alt çizgi, tire, nokta → boşluk
    name = re.sub(r"[_\-\.]+", " ", name)
    # Harf/rakam olmayan → boşluk
    name = re.sub(r"[^a-z0-9 ]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def _names_match(range_name: str, pdf_name: str) -> bool:
    """İki belge isminin aynı PDF'e ait olup olmadığını kontrol eder.
    1. Normalize edilmiş tam eşleşme
    2. Biri diğerini içeriyor (şantiye vs şantiye_2)
    3. Fuzzy benzerlik ≥ %75
    """
    r, p = _norm_name(range_name), _norm_name(pdf_name)
    if not r or not p:
        return False
    if r == p:
        return True
    if r in p or p in r:
        return True
    return SequenceMatcher(None, r, p).ratio() >= 0.75


def _find_analysis(rng: dict, analyses_by_id: dict, analyses_list: list) -> dict | None:
    """Bir aralık için en iyi analiz eşleşmesini bul.
    1. document_id ile kesin eşleşme
    2. İsim fuzzy benzerliği
    3. Tek analiz varsa otomatik kullan (tek PDF yüklenmiş senaryo)
    """
    doc_id = rng.get("document_id")
    if doc_id and doc_id in analyses_by_id:
        return analyses_by_id[doc_id]
    range_name = rng.get("document_name", "")
    for a in analyses_list:
        if _names_match(range_name, a.get("pdf_name", "")):
            return a
    # Tek analiz varsa ve document_id bağlı değilse → onu kullan
    if len(analyses_list) == 1 and not doc_id:
        return analyses_list[0]
    return None


def get_questions_by_ranges(
    lesson_name: str | None = None,
    group_lessons: list[str] | None = None,
    year: str | None = None,
) -> list[dict]:
    """Manuel soru aralıklarını kullanarak soruları döner.
    AI tahmini değil, kullanıcının girdiği aralıklar kaynak.
    """
    supabase = get_supabase_client()

    ranges_resp = supabase.table("sgs_question_ranges").select("*").execute()
    all_ranges = ranges_resp.data or []

    if lesson_name:
        target_ranges = [r for r in all_ranges if r["lesson_name"] == lesson_name]
    elif group_lessons:
        target_ranges = [r for r in all_ranges if r["lesson_name"] in group_lessons]
    else:
        target_ranges = all_ranges

    if not target_ranges:
        return []

    analyses_query = supabase.table("sgs_analyses").select("id, pdf_name, year, semester, questions")
    if year:
        analyses_query = analyses_query.eq("year", year)
    analyses_resp = analyses_query.execute()

    all_analyses: list[dict] = analyses_resp.data or []
    analyses_by_id: dict[str, dict] = {a["id"]: a for a in all_analyses}

    result = []
    for rng in target_ranges:
        analysis = _find_analysis(rng, analyses_by_id, all_analyses)
        if not analysis:
            continue
        start, end = rng["start_question_no"], rng["end_question_no"]
        lesson = rng["lesson_name"]
        for q in (analysis.get("questions") or []):
            q_id = q.get("id", 0)
            if start <= q_id <= end:
                result.append({
                    **q,
                    "subject": lesson,   # manuel aralık, AI tahmini override
                    "source_pdf": analysis.get("pdf_name", ""),
                    "source_year": analysis.get("year", ""),
                    "source_semester": analysis.get("semester", ""),
                    "analysis_id": analysis.get("id", ""),
                    "source_range_id": rng.get("id", ""),
                })
    return result


def get_areas_summary(year: str | None = None) -> list[dict]:
    """Alan bazlı soru özeti — beklenen (aralıklar) vs bulunan (analizler)."""
    from app.config.sgs_groups import SGS_LESSON_GROUPS
    supabase = get_supabase_client()

    ranges_resp = supabase.table("sgs_question_ranges").select("*").execute()
    all_ranges = ranges_resp.data or []

    analyses_query = supabase.table("sgs_analyses").select("id, pdf_name, year, questions")
    if year:
        analyses_query = analyses_query.eq("year", year)
    analyses_resp = analyses_query.execute()

    all_analyses: list[dict] = analyses_resp.data or []
    analyses_by_id: dict[str, dict] = {a["id"]: a for a in all_analyses}

    areas = []
    for area, lessons in SGS_LESSON_GROUPS.items():
        area_expected = 0
        area_found = 0
        lessons_data = []
        for lesson in lessons:
            lesson_ranges = [r for r in all_ranges if r["lesson_name"] == lesson]
            expected = sum(r["end_question_no"] - r["start_question_no"] + 1 for r in lesson_ranges)
            found = 0
            has_pdf_match = False
            for r in lesson_ranges:
                a = _find_analysis(r, analyses_by_id, all_analyses)
                if a:
                    has_pdf_match = True
                    s, e = r["start_question_no"], r["end_question_no"]
                    found += sum(1 for q in (a.get("questions") or []) if s <= q.get("id", 0) <= e)

            if len(lesson_ranges) == 0:
                lesson_status = "no_range"
            elif found > 0:
                lesson_status = "ready"
            elif has_pdf_match:
                lesson_status = "no_questions"
            else:
                lesson_status = "no_pdf"

            lessons_data.append({
                "name": lesson,
                "expected": expected,
                "found": found,
                "range_count": len(lesson_ranges),
                "status": lesson_status,
            })
            area_expected += expected
            area_found += found

        discrepancy = area_expected - area_found
        status = "ok" if area_expected > 0 and discrepancy == 0 else ("warning" if discrepancy > 0 and area_expected > 0 else "missing")
        areas.append({
            "name": area,
            "expected_total": area_expected,
            "found_total": area_found,
            "discrepancy": discrepancy,
            "status": status,
            "lessons": lessons_data,
        })
    return areas


def bulk_link_ranges_to_analysis(analysis_id: str) -> dict:
    """document_id boş olan tüm aralıkları verilen analize bağla."""
    supabase = get_supabase_client()
    check = supabase.table("sgs_analyses").select("id, pdf_name").eq("id", analysis_id).execute()
    if not check.data:
        return {"linked": 0, "error": "Analiz bulunamadı"}
    pdf_name = check.data[0]["pdf_name"]
    resp = (
        supabase.table("sgs_question_ranges")
        .update({"document_id": analysis_id, "document_name": pdf_name})
        .is_("document_id", "null")
        .execute()
    )
    return {"linked": len(resp.data or []), "pdf_name": pdf_name}


def get_all_questions(
    lesson_name: str | None = None,
    group_lessons: list[str] | None = None,
    year: str | None = None,
) -> list[dict]:
    """Tüm analizlerden ders/grup/yıl bazlı soru listesi döner."""
    supabase = get_supabase_client()
    query = supabase.table("sgs_analyses").select("id, pdf_name, year, semester, questions")
    if year:
        query = query.eq("year", year)
    resp = query.execute()

    result = []
    for analysis in (resp.data or []):
        for q in (analysis.get("questions") or []):
            subj = q.get("subject", "")
            if subj == "Belirsiz":
                continue
            if lesson_name and subj != lesson_name:
                continue
            if group_lessons and subj not in group_lessons:
                continue
            result.append({
                **q,
                "source_pdf": analysis.get("pdf_name", ""),
                "source_year": analysis.get("year", ""),
                "source_semester": analysis.get("semester", ""),
                "analysis_id": analysis.get("id", ""),
            })
    return result


def find_analysis_by_pdf_name(pdf_name: str) -> dict | None:
    """Aynı pdf_name ile daha önce yüklenmiş analiz var mı? Varsa döndür."""
    supabase = get_supabase_client()
    resp = (
        supabase.table("sgs_analyses")
        .select("id, pdf_name, document_type, year, semester, total_questions, subjects, questions, video_plan, status, created_at")
        .eq("pdf_name", pdf_name)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def create_analysis(
    pdf_name: str,
    total_questions: int,
    subjects: list,
    questions: list,
    video_plan: list,
    document_type: str = "Çıkmış Sorular",
    year: str = "",
    semester: str = "",
) -> dict | None:
    supabase = get_supabase_client()
    resp = supabase.table("sgs_analyses").insert({
        "pdf_name": pdf_name,
        "total_questions": total_questions,
        "subjects": subjects,
        "questions": questions,
        "video_plan": video_plan,
        "status": "completed",
        "document_type": document_type,
        "year": year,
        "semester": semester,
    }).execute()
    return resp.data[0] if resp.data else None


def list_analyses() -> list[dict]:
    supabase = get_supabase_client()
    resp = (
        supabase.table("sgs_analyses")
        .select("id, pdf_name, document_type, year, semester, total_questions, subjects, video_plan, status, created_at")
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data if resp.data else []


def get_analysis(analysis_id: str) -> dict | None:
    supabase = get_supabase_client()
    resp = supabase.table("sgs_analyses").select("*").eq("id", analysis_id).execute()
    return resp.data[0] if resp.data else None


def delete_analysis(analysis_id: str) -> None:
    supabase = get_supabase_client()
    supabase.table("sgs_analyses").delete().eq("id", analysis_id).execute()


def update_analysis(analysis_id: str, **fields) -> dict | None:
    """sgs_analyses satırındaki belirtilen alanları günceller."""
    if not fields:
        return None
    supabase = get_supabase_client()
    resp = supabase.table("sgs_analyses").update(fields).eq("id", analysis_id).execute()
    return resp.data[0] if resp.data else None


def update_question_subject(analysis_id: str, question_id: int, new_subject: str) -> dict | None:
    """Bir analizdeki belirli sorunun dersini günceller."""
    supabase = get_supabase_client()
    row = get_analysis(analysis_id)
    if not row:
        return None
    questions = row.get("questions", [])
    for q in questions:
        if q.get("id") == question_id:
            q["subject"] = new_subject
            q["lesson_confidence"] = 1.0
            q["lesson_reason"] = "Kullanıcı tarafından manuel düzeltildi."
            break
    resp = supabase.table("sgs_analyses").update({"questions": questions}).eq("id", analysis_id).execute()
    return resp.data[0] if resp.data else None

def parse_questions_by_ranges(
    analysis_id: str,
    range_ids: list[str] | None = None,
    document_id: str | None = None,
) -> dict:
    import logging
    from collections import Counter
    from app.config.sgs_groups import SGS_LESSON_GROUPS
    logger = logging.getLogger(__name__)

    supabase = get_supabase_client()
    effective_doc_id = document_id or analysis_id

    logger.info(f"[parse] analysis_id={analysis_id} document_id={effective_doc_id}")

    # 1. Analizi al
    resp = supabase.table("sgs_analyses").select("id,pdf_name,year,questions").eq("id", analysis_id).execute()
    if not resp.data:
        logger.warning(f"[parse] analiz bulunamadı: {analysis_id}")
        return {"error": f"Analiz bulunamadı (id={analysis_id[:8]}...). Önce PDF'i yükleyin."}
    a = resp.data[0]
    questions = a.get("questions") or []
    pdf_name = a.get("pdf_name", "")
    logger.info(f"[parse] analiz bulundu: pdf={pdf_name}, soru_sayısı={len(questions)}")

    if not questions:
        return {"error": f"'{pdf_name}' analizinde hiç soru yok. PDF yeniden analiz edilmeli."}

    # 2. Aralıkları al
    if range_ids:
        # Belirtilen range ID'leri doğrudan getir
        ranges_resp = supabase.table("sgs_question_ranges").select("*").in_("id", range_ids).execute()
        ranges = ranges_resp.data or []
        logger.info(f"[parse] range_ids ile {len(ranges)} aralık bulundu")
    else:
        # document_id ile ara
        ranges_resp = supabase.table("sgs_question_ranges").select("*").eq("document_id", effective_doc_id).execute()
        ranges = ranges_resp.data or []

        if not ranges and pdf_name:
            logger.info(f"[parse] document_id ile aralık bulunamadı, document_name ile deneniyor: {pdf_name}")
            ranges_resp2 = supabase.table("sgs_question_ranges").select("*").eq("document_name", pdf_name).execute()
            ranges = ranges_resp2.data or []
            if ranges:
                ids = [r["id"] for r in ranges]
                supabase.table("sgs_question_ranges").update({
                    "document_id": analysis_id
                }).in_("id", ids).execute()
                logger.info(f"[parse] {len(ranges)} aralık otomatik bağlandı (document_name eşleşmesi)")

    # 3. Soru numarasını normalize et
    def _get_q_no(q: dict) -> int | None:
        for key in ("id", "question_id", "no", "number", "soru_no"):
            val = q.get(key)
            if val is not None:
                try:
                    return int(val)
                except (ValueError, TypeError):
                    continue
        return None

    def get_group(lesson_name: str) -> str:
        for group, lessons in SGS_LESSON_GROUPS.items():
            if lesson_name in lessons:
                return group
        return "Genel"

    # 4. Aralık yoksa AI subject ile otomatik parse (upload anında data yazılsın)
    if not ranges:
        logger.info(f"[parse] aralık bulunamadı → AI subject kullanılıyor (otomatik parse): {pdf_name}")
        to_insert = []
        belirsiz_skipped = 0
        for q in questions:
            q_no = _get_q_no(q)
            if q_no is None:
                continue
            ai_subject = (q.get("subject") or "").strip()
            topic = q.get("topic") or ""
            if not ai_subject or ai_subject == "Belirsiz":
                # Konu üzerinden ders tespiti: Belirsiz sorularda topic map'e başvur
                resolved = _resolve_lesson_for_topic(topic, "")
                if not resolved:
                    belirsiz_skipped += 1
                    logger.debug(f"[parse] q#{q_no} Belirsiz+konu çözülmedi, atlanıyor (topic={topic!r})")
                    continue
                lesson = resolved
                logger.debug(f"[parse] q#{q_no} Belirsiz → topic={topic!r} → {lesson}")
            else:
                lesson = _resolve_lesson_for_topic(topic, ai_subject)
            to_insert.append({
                "document_id": analysis_id,
                "lesson_group": get_group(lesson),
                "lesson_name": lesson,
                "question_number": q_no,
                "year": a.get("year"),
                "topic": topic,
                "subtopic": q.get("subtopic"),
                "answer": q.get("answer"),
            })
        if belirsiz_skipped:
            logger.warning(f"[parse] {belirsiz_skipped} Belirsiz soru atlandı (topic map eşleşmesi yok): {pdf_name}")
        if not to_insert:
            return {"error": f"'{pdf_name}' analizinde sınıflandırılabilir soru yok. ({belirsiz_skipped} Belirsiz atlandı)"}
        supabase.table("sgs_questions").delete().eq("document_id", analysis_id).execute()
        insert_resp = supabase.table("sgs_questions").insert(to_insert).execute()
        inserted = len(insert_resp.data or [])
        if inserted < len(to_insert):
            logger.warning(f"[parse] INSERT eksik: beklenen={len(to_insert)}, yazılan={inserted}, pdf={pdf_name}")
        lesson_counts = Counter(q["lesson_name"] for q in to_insert)
        logger.info(f"[parse] otomatik parse: {inserted}/{len(questions)} soru yazıldı, belirsiz_atlandı={belirsiz_skipped}, pdf={pdf_name}")
        return {
            "questions_created": inserted,
            "failed_count": belirsiz_skipped,
            "belirsiz_skipped": belirsiz_skipped,
            "lessons": [{"lesson_name": k, "count": v} for k, v in lesson_counts.items()],
            "analysis_id": analysis_id,
        }

    logger.info(f"[parse] {len(ranges)} aralık bulundu")

    # 5. Aralıklarla eşleştir
    to_insert = []
    unmatched = []
    for q in questions:
        q_no = _get_q_no(q)
        if q_no is None:
            continue
        matched = False
        for r in ranges:
            if r["start_question_no"] <= q_no <= r["end_question_no"]:
                range_lesson = r["lesson_name"]
                topic = q.get("topic") or ""
                lesson = _resolve_lesson_for_topic(topic, range_lesson)
                to_insert.append({
                    "document_id": analysis_id,
                    "lesson_group": get_group(lesson),
                    "lesson_name": lesson,
                    "question_number": q_no,
                    "year": a.get("year"),
                    "topic": topic,
                    "subtopic": q.get("subtopic"),
                    "answer": q.get("answer"),
                })
                matched = True
                break
        if not matched:
            unmatched.append(q_no)

    logger.info(f"[parse] eşleşen={len(to_insert)}, eşleşmeyen={len(unmatched)}")

    if not to_insert:
        range_summary = [(r["start_question_no"], r["end_question_no"]) for r in ranges[:3]]
        sample_nos = [_get_q_no(q) for q in questions[:5] if _get_q_no(q)]
        logger.warning(f"[parse] soru eşleşmedi. örnek_no={sample_nos}, aralıklar={range_summary}")
        return {
            "error": (
                f"Hiç soru eşleşmedi. "
                f"Analizdeki ilk soru numaraları: {sample_nos}. "
                f"Tanımlı aralıklar (ilk 3): {range_summary}. "
                f"Soru numaraları aralıklarla örtüşmüyor — aralık başlangıç/bitiş numaralarını kontrol edin."
            )
        }

    # 5. Kaydet
    supabase.table("sgs_questions").delete().eq("document_id", analysis_id).execute()
    insert_resp = supabase.table("sgs_questions").insert(to_insert).execute()
    inserted = len(insert_resp.data or [])
    if inserted < len(to_insert):
        logger.warning(f"[parse] INSERT eksik: beklenen={len(to_insert)}, yazılan={inserted}, pdf={pdf_name}")

    lesson_counts = Counter(q["lesson_name"] for q in to_insert)
    logger.info(
        f"[parse] {inserted}/{len(questions)} soru kaydedildi, "
        f"eşleşmeyen={len(unmatched)}, pdf={pdf_name}, dersler={dict(lesson_counts)}"
    )

    return {
        "questions_created": inserted,
        "failed_count": len(unmatched),
        "unmatched_question_nos": unmatched[:20],  # ilk 20 — debug için
        "lessons": [{"lesson_name": k, "count": v} for k, v in lesson_counts.items()],
        "analysis_id": analysis_id,
    }


def get_areas_from_sgs_questions(year: str | None = None) -> list[dict]:
    """Alan bazlı soru özeti — sgs_questions tablosu birincil kaynak.
    sgs_questions tamamen boşsa eski get_areas_summary'ye döner.
    Kısmen dolu tabloda parse edilmemiş dersler 0 gösterir (doğru davranış).
    """
    from app.config.sgs_groups import SGS_LESSON_GROUPS
    from collections import Counter
    supabase = get_supabase_client()

    # Supabase default 1000 satır sınırı — büyük tablolarda kesilebilir.
    # limit(50000) ile tüm satırları al.
    query = supabase.table("sgs_questions").select("lesson_name", count="exact").limit(50000)
    if year:
        query = query.eq("year", year)
    resp = query.execute()
    total_count = resp.count or 0

    if total_count == 0:
        return get_areas_summary(year=year)

    rows = resp.data or []
    lesson_counts = Counter(r["lesson_name"] for r in rows)
    areas = []
    for area, lessons in SGS_LESSON_GROUPS.items():
        area_total = 0
        lessons_data = []
        for lesson in lessons:
            found = lesson_counts.get(lesson, 0)
            area_total += found
            lessons_data.append({
                "name": lesson,
                "expected": found,
                "found": found,
                "range_count": 0,
                "status": "ready" if found > 0 else "no_questions",
            })
        areas.append({
            "name": area,
            "expected_total": area_total,
            "found_total": area_total,
            "discrepancy": 0,
            "status": "ok" if area_total > 0 else "missing",
            "lessons": lessons_data,
        })
    return areas


def get_lesson_topics_from_sgs_questions(lesson_name: str, year: str | None = None) -> dict:
    """Ders bazlı konu analizi — sgs_questions tablosu tek kaynak.
    Tablo boşsa eski range/AI fallback'e dön (backward compat).
    """
    from collections import Counter
    supabase = get_supabase_client()

    query = supabase.table("sgs_questions").select("topic, year").eq("lesson_name", lesson_name).limit(50000)
    if year:
        query = query.eq("year", year)
    resp = query.execute()
    rows = resp.data or []

    if not rows:
        questions = get_questions_by_ranges(lesson_name=lesson_name, year=year)
        data_source = "ranges"
        if not questions:
            questions = get_all_questions(lesson_name=lesson_name, year=year)
            data_source = "ai"
        topic_counts = Counter(q.get("topic", "Belirsiz") for q in questions)
        year_counts = Counter(q.get("source_year") or q.get("year", "?") for q in questions)
        return {
            "lesson": lesson_name,
            "total": len(questions),
            "top_topics": [{"topic": t, "count": c} for t, c in topic_counts.most_common(20)],
            "year_breakdown": [{"year": y, "count": c} for y, c in sorted(year_counts.items())],
            "data_source": data_source,
        }

    topic_counts = Counter(r.get("topic") or "Belirsiz" for r in rows)
    year_counts = Counter(r.get("year") or "?" for r in rows)
    return {
        "lesson": lesson_name,
        "total": len(rows),
        "top_topics": [{"topic": t, "count": c} for t, c in topic_counts.most_common(20)],
        "year_breakdown": [{"year": y, "count": c} for y, c in sorted(year_counts.items())],
        "data_source": "questions_table",
    }


def reclassify_all_questions() -> dict:
    """sgs_questions tablosundaki tüm sorulara _TOPIC_LESSON_MAP uygula.
    Yanlış ders atamalı satırları bulk update eder ve rapor döner.
    """
    import logging as _logging
    from app.config.sgs_groups import get_group_for_lesson
    _log = _logging.getLogger(__name__)
    supabase = get_supabase_client()

    resp = supabase.table("sgs_questions").select("id, lesson_name, topic").limit(50000).execute()
    rows = resp.data or []

    # (topic_lower, current_lesson) → {topic, from, to, ids}
    moves: dict[tuple, dict] = {}
    for row in rows:
        topic = (row.get("topic") or "").strip()
        current_lesson = row.get("lesson_name", "")
        # _resolve_lesson_for_topic: exact match + substring match (tutarlı parse ile)
        correct_lesson = _resolve_lesson_for_topic(topic, current_lesson)
        if correct_lesson != current_lesson:
            key = (topic.lower(), current_lesson)
            if key not in moves:
                moves[key] = {"topic": topic, "from": current_lesson, "to": correct_lesson, "ids": []}
            moves[key]["ids"].append(row["id"])

    updated_total = 0
    moved_summary = []
    for move in moves.values():
        correct_lesson = move["to"]
        group = get_group_for_lesson(correct_lesson) or "Genel Dersler"
        ids = move["ids"]
        supabase.table("sgs_questions").update({
            "lesson_name": correct_lesson,
            "lesson_group": group,
        }).in_("id", ids).execute()
        updated_total += len(ids)
        moved_summary.append({"topic": move["topic"], "from": move["from"], "to": correct_lesson, "count": len(ids)})
        _log.info(f"[reclassify] {move['topic']!r}: {move['from']} → {correct_lesson} ({len(ids)} soru)")

    return {
        "success": True,
        "total_rows": len(rows),
        "updated": updated_total,
        "moved": sorted(moved_summary, key=lambda x: x["count"], reverse=True),
    }


def get_questions_for_topic(topic: str, lesson_name: str | None = None, limit: int = 30) -> list[dict]:
    """sgs_questions tablosundan konu/ders bazlı sorular — tam soru detayı ile."""
    supabase = get_supabase_client()

    # sgs_questions tablosundan eşleşen satırları al
    query = supabase.table("sgs_questions").select("*")
    if topic:
        query = query.eq("topic", topic)
    if lesson_name:
        query = query.eq("lesson_name", lesson_name)
    resp = query.limit(limit).execute()
    rows = resp.data or []

    if not rows:
        # sgs_questions boşsa sgs_analyses.questions JSONB'den dene (AI tabanlı)
        all_q = get_all_questions(lesson_name=lesson_name)
        return [q for q in all_q if q.get("topic", "") == topic][:limit]

    # Benzersiz analysis ID'leri topla ve analizleri çek
    analysis_ids = list({r["document_id"] for r in rows if r.get("document_id")})
    if not analysis_ids:
        return []

    analyses_resp = supabase.table("sgs_analyses").select("id,pdf_name,year,questions").in_("id", analysis_ids).execute()

    # analysis_id → {question_number: full_question_dict}
    lookup: dict[str, tuple[dict, str, str]] = {}
    for a in (analyses_resp.data or []):
        q_map: dict[int, dict] = {}
        for q in (a.get("questions") or []):
            q_no = q.get("id") or q.get("question_id") or q.get("no")
            if q_no is not None:
                q_map[int(q_no)] = q
        lookup[a["id"]] = (q_map, a.get("pdf_name", ""), a.get("year", ""))

    result = []
    for row in rows:
        doc_id = row.get("document_id")
        q_no = row.get("question_number")
        if not doc_id or q_no is None:
            continue
        q_map, pdf_name, year = lookup.get(doc_id, ({}, "", ""))
        q_data = q_map.get(int(q_no), {})

        result.append({
            **q_data,
            "id": q_no,
            "subject": row["lesson_name"],       # aralıktan gelen doğru ders
            "topic": row["topic"] or q_data.get("topic", ""),
            "year": row.get("year") or year or q_data.get("year", ""),
            "document_name": pdf_name,
        })

    return result


def update_question_in_sgs_questions(question_number: int, lesson_name: str | None = None, topic: str | None = None) -> bool:
    """sgs_questions tablosunda question_number bazlı ders/konu düzeltmesi."""
    from app.config.sgs_groups import get_group_for_lesson
    supabase = get_supabase_client()

    updates: dict = {}
    if lesson_name:
        updates["lesson_name"] = lesson_name
        group = get_group_for_lesson(lesson_name)
        if group:
            updates["lesson_group"] = group
    if topic:
        updates["topic"] = topic

    if not updates:
        return False

    resp = supabase.table("sgs_questions").update(updates).eq("question_number", question_number).execute()
    return bool(resp.data)


def get_topic_detail(topic: str, lesson_name: str | None = None) -> dict:
    """Bir konu için toplam soru, yıl dağılımı, ders dağılımı ve çıkma oranı.
    sgs_questions tablosu tek kaynak; tablo boşsa eski yola dön.
    """
    from collections import Counter as _Counter
    supabase = get_supabase_client()

    # 1. sgs_questions tablosundan konu sorularını al
    q_query = supabase.table("sgs_questions").select("lesson_name, year, topic").eq("topic", topic)
    if lesson_name:
        q_query = q_query.eq("lesson_name", lesson_name)
    q_resp = q_query.execute()
    topic_rows = q_resp.data or []

    if not topic_rows:
        # Fallback: eski yol (sgs_analyses JSONB)
        q_ranges = get_questions_by_ranges(lesson_name=lesson_name)
        topic_questions = [q for q in q_ranges if q.get("topic", "") == topic]
        if not topic_questions:
            q_all = get_all_questions(lesson_name=lesson_name)
            topic_questions = [q for q in q_all if q.get("topic", "") == topic]
        total = len(topic_questions)
        year_counter = _Counter(q.get("source_year") or q.get("year", "?") for q in topic_questions)
        lesson_counter = _Counter(q.get("subject", "Belirsiz") for q in topic_questions)
        if lesson_name:
            all_lesson_q = get_questions_by_ranges(lesson_name=lesson_name) or get_all_questions(lesson_name=lesson_name)
            lesson_total = len(all_lesson_q)
        else:
            lesson_total = total
    else:
        total = len(topic_rows)
        year_counter = _Counter(r.get("year") or "?" for r in topic_rows)
        lesson_counter = _Counter(r.get("lesson_name") or "Belirsiz" for r in topic_rows)

        # Frekans payda: bu dersin toplam soru sayısı
        if lesson_name:
            denom_resp = supabase.table("sgs_questions").select("id", count="exact").eq("lesson_name", lesson_name).execute()
            lesson_total = denom_resp.count or 0
        else:
            lesson_total = total

    frequency_pct = round((total / lesson_total * 100), 1) if lesson_total > 0 else 0.0

    return {
        "topic": topic,
        "total_questions": total,
        "lessons": [{"lesson_name": l, "count": c} for l, c in lesson_counter.most_common()],
        "years": [{"year": y, "count": c} for y, c in sorted(year_counter.items())],
        "frequency_pct": frequency_pct,
    }


def parse_all_unparsed_analyses() -> dict:
    """Tüm analizleri kontrol eder; hiç parse edilmemiş veya kısmen parse edilmiş
    olanları AI subject ile otomatik parse eder.

    Eski davranış (herhangi 1 satır varsa atla) yerine count-based kontrol:
    sgs_questions'taki satır sayısı < sgs_analyses.questions sayısı ise yeniden parse et.
    """
    import logging as _logging
    _log = _logging.getLogger(__name__)
    supabase = get_supabase_client()

    analyses_resp = supabase.table("sgs_analyses").select("id, pdf_name, year, questions").execute()
    analyses = analyses_resp.data or []

    # Satır limiti: Supabase default 1000 satır — büyük tablolarda kesilebilir.
    # .limit(50000) ile güvenli bölgeye çık.
    sq_resp = supabase.table("sgs_questions").select("document_id").limit(50000).execute()
    parsed_counts: dict[str, int] = {}
    for r in (sq_resp.data or []):
        did = r.get("document_id")
        if did:
            parsed_counts[did] = parsed_counts.get(did, 0) + 1

    total_created = 0
    skipped = 0
    results = []
    errors = []

    for a in analyses:
        aid = a["id"]
        expected = len(a.get("questions") or [])
        already = parsed_counts.get(aid, 0)

        if expected > 0 and already >= expected:
            # Tüm sorular parse edilmiş — atla
            skipped += 1
            _log.debug(f"[parse-all] atlandı (tam parse): {a.get('pdf_name')} ({already}/{expected})")
            continue

        result = parse_questions_by_ranges(analysis_id=aid)
        created = result.get("questions_created", 0)
        total_created += created

        entry = {
            "pdf": a.get("pdf_name", aid),
            "created": created,
            "expected": expected,
            "was_partial": already > 0,
        }
        if result.get("error"):
            entry["error"] = result["error"]
            errors.append(entry)
        results.append(entry)
        _log.info(f"[parse-all] {a.get('pdf_name')}: {created}/{expected} soru yazıldı (önceden={already})")

    return {
        "total_created": total_created,
        "total_analyses": len(analyses),
        "processed": len(results),
        "skipped": skipped,
        "errors": errors,
        "analyses": results,
    }

