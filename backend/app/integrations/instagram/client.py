import time
import requests
from app.core.config import settings

GRAPH = "https://graph.facebook.com/v21.0"


class InstagramClient:
    def __init__(self, token: str | None = None, business_id: str | None = None):
        self.token = token or settings.INSTAGRAM_ACCESS_TOKEN or settings.META_ACCESS_TOKEN
        self.business_id = business_id or settings.INSTAGRAM_BUSINESS_ID or settings.INSTAGRAM_BUSINESS_ACCOUNT_ID
        if not self.token or not self.business_id:
            raise RuntimeError("instagram_credentials_missing")

    def post(self, path: str, data: dict) -> dict:
        response = requests.post(f"{GRAPH}/{path}", data={**data, "access_token": self.token}, timeout=30)
        payload = response.json()
        if not response.ok or payload.get("error"):
            raise RuntimeError(f"instagram_api_error: {payload.get('error', payload)}")
        return payload

    def get(self, path: str, params: dict | None = None) -> dict:
        response = requests.get(f"{GRAPH}/{path}", params={**(params or {}), "access_token": self.token}, timeout=30)
        payload = response.json()
        if not response.ok or payload.get("error"):
            raise RuntimeError(f"instagram_api_error: {payload.get('error', payload)}")
        return payload

    def create_media(self, data: dict) -> str:
        return str(self.post(f"{self.business_id}/media", data)["id"])

    def wait_finished(self, creation_id: str, timeout_seconds: int = 300) -> None:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            status = self.get(creation_id, {"fields": "status_code"}).get("status_code")
            if status == "FINISHED": return
            if status in ("ERROR", "EXPIRED"): raise RuntimeError(f"instagram_container_{status.lower()}")
            time.sleep(5)
        raise RuntimeError("instagram_container_timeout")

    def publish(self, creation_id: str) -> str:
        return str(self.post(f"{self.business_id}/media_publish", {"creation_id": creation_id})["id"])


def refresh_long_lived_token(token: str | None = None) -> dict:
    current = token or settings.INSTAGRAM_ACCESS_TOKEN or settings.META_ACCESS_TOKEN
    if not current:
        raise RuntimeError("instagram_access_token_missing")
    response = requests.get(
        f"{GRAPH}/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": current}, timeout=30,
    )
    payload = response.json()
    if not response.ok or payload.get("error"):
        raise RuntimeError(f"instagram_token_refresh_failed: {payload}")
    return payload
