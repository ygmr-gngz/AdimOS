from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from app.core.config import settings

_options = ClientOptions(postgrest_client_timeout=30)

_client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY,
    options=_options,
)

def get_supabase_client() -> Client:
    return _client
