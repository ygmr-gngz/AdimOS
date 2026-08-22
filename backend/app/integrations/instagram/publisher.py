from app.integrations.instagram.client import InstagramClient


def publish_queue_item(row: dict) -> str:
    client = InstagramClient()
    assets = row["asset_urls"]
    package = row.get("publish_package") or {}
    caption = str(package.get("caption") or package.get("description") or "")
    if row["content_type"] == "video":
        creation = client.create_media({"media_type": "REELS", "video_url": assets[0], "caption": caption})
        client.wait_finished(creation)
        return client.publish(creation)
    if row["content_type"] == "single_image":
        creation = client.create_media({"image_url": assets[0], "caption": caption})
        return client.publish(creation)
    children = [client.create_media({"image_url": url, "is_carousel_item": "true"}) for url in assets]
    parent = client.create_media({"media_type": "CAROUSEL", "children": ",".join(children), "caption": caption})
    return client.publish(parent)
