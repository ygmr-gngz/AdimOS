import secrets
import string
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.auth import require_admin, get_current_user
from app.db.supabase import get_supabase_client
from app.db.repositories.audit_repo import log_action

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateUserRequest(BaseModel):
    email: str
    display_name: str
    role: str = "editor"
    temporary_password: str | None = None


class UpdateRoleRequest(BaseModel):
    role: str


def _temp_password() -> str:
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(chars) for _ in range(12))


@router.get("")
def list_users(user_data=Depends(require_admin)):
    supabase = get_supabase_client()
    try:
        resp = supabase.table("user_profiles").select("*").order("created_at", desc=True).execute()
        return {"users": resp.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
def create_user(request: CreateUserRequest, user_data=Depends(require_admin)):
    if request.role not in ("admin", "editor"):
        raise HTTPException(status_code=400, detail="Rol 'admin' veya 'editor' olmalı")
    supabase = get_supabase_client()
    temp_pass = request.temporary_password or _temp_password()
    try:
        auth_resp = supabase.auth.admin.create_user({
            "email": request.email,
            "password": temp_pass,
            "email_confirm": True,
        })
        new_user = auth_resp.user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Kullanıcı oluşturulamadı: {e}")
    try:
        supabase.table("user_profiles").insert({
            "user_id": new_user.id,
            "display_name": request.display_name,
            "role": request.role,
            "force_password_change": True,
            "is_active": True,
        }).execute()
    except Exception as e:
        logger.error(f"[users] profil oluşturulamadı: {e}")
    log_action(
        user_id=user_data["user"].id,
        user_email=user_data["user"].email,
        action="user.create",
        resource=request.email,
        details={"role": request.role, "display_name": request.display_name},
    )
    return {"user_id": new_user.id, "email": request.email, "role": request.role, "temporary_password": temp_pass}


@router.put("/{user_id}/role")
def update_role(user_id: str, request: UpdateRoleRequest, user_data=Depends(require_admin)):
    if request.role not in ("admin", "editor"):
        raise HTTPException(status_code=400, detail="Geçersiz rol")
    supabase = get_supabase_client()
    supabase.table("user_profiles").update({"role": request.role}).eq("user_id", user_id).execute()
    log_action(
        user_id=user_data["user"].id,
        user_email=user_data["user"].email,
        action="user.role_change",
        resource=user_id,
        details={"new_role": request.role},
    )
    return {"ok": True}


@router.delete("/{user_id}")
def deactivate_user(user_id: str, user_data=Depends(require_admin)):
    supabase = get_supabase_client()
    supabase.table("user_profiles").update({"is_active": False}).eq("user_id", user_id).execute()
    log_action(user_id=user_data["user"].id, user_email=user_data["user"].email, action="user.deactivate", resource=user_id)
    return {"ok": True}


@router.post("/me/change-password")
def change_password(body: dict, user=Depends(get_current_user)):
    new_password = body.get("new_password", "")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Şifre en az 8 karakter olmalı")
    supabase = get_supabase_client()
    try:
        supabase.auth.admin.update_user_by_id(user.id, {"password": new_password})
        supabase.table("user_profiles").update({"force_password_change": False}).eq("user_id", user.id).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    log_action(user_id=user.id, user_email=user.email, action="auth.password_change")
    return {"ok": True}


@router.get("/me")
def get_me(user=Depends(get_current_user)):
    supabase = get_supabase_client()
    try:
        profile = supabase.table("user_profiles").select("*").eq("user_id", user.id).single().execute()
        role = profile.data.get("role", "editor") if profile.data else "admin"
        force_change = profile.data.get("force_password_change", False) if profile.data else False
        display_name = profile.data.get("display_name") if profile.data else None
    except Exception:
        role = "editor"
        force_change = False
        display_name = None
    return {
        "id": user.id,
        "email": user.email,
        "display_name": display_name,
        "role": role,
        "force_password_change": force_change,
    }
