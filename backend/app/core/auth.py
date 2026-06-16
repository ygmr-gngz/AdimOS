from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.supabase import get_supabase_client
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Giriş gerekli")
    token = credentials.credentials
    supabase = get_supabase_client()
    try:
        resp = supabase.auth.get_user(token)
        user = resp.user
        if not user:
            raise HTTPException(status_code=401, detail="Geçersiz token")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"[auth] token doğrulanamadı: {e}")
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş token")


def get_user_with_role(user=Depends(get_current_user)):
    supabase = get_supabase_client()
    try:
        profile = (
            supabase.table("user_profiles")
            .select("role, is_active, display_name")
            .eq("user_id", user.id)
            .single()
            .execute()
        )
        if profile.data:
            if not profile.data.get("is_active", True):
                raise HTTPException(status_code=403, detail="Hesabınız devre dışı")
            role = profile.data.get("role", "editor")
        else:
            role = "admin"
    except HTTPException:
        raise
    except Exception:
        role = "editor"
    return {"user": user, "role": role}


def require_admin(user_data=Depends(get_user_with_role)):
    if user_data["role"] != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekli")
    return user_data
