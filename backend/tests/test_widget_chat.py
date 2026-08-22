import gzip
from pathlib import Path

from app.api.routes.widget_chat import _filter_answer


def test_forbidden_marketing_phrase_is_blocked() -> None:
    answer = _filter_answer("Size en ucuz muhasebe hizmetini veriyoruz")
    assert "en ucuz" not in answer.casefold()
    assert "genel bilgilendirme" in answer


def test_widget_bundle_is_under_40kb_gzip() -> None:
    bundle = Path(__file__).parents[1] / "app" / "static" / "widget" / "chat.js"
    assert bundle.exists()
    assert len(gzip.compress(bundle.read_bytes())) < 40 * 1024
    source = bundle.read_text(encoding="utf-8")
    assert "attachShadow" in source
