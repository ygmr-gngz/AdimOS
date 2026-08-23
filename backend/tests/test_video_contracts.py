import pytest

from app.api.routes.video import (
    QuizOption,
    QuizQuestion,
    _effective_duration_tolerance,
    _expected_render_duration,
    _questions_are_blank,
    _resolve_motivation_topic,
    _validate_manual_questions,
)
from app.pipelines.registry import validate_routing
from app.modules.content.motivation_generator import _voice_text
from app.modules.content.tr_speech_normalize import tr_speech_normalize


def _blank_question() -> QuizQuestion:
    return QuizQuestion(
        text="",
        options=[QuizOption(label=label, text="") for label in "ABCDE"],
        correct_label="A",
    )


def test_blank_question_form_means_auto_generation() -> None:
    assert _questions_are_blank([_blank_question(), _blank_question()])


def test_partial_manual_question_is_rejected() -> None:
    question = _blank_question()
    question.text = "KDV kaydı hangisidir?"
    with pytest.raises(ValueError, match="boş şık"):
        _validate_manual_questions([question])


def test_chalkboard_quiz_does_not_require_separate_question_scene() -> None:
    validate_routing("soru_cozum", [
        {"component": "IntroScene"},
        {"component": "ChalkboardSolutionScene"},
        {"component": "OutroScene"},
    ])


def test_long_video_tolerance_scales_with_requested_duration() -> None:
    assert _effective_duration_tolerance("konu_anlatimi", 720, 8) == 180
    assert _effective_duration_tolerance("soru_cozum", 600, 8) == 150
    assert _effective_duration_tolerance("reels_short", 60, 8) == 8


def test_render_duration_includes_scene_transition_frames() -> None:
    assert _expected_render_duration(52.78, 13) == pytest.approx(59.28)


def test_spoken_text_has_priority_for_tts() -> None:
    scene = {"spoken_text": "normalize edilmiş", "narration": "ham metin"}
    assert _voice_text(scene) == "normalize edilmiş"


def test_blank_motivation_topic_uses_content_bank() -> None:
    entry = {
        "id": 14,
        "title": "Her gün soru çözme alışkanlığı kuramıyorsun",
        "feeling": "isteksizlik",
        "action": "günde 10 soru, sabit saat",
        "sgs_fact": "günde 10 soru, ayda 300 soru demek",
    }
    from unittest.mock import patch
    with patch("app.core.content_bank_motivation.select_topic", return_value=entry):
        title, prompt_topic = _resolve_motivation_topic("   ")
    assert title == entry["title"]
    assert "günde 10 soru" in prompt_topic


def test_sgs_pronunciation_is_turkish_letter_names() -> None:
    assert tr_speech_normalize("SGS sınavı") == "se ge se sınavı"
