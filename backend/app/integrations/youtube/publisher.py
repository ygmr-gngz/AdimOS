from app.integrations.youtube.client import upload_to_youtube
from app.integrations.youtube.quota import ensure_upload_quota


def publish_queue_item(row: dict) -> str:
    ensure_upload_quota()
    package = row.get("publish_package") or {}
    title = str(package.get("title") or "Adım Müşavir SGS Eğitimi")[:100]
    description = str(package.get("description") or "")
    if "#Shorts" not in description:
        description = f"{description}\n\n#Shorts".strip()
    hashtags = package.get("hashtags") or []
    tags = [str(tag).lstrip("#") for tag in hashtags]
    result = upload_to_youtube(row["asset_urls"][0], title, description, tags, privacy="public")
    return str(result["video_id"])
