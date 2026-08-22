import base64
import io
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image

from app.modules.content.illustrated_carousel import (
    CAROUSEL_MODES,
    generate_carousel_plan,
    generate_carousel_pngs,
    validate_carousel_plan,
)


def _plan() -> dict:
    kinds = [
        "hook", "overview", "worked_example", "account_application",
        "common_mistake", "exam_tip",
    ]
    return {
        "topic": "Safha Maliyeti",
        "cards": [
            {"kind": kind, "title": f"Kart {index}", "subtitle": "Kısa açıklama", "bullets": ["Kısa bilgi"]}
            for index, kind in enumerate(kinds, 1)
        ],
    }


def _source_png() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (1024, 1536), "#f5efdf").save(output, "PNG")
    return output.getvalue()


def test_all_premium_modes_use_six_card_contract() -> None:
    for mode in CAROUSEL_MODES:
        with patch("app.modules.content.illustrated_carousel._context", return_value="kaynak"), patch(
            "app.modules.content.illustrated_carousel.llm_json", return_value=_plan()
        ) as llm:
            plan = generate_carousel_plan("Safha Maliyeti", mode)
        validate_carousel_plan(plan)
        assert len(plan["cards"]) == 6
        assert "altı kartlık" in llm.call_args.kwargs["messages"][1]["content"]


def test_png_pipeline_generates_six_4x5_images() -> None:
    encoded = base64.b64encode(_source_png()).decode("ascii")
    client = Mock()
    client.images.generate.return_value = SimpleNamespace(data=[SimpleNamespace(b64_json=encoded)])
    uploaded: list[bytes] = []

    def fake_upload(data: bytes, *_args) -> str:
        uploaded.append(data)
        return f"https://cdn.test/{len(uploaded)}.png"

    with patch("app.modules.content.illustrated_carousel.upload_bytes", side_effect=fake_upload):
        plan, urls = generate_carousel_pngs(
            "job-123", "Safha Maliyeti", "illustrated", plan=_plan(), client=client
        )

    assert len(plan["cards"]) == len(urls) == len(uploaded) == 6
    assert client.images.generate.call_count == 6
    for png in uploaded:
        with Image.open(io.BytesIO(png)) as image:
            assert image.size == (1080, 1350)
            assert image.format == "PNG"


def test_image_prompt_enforces_reference_style_and_exact_text() -> None:
    encoded = base64.b64encode(_source_png()).decode("ascii")
    client = Mock()
    client.images.generate.return_value = SimpleNamespace(data=[SimpleNamespace(b64_json=encoded)])
    with patch("app.modules.content.illustrated_carousel.upload_bytes", return_value="https://cdn.test/card.png"):
        generate_carousel_pngs(
            "job-123", "Safha Maliyeti", "illustrated", plan=_plan(), client=client
        )

    prompt = client.images.generate.call_args_list[1].kwargs["prompt"]
    assert "warm ivory recycled-paper" in prompt
    assert "hand-drawn black ink" in prompt
    assert "EXACT TITLE: Kart 2" in prompt
    assert "no dark navy background" in prompt
