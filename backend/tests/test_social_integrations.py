from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from app.integrations.instagram.messenger import within_reply_window
from app.integrations.instagram.publisher import publish_queue_item


def test_instagram_carousel_three_step_flow() -> None:
    client = Mock()
    client.create_media.side_effect = ["child1", "child2", "parent"]
    client.publish.return_value = "post123"
    with patch("app.integrations.instagram.publisher.InstagramClient", return_value=client):
        result = publish_queue_item({
            "content_type": "carousel",
            "asset_urls": ["https://cdn/1.png", "https://cdn/2.png"],
            "publish_package": {"caption": "SGS özeti"},
        })
    assert result == "post123"
    assert client.create_media.call_count == 3
    assert client.publish.call_count == 1


def test_instagram_reels_waits_before_publish() -> None:
    client = Mock()
    client.create_media.return_value = "creation1"
    client.publish.return_value = "reel1"
    with patch("app.integrations.instagram.publisher.InstagramClient", return_value=client):
        assert publish_queue_item({"content_type": "video", "asset_urls": ["https://cdn/video.mp4"], "publish_package": {}}) == "reel1"
    client.wait_finished.assert_called_once_with("creation1")


def test_dm_reply_window_is_24_hours() -> None:
    now = datetime(2026, 8, 22, 12, tzinfo=timezone.utc)
    assert within_reply_window(now - timedelta(hours=23, minutes=59), now)
    assert not within_reply_window(now - timedelta(hours=24, seconds=1), now)
