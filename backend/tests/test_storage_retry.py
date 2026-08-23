from unittest.mock import Mock, patch

from app.modules.content.storage import upload_bytes


def test_upload_bytes_retries_transient_storage3_unbound_response() -> None:
    storage = Mock()
    storage.upload.side_effect = [
        UnboundLocalError("cannot access local variable 'response'"),
        None,
    ]
    storage.get_public_url.return_value = "https://cdn.test/card.png"
    supabase = Mock()
    supabase.storage.from_.return_value = storage

    with patch("app.modules.content.storage.ensure_bucket"), patch(
        "app.modules.content.storage.get_supabase_client", return_value=supabase
    ), patch("app.modules.content.storage.time.sleep"):
        url = upload_bytes(b"png", "content-videos", "carousel/job/card.png", "image/png")

    assert url == "https://cdn.test/card.png"
    assert storage.upload.call_count == 2


def test_upload_bytes_reports_stage_after_three_failures() -> None:
    storage = Mock()
    storage.upload.side_effect = UnboundLocalError("response")
    supabase = Mock()
    supabase.storage.from_.return_value = storage

    with patch("app.modules.content.storage.ensure_bucket"), patch(
        "app.modules.content.storage.get_supabase_client", return_value=supabase
    ), patch("app.modules.content.storage.time.sleep"):
        try:
            upload_bytes(b"png", "content-videos", "carousel/job/card.png", "image/png")
        except RuntimeError as exc:
            assert "storage_upload_failed" in str(exc)
        else:
            raise AssertionError("Üç başarısız denemeden sonra hata bekleniyordu")
