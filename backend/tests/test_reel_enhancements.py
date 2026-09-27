import base64
import io
from types import SimpleNamespace

import pytest
from PIL import Image

from app.modules.content.reel_enhancements import (
    _scene_visual_intent,
    add_animated_illustrations,
    build_single_question_reel,
    build_viral_title_reel,
)
from app.pipelines.registry import validate_routing


def _question():
    return {
        "text": "İndirilecek KDV hangi tarafta izlenir?",
        "options": [{"label": label, "text": f"Seçenek {label}"} for label in "ABCDE"],
        "correct_label": "B",
        "explanation": "İndirilecek KDV varlık niteliğinde borçta izlenir.",
    }


def test_single_question_reel_has_five_options_and_memory_hook():
    board = build_single_question_reel(
        title="KDV", topic="KDV", subject="Muhasebe", question=_question(), brand={},
    )
    assert board["reel_mode"] == "single_question"
    assert [s["component"] for s in board["scenes"]] == [
        "ReelHookScene", "DrawnQuestionExplainerScene", "ReelCtaScene",
    ]
    assert [o["label"] for o in board["scenes"][1]["options"]] == list("ABCDE")
    assert board["scenes"][1]["memory_hook"]


def test_single_question_rejects_missing_option():
    question = _question()
    question["options"] = question["options"][:4]
    with pytest.raises(ValueError, match="A-E"):
        build_single_question_reel(title="x", topic="x", subject="x", question=question, brand={})


def test_viral_title_reel_uses_dedicated_scene_and_original_copy_bank():
    board = build_viral_title_reel(title="Unvan", topic="SMMM sınav motivasyonu", brand={})
    assert len(board["scenes"]) == 1
    assert board["scenes"][0]["component"] == "ViralTitleScene"
    assert "unvan" in board["scenes"][0]["subtitle"].lower()
    assert board["scenes"][0]["voice_text"]
    validate_routing("motivasyon", board["scenes"])


def test_animated_illustrations_enrich_only_three_scenes(monkeypatch):
    image = Image.new("RGB", (1024, 1536), "white")
    buf = io.BytesIO()
    image.save(buf, "PNG")
    encoded = base64.b64encode(buf.getvalue()).decode()

    class Images:
        def generate(self, **_kwargs):
            return SimpleNamespace(data=[SimpleNamespace(b64_json=encoded)])

    client = SimpleNamespace(images=Images())
    monkeypatch.setattr(
        "app.modules.content.reel_enhancements.upload_bytes",
        lambda _data, _bucket, path, _type: f"https://cdn.test/{path}",
    )
    board = {"scenes": [
        {"id": i, "component": "ReelConceptScene", "segment_type": "content", "title": f"S{i}", "voice_text": "Açıklama"}
        for i in range(1, 6)
    ]}
    result = add_animated_illustrations(board, job_id="job-1", topic="KDV", client=client, limit=5)
    illustrated = [s for s in result["scenes"] if s["component"] == "AnimatedIllustrationScene"]
    assert len(illustrated) == 5
    assert [s["animation_preset"] for s in illustrated] == [
        "draw_reveal", "parallax_parts", "focus_pulse", "draw_reveal", "parallax_parts",
    ]
    assert len({s["visual_intent"]["scene_purpose"] for s in illustrated}) == 5


@pytest.mark.parametrize(
    ("topic", "required_terms"),
    [
        ("Python'da list comprehension", ("Python", "list comprehension")),
        ("Tekstil fabrikasında kalite kontrol", ("Tekstil", "kalite kontrol")),
        ("Kahve çekirdeği kavurma süreci", ("Kahve", "kavurma")),
    ],
)
def test_video_scene_visual_intent_is_topic_specific(topic, required_terms):
    intent = _scene_visual_intent(
        topic, {"id": 1, "title": "Süreç ayrıntısı", "voice_text": "Açıklama"}, 3,
    )
    assert all(term.casefold() in intent["search_query"].casefold() for term in required_terms)
    assert intent["scene_purpose"] == "process_detail"
    assert "çalışma masası" not in intent["search_query"].casefold()


def test_animated_mode_keeps_structured_table_as_real_table(monkeypatch):
    board = {"scenes": [{
        "id": 1, "component": "TableScene", "segment_type": "content",
        "headers": ["Özellik", "191", "391"], "rows": [["Doğar", "Alışta", "Satışta"]],
    }]}
    result = add_animated_illustrations(board, job_id="job-2", topic="KDV", client=SimpleNamespace())
    assert result["scenes"][0]["component"] == "TableScene"
    assert "illustration_url" not in result["scenes"][0]
