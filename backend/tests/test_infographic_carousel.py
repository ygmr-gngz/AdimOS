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
    concepts = [
        ("soru kancası", "kapıyı açar", "sınıf"),
        ("süreç haritası", "oklarla bağlar", "fabrika"),
        ("hesap makinesi", "sonucu hesaplar", "çalışma masası"),
        ("yevmiye tablosu", "satırları dengeler", "muhasebe ofisi"),
        ("yol ayrımı", "yanlışı doğrudan ayırır", "kavşak"),
        ("hafıza ampulü", "ipucunu aydınlatır", "sınav salonu"),
    ]
    return {
        "topic": "Safha Maliyeti",
        "cards": [
            {
                "kind": kind, "title": f"Kart {index}", "subtitle": "Kısa açıklama",
                "bullets": ["Kısa bilgi"],
                "visual_intent": {
                    "semantic_focus": concepts[index - 1][0],
                    "visual_concept": concepts[index - 1][0],
                    "subjects": [f"nesne {index}"],
                    "action": concepts[index - 1][1],
                    "environment": concepts[index - 1][2], "symbols": [f"sembol {index}"],
                    "search_query": " ".join(concepts[index - 1]),
                    "avoid": [f"diğer kart {index}"],
                },
            }
            for index, kind in enumerate(kinds, 1)
        ],
    }


def _source_png(color: str = "#f5efdf") -> bytes:
    output = io.BytesIO()
    image = Image.new("RGB", (1024, 1536), color)
    # dHash'in kartlar arasında ayrışması için farklı bir dikey işaret ekle.
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    marker = int(color[-2:], 16) % 8
    draw.rectangle((marker * 110, 100, marker * 110 + 80, 1400), fill="#111111")
    image.save(output, "PNG")
    return output.getvalue()


def test_all_premium_modes_use_six_card_contract() -> None:
    for mode in CAROUSEL_MODES:
        context = SimpleNamespace(text="kaynak", evidence_ids=(), rejected_count=0)
        with patch("app.modules.content.illustrated_carousel._context_bundle", return_value=context), patch(
            "app.modules.content.illustrated_carousel.llm_json", return_value=_plan()
        ) as llm:
            plan = generate_carousel_plan("Safha Maliyeti", mode)
        validate_carousel_plan(plan)
        assert len(plan["cards"]) == 6
        assert "altı kartlık" in llm.call_args.kwargs["messages"][1]["content"]


def test_png_pipeline_generates_six_4x5_images() -> None:
    client = Mock()
    colors = ["#f5ef01", "#f5ef02", "#f5ef03", "#f5ef04", "#f5ef05", "#f5ef06"]
    client.images.generate.side_effect = [
        SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(_source_png(c)).decode("ascii"))])
        for c in colors
    ]
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
    client = Mock()
    colors = ["#f5ef11", "#f5ef12", "#f5ef13", "#f5ef14", "#f5ef15", "#f5ef16"]
    client.images.generate.side_effect = [
        SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(_source_png(c)).decode("ascii"))])
        for c in colors
    ]
    with patch("app.modules.content.illustrated_carousel.upload_bytes", return_value="https://cdn.test/card.png"):
        generate_carousel_pngs(
            "job-123", "Safha Maliyeti", "illustrated", plan=_plan(), client=client
        )

    prompt = client.images.generate.call_args_list[1].kwargs["prompt"]
    assert "warm ivory recycled-paper" in prompt
    assert "hand-drawn black ink" in prompt
    assert "EXACT TITLE: Kart 2" in prompt
    assert "no dark navy background" in prompt


def test_application_prompt_cannot_leak_previous_topic_facts() -> None:
    from app.modules.content.illustrated_carousel import _card_prompt
    card = {
        "kind": "account_application",
        "title": "KDV Uygulama Tablosu",
        "subtitle": "KDV hesaplamasında adımlar",
        "bullets": ["Alış KDV'sini belirle", "Satış KDV'sini hesapla"],
        "visual_intent": {"semantic_focus": "KDV farkı", "visual_concept": "iki vergi sütunu",
            "subjects": ["faturalar"], "action": "karşılaştırma", "environment": "muhasebe masası",
            "symbols": ["eksi"], "search_query": "KDV indirilecek hesaplanan karşılaştırma", "avoid": []},
    }
    prompt = _card_prompt("İndirilecek ve Hesaplanan KDV Farkı", card, 4)
    assert "DBYM" not in prompt
    assert "DSYM" not in prompt
    assert "only from the supplied exact lines" in prompt
