"""Meta Graph endpoint seçimi.

Instagram Login tokenları (IGAA…) graph.instagram.com, eski Facebook
Login/Page tokenları (EAA…) graph.facebook.com üzerinden çalışır.
"""
from app.core.config import settings


def graph_base(token: str) -> str:
    host = "graph.instagram.com" if token.startswith("IG") else "graph.facebook.com"
    return f"https://{host}/{settings.META_GRAPH_API_VERSION}"


def refresh_url(token: str) -> str:
    if token.startswith("IG"):
        return "https://graph.instagram.com/refresh_access_token"
    # Geriye dönük davranış: mevcut Page-token akışının endpointini koru.
    return f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION}/refresh_access_token"
