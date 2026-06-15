from app.db.supabase import get_supabase_client


def create_student(name: str, surname: str, email: str, phone: str, status: str) -> dict | None:
    supabase = get_supabase_client()
    response = supabase.table("students").insert({
        "name": name,
        "surname": surname,
        "email": email,
        "phone": phone,
        "status": status,
    }).execute()
    return response.data[0] if response.data else None


def get_students() -> list[dict]:
    supabase = get_supabase_client()
    response = (
        supabase.table("students")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data if response.data else []


def get_student(student_id: str) -> dict | None:
    supabase = get_supabase_client()
    response = supabase.table("students").select("*").eq("id", student_id).execute()
    return response.data[0] if response.data else None


def update_student(student_id: str, updates: dict) -> dict | None:
    supabase = get_supabase_client()
    response = supabase.table("students").update(updates).eq("id", student_id).execute()
    return response.data[0] if response.data else None


def delete_student(student_id: str) -> list[dict]:
    supabase = get_supabase_client()
    response = supabase.table("students").delete().eq("id", student_id).execute()
    return response.data if response.data else []


def create_exam_attempt(student_id: str, exam_name: str, score: float) -> dict | None:
    supabase = get_supabase_client()
    response = supabase.table("exam_attempts").insert({
        "student_id": student_id,
        "exam_name": exam_name,
        "score": score,
    }).execute()
    return response.data[0] if response.data else None


def get_exam_attempts(student_id: str) -> list[dict]:
    supabase = get_supabase_client()
    response = (
        supabase.table("exam_attempts")
        .select("*")
        .eq("student_id", student_id)
        .order("attempt_date", desc=True)
        .execute()
    )
    return response.data if response.data else []
