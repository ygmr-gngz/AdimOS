"""SGS analizleri için Supabase repo."""
from app.db.supabase import get_supabase_client


def create_analysis(pdf_name: str, total_questions: int,
                    subjects: list, questions: list, video_plan: list) -> dict | None:
    supabase = get_supabase_client()
    resp = supabase.table("sgs_analyses").insert({
        "pdf_name": pdf_name,
        "total_questions": total_questions,
        "subjects": subjects,
        "questions": questions,
        "video_plan": video_plan,
        "status": "completed",
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
