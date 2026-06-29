"""SGS analizleri için Supabase repo."""
import re
import unicodedata
from difflib import SequenceMatcher
from app.db.supabase import get_supabase_client


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
        .select("id, pdf_name, total_questions, subjects, video_plan, status, created_at")
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

    print(f"[parse_repo] analysis_id={analysis_id}, document_id={effective_doc_id}, range_ids={range_ids}")
    logger.info(f"[parse] analysis_id={analysis_id} document_id={effective_doc_id}")

    # 1. Analizi al
    resp = supabase.table("sgs_analyses").select("id,pdf_name,year,questions").eq("id", analysis_id).execute()
    if not resp.data:
        logger.warning(f"[parse] analiz bulunamadı: {analysis_id}")
        return {"error": f"Analiz bulunamadı (id={analysis_id[:8]}...). Önce PDF'i yükleyin."}
    a = resp.data[0]
    questions = a.get("questions") or []
    pdf_name = a.get("pdf_name", "")
    print(f"[parse_repo] analiz bulundu: pdf={pdf_name!r}, toplam_soru={len(questions)}")
    logger.info(f"[parse] analiz bulundu: pdf={pdf_name}, soru_sayısı={len(questions)}")

    if not questions:
        return {"error": f"'{pdf_name}' analizinde hiç soru yok. PDF yeniden analiz edilmeli."}

    # 2. Aralıkları al
    if range_ids:
        # Belirtilen range ID'leri doğrudan getir
        ranges_resp = supabase.table("sgs_question_ranges").select("*").in_("id", range_ids).execute()
        ranges = ranges_resp.data or []
        print(f"[parse_repo] range_ids ile {len(ranges)} aralık bulundu (istenen: {len(range_ids)})")
        logger.info(f"[parse] range_ids ile {len(ranges)} aralık bulundu")
    else:
        # document_id ile ara
        ranges_resp = supabase.table("sgs_question_ranges").select("*").eq("document_id", effective_doc_id).execute()
        ranges = ranges_resp.data or []
        print(f"[parse_repo] document_id={effective_doc_id!r} ile {len(ranges)} aralık bulundu")

        if not ranges and pdf_name:
            logger.info(f"[parse] document_id ile aralık bulunamadı, document_name ile deneniyor: {pdf_name}")
            print(f"[parse_repo] document_name={pdf_name!r} ile fallback arama...")
            ranges_resp2 = supabase.table("sgs_question_ranges").select("*").eq("document_name", pdf_name).execute()
            ranges = ranges_resp2.data or []
            # Bulunan aralıkların document_id'sini güncelle
            if ranges:
                ids = [r["id"] for r in ranges]
                for rid in ids:
                    supabase.table("sgs_question_ranges").update({
                        "document_id": analysis_id
                    }).eq("id", rid).execute()
                print(f"[parse_repo] {len(ranges)} aralık document_name eşleşmesiyle otomatik bağlandı")
                logger.info(f"[parse] {len(ranges)} aralık otomatik bağlandı (document_name eşleşmesi)")

    if not ranges:
        total_resp = supabase.table("sgs_question_ranges").select("id,document_id,document_name", count="exact").execute()
        total_count = total_resp.count or 0
        sample = [(r.get("document_name"), r.get("document_id")) for r in (total_resp.data or [])[:3]]
        print(f"[parse_repo] HATA: hiç aralık bulunamadı. Toplam: {total_count}, örnek kayıtlar: {sample}")
        logger.warning(f"[parse] hiç aralık bulunamadı. Toplam aralık sayısı: {total_count}")
        return {
            "error": (
                f"'{pdf_name}' PDF'ine bağlı aralık bulunamadı. "
                f"Veritabanında toplam {total_count} aralık var. "
                f"'Soru Aralıkları' bölümünde '{pdf_name}' PDF'ini seçip 'Aralıkları PDF'e Bağla' yapın."
            )
        }

    range_summary = [(r["lesson_name"], r["start_question_no"], r["end_question_no"], r.get("document_id")) for r in ranges]
    print(f"[parse_repo] {len(ranges)} aralık bulundu: {range_summary}")
    logger.info(f"[parse] {len(ranges)} aralık bulundu")

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

    # 4. Eşleştir
    to_insert = []
    unmatched = []
    for q in questions:
        q_no = _get_q_no(q)
        if q_no is None:
            continue
        matched = False
        for r in ranges:
            if r["start_question_no"] <= q_no <= r["end_question_no"]:
                lesson = r["lesson_name"]
                to_insert.append({
                    "document_id": analysis_id,
                    "lesson_group": get_group(lesson),
                    "lesson_name": lesson,
                    "question_number": q_no,
                    "year": a.get("year"),
                    "topic": q.get("subject") or q.get("topic"),
                    "subtopic": q.get("subtopic"),
                    "answer": q.get("answer"),
                })
                matched = True
                break
        if not matched:
            unmatched.append(q_no)

    print(f"[parse_repo] eşleşen={len(to_insert)}, eşleşmeyen={len(unmatched)}, örnek eşleşmeyenler={unmatched[:10]}")
    logger.info(f"[parse] eşleşen={len(to_insert)}, eşleşmeyen={len(unmatched)}, ilk 5 eşleşmeyen={unmatched[:5]}")

    if not to_insert:
        range_summary = [(r["start_question_no"], r["end_question_no"]) for r in ranges[:3]]
        sample_nos = [_get_q_no(q) for q in questions[:5] if _get_q_no(q)]
        print(f"[parse_repo] HATA: Soru eşleşmedi. sample_nos={sample_nos}, aralıklar={range_summary}")
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
    supabase.table("sgs_questions").insert(to_insert).execute()

    lesson_counts = Counter(q["lesson_name"] for q in to_insert)
    print(f"[parse_repo] BAŞARI: {len(to_insert)} soru kaydedildi, failed={len(unmatched)}, dersler={dict(lesson_counts)}")
    logger.info(f"[parse] {len(to_insert)} soru kaydedildi: {dict(lesson_counts)}")

    return {
        "questions_created": len(to_insert),
        "failed_count": len(unmatched),
        "lessons": [{"lesson_name": k, "count": v} for k, v in lesson_counts.items()],
        "analysis_id": analysis_id,
    }

