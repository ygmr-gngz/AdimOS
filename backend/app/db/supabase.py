from supabase import create_client, Client
from app.core.config import settings

_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

def get_supabase_client() -> Client:
    return _client
