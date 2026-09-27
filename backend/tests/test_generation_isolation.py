import base64
import io
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from PIL import Image, ImageDraw

from app.modules.content.context_isolation import RequiredGroundingError, retrieve_isolated_context
from app.modules.content.illustrated_carousel import (
    _difference_hash,
    _to_instagram_4x5,
    generate_carousel_plan,
    generate_carousel_pngs,
    validate_carousel_plan,
)


KINDS = ["hook", "overview", "worked_example", "account_application", "common_mistake", "exam_tip"]


def _plan(topic: str) -> dict:
    concepts = [
        ("kilitli kapı", "anahtarla açma", "arşiv odası"),
        ("akış şeması", "oklarla ilerleme", "üretim hattı"),
        ("hesap makinesi", "rakamları toplama", "çalışma masası"),
        ("iki sütun", "borç alacak dengeleme", "muhasebe ofisi"),
        ("yol ayrımı", "yanlış doğru ayırma", "şehir kavşağı"),
        ("hafıza ampulü", "ipucunu yakma", "sınav salonu"),
    ]
    return {
        "topic": "MODELİN DEĞİŞTİRMEMESİ GEREKEN DEĞER",
        "cards": [
            {
                "kind": kind,
                "title": f"{topic} {index}",
                "subtitle": f"{topic} alt konu {index}",
                "bullets": [f"{topic} bilgi {index}"],
                "visual_intent": {
                    "semantic_focus": concepts[index - 1][0],
                    "visual_concept": concepts[index - 1][0],
                    "subjects": [f"özne {index}"],
                    "action": concepts[index - 1][1],
                    "environment": concepts[index - 1][2],
                    "symbols": [f"sembol {index}"],
                    "search_query": f"{topic} {' '.join(concepts[index - 1])}",
                    "avoid": [f"metafor {index + 1}"],
                },
            }
            for index, kind in enumerate(KINDS, 1)
        ],
    }


def _png(marker: int) -> str:
    image = Image.new("RGB", (1024, 1536), "#f5efdf")
    draw = ImageDraw.Draw(image)
    lane = marker % 8
    draw.rectangle((lane * 120, 100, lane * 120 + 70, 1400), fill="#111111")
    draw.rectangle((50, 100 + marker * 17, 950, 120 + marker * 17), fill="#374151")
    output = io.BytesIO()
    image.save(output, "PNG")
    return base64.b64encode(output.getvalue()).decode("ascii")


def test_context_rejects_high_scoring_but_unrelated_previous_topic() -> None:
    chunks = [
        {"id": "old", "content": "Safha maliyetinde DBYM ve DSYM miktar dengesi", "similarity": 0.65},
        {"id": "current", "content": "İndirilecek KDV alışlarda, hesaplanan KDV satışlarda doğar", "similarity": 0.82},
    ]
    bundle = retrieve_isolated_context(
        "İndirilecek KDV ve Hesaplanan KDV",
        max_chars=1000, per_chunk_chars=500, generation_id="job-kdv",
        retriever=lambda *_args, **_kwargs: chunks,
    )
    assert "DBYM" not in bundle.text
    assert "İndirilecek KDV" in bundle.text
    assert bundle.evidence_ids == ("current",)


@pytest.mark.parametrize(
    ("old_text", "topic", "current_text", "forbidden"),
    [
        (
            "Python coding ile makine öğrenmesi tutorial modeli",
            "Tekstil üretiminde kalite kontrol",
            "Tekstil üretiminde kalite kontrol kumaş kusurlarını sınıflandırır",
            "Python",
        ),
        (
            "Uzay araştırmaları roket ve yörünge görevi",
            "Kahve çekirdeği kavurma",
            "Kahve çekirdeği kavurma sıcaklık ve aroma gelişimini etkiler",
            "roket",
        ),
    ],
)
def test_unrelated_memory_never_enters_generation_context(old_text, topic, current_text, forbidden) -> None:
    bundle = retrieve_isolated_context(
        topic, max_chars=1000, per_chunk_chars=500, generation_id="isolated",
        retriever=lambda *_args, **_kwargs: [
            {"id": "old", "content": old_text, "similarity": 0.65},
            {"id": "new", "content": current_text, "similarity": 0.80},
        ],
    )
    assert forbidden.casefold() not in bundle.text.casefold()
    assert bundle.evidence_ids == ("new",)


@pytest.mark.parametrize(
    ("score", "text", "accepted"),
    [
        (0.49, "müşteri kaybı ölçümü", False),
        (0.50, "müşteri kaybı ölçümü", True),
        (0.70, "müşteri kaybı ölçümü", True),
        (0.79, "abonelikten ayrılma ve churn analizi", True),
    ],
)
def test_hybrid_similarity_threshold_boundaries(score, text, accepted) -> None:
    bundle = retrieve_isolated_context(
        "müşteri kaybı", max_chars=500, per_chunk_chars=500,
        min_similarity=0.50, high_confidence_similarity=0.78,
        retriever=lambda *_args, **_kwargs: [{"id": "candidate", "content": text, "similarity": score}],
    )
    assert (bundle.evidence_ids == ("candidate",)) is accepted


@pytest.mark.parametrize(
    ("topic", "semantic_text"),
    [
        ("yapay zeka", "artificial intelligence adoption in finance"),
        ("kalite hatası", "quality defect inspection in textile production"),
        ("müşteri terk oranı", "subscription churn and cancellation behavior"),
    ],
)
def test_high_confidence_semantic_match_can_bypass_lexical_anchor(topic, semantic_text) -> None:
    bundle = retrieve_isolated_context(
        topic, max_chars=500, per_chunk_chars=500,
        min_similarity=0.50, high_confidence_similarity=0.78,
        retriever=lambda *_args, **_kwargs: [
            {"id": "semantic", "content": semantic_text, "similarity": 0.82}
        ],
    )
    assert bundle.evidence_ids == ("semantic",)


def test_required_grounding_fails_closed_when_no_evidence() -> None:
    with pytest.raises(RequiredGroundingError, match="required_grounding_missing"):
        retrieve_isolated_context(
            "Bu PDF'e göre vergi uygulaması", max_chars=500, per_chunk_chars=500,
            required_grounding=True, retriever=lambda *_args, **_kwargs: [],
        )


def test_two_unrelated_topics_do_not_share_plan_state() -> None:
    first = _plan("Safha Maliyeti")
    second = _plan("KDV Farkı")
    context = SimpleNamespace(text="yalnız güncel kaynak", evidence_ids=("current",), rejected_count=1)
    with patch("app.modules.content.illustrated_carousel._context_bundle", return_value=context), patch(
        "app.modules.content.illustrated_carousel.llm_json", side_effect=[first, first, second, second]
    ):
        safha = generate_carousel_plan("Safha Maliyeti", "illustrated", generation_id="job-1")
        kdv = generate_carousel_plan("KDV Farkı", "illustrated", generation_id="job-2")
    assert safha["topic"] == "Safha Maliyeti"
    assert kdv["topic"] == "KDV Farkı"
    assert "Safha" not in str(kdv["cards"])
    assert safha["generation_debug"]["generation_id"] != kdv["generation_debug"]["generation_id"]


def test_same_topic_cards_require_distinct_subtopic_visual_intents() -> None:
    plan = _plan("KDV")
    plan["cards"][1]["visual_intent"] = dict(plan["cards"][0]["visual_intent"])
    with pytest.raises(RuntimeError, match="carousel_plan_invalid"):
        validate_carousel_plan(plan)


def test_visual_intent_semantic_laptop_variants_are_rejected() -> None:
    plan = _plan("Teknoloji")
    variants = [
        "person working on laptop at desk",
        "developer coding at computer",
        "engineer sitting in front of laptop",
    ]
    for card, value in zip(plan["cards"][:3], variants):
        card["visual_intent"].update({
            "semantic_focus": value, "visual_concept": value,
            "action": value, "environment": "office", "search_query": value,
        })
    with pytest.raises(RuntimeError, match="carousel_plan_invalid"):
        validate_carousel_plan(plan)


def test_visual_intent_distinct_textile_concepts_are_accepted() -> None:
    plan = _plan("Tekstil")
    concepts = [
        "close-up sewing needle", "factory production line", "fabric defect inspection",
        "shipping containers", "retail clothing rack", "exam memory lightbulb",
    ]
    for card, value in zip(plan["cards"], concepts):
        card["visual_intent"].update({
            "semantic_focus": value, "visual_concept": value,
            "action": value, "environment": value, "search_query": value,
        })
    validate_carousel_plan(plan)


def test_duplicate_retry_is_bounded_and_degrades_gracefully() -> None:
    client = Mock()
    same = SimpleNamespace(data=[SimpleNamespace(b64_json=_png(1))])
    client.images.generate.return_value = same
    with patch("app.modules.content.illustrated_carousel.upload_bytes", return_value="https://cdn/card.png"):
        _, urls = generate_carousel_pngs(
            "bounded", "KDV", "illustrated", plan=_plan("KDV"), client=client,
        )
    assert len(urls) == 6
    assert client.images.generate.call_count == 1 + 5 * 3


def test_image_normalization_handles_transparency_and_resolution() -> None:
    transparent = Image.new("RGBA", (400, 800), (255, 0, 0, 0))
    draw = ImageDraw.Draw(transparent)
    draw.rectangle((50, 100, 200, 700), fill=(0, 0, 0, 255))
    raw = io.BytesIO()
    transparent.save(raw, "PNG")
    normalized = _to_instagram_4x5(raw.getvalue())
    with Image.open(io.BytesIO(normalized)) as image:
        assert image.mode == "RGB"
        assert image.size == (1080, 1350)
    assert isinstance(_difference_hash(normalized), int)


@pytest.mark.parametrize("payload", [b"not-an-image", b""])
def test_corrupted_image_fails_with_explicit_error(payload) -> None:
    with pytest.raises(RuntimeError, match="carousel_image_invalid"):
        _to_instagram_4x5(payload)


def test_tiny_image_is_rejected_before_hashing_pipeline() -> None:
    tiny = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(tiny, "PNG")
    with pytest.raises(RuntimeError, match="çok küçük"):
        _to_instagram_4x5(tiny.getvalue())


def test_perceptual_duplicate_is_regenerated_before_upload() -> None:
    client = Mock()
    # card 2 first repeats card 1, then receives a distinct retry.
    markers = [1, 1, 2, 3, 4, 5, 6]
    client.images.generate.side_effect = [
        SimpleNamespace(data=[SimpleNamespace(b64_json=_png(marker))]) for marker in markers
    ]
    uploads: list[bytes] = []
    plan = _plan("KDV")
    plan["generation_debug"] = {"slides": [{} for _ in range(6)]}
    with patch(
        "app.modules.content.illustrated_carousel.upload_bytes",
        side_effect=lambda data, *_args: uploads.append(data) or f"https://cdn/{len(uploads)}.png",
    ):
        _, urls = generate_carousel_pngs(
            "rapid-job-2", "KDV", "illustrated", plan=plan, client=client,
        )
    assert len(urls) == len(uploads) == 6
    assert client.images.generate.call_count == 7
    retry_prompt = client.images.generate.call_args_list[2].kwargs["prompt"]
    assert "Previous cards already used these concepts" in retry_prompt
    assert plan["generation_debug"]["slides"][1]["retry_count"] == 1
    assert plan["generation_debug"]["slides"][1]["dedup_exhausted"] is False


def test_generation_and_cache_identity_are_isolated_for_rapid_topics() -> None:
    """There is no response cache: each job renders and gets generation-scoped paths."""
    client = Mock()
    markers = list(range(1, 13))
    client.images.generate.side_effect = [
        SimpleNamespace(data=[SimpleNamespace(b64_json=_png(marker))]) for marker in markers
    ]
    paths: list[str] = []
    with patch(
        "app.modules.content.illustrated_carousel.upload_bytes",
        side_effect=lambda _data, _bucket, path, _mime: paths.append(path) or f"https://cdn/{path}",
    ):
        first, _ = generate_carousel_pngs(
            "generation-A", "Uzay araştırmaları", "illustrated",
            plan=_plan("Uzay araştırmaları"), client=client,
        )
        second, _ = generate_carousel_pngs(
            "generation-B", "Kahve çekirdeği kavurma", "illustrated",
            plan=_plan("Kahve çekirdeği kavurma"), client=client,
        )
    assert client.images.generate.call_count == 12
    assert len(paths) == len(set(paths)) == 12
    assert all("generation-A" in path for path in paths[:6])
    assert all("generation-B" in path for path in paths[6:])
    assert "Uzay" not in str(second["cards"])
    assert first is not second
