"""
İçerik türü → generator → composition → sahne eşlemesi.
TEK DOĞRULUK KAYNAĞI — composition adı başka hiçbir yerde string olarak yazılmaz.
"""
from app.errors.registry import PipelineErrorException

CONTENT_PIPELINES: dict[str, dict] = {
    "quiz": {
        "generator": "quiz_storyboard",
        "composition": "QuizVideo",
        "aspect": "9:16",
        "fps": 30,
        "duration_range": (60, 90),
        "allowed_scenes": [
            "QuizIntroScene", "QuestionScene", "ThinkingTimerScene",
            "ChalkboardSolutionScene", "AnswerRevealScene", "QuizOutroScene",
            # geriye dönük uyumluluk — eski pipeline sahneleri
            "IntroScene", "ThinkingScene", "CorrectAnswerScene", "KeyPointScene",
            "OutroScene", "SplitQuizVerticalScene", "OptionAnalysisScene",
            "SplitQuizScene", "TAccountScene", "CalculationStepsScene",
        ],
        "required_scenes": ["QuestionScene", "ChalkboardSolutionScene"],
    },
    "lesson": {
        "generator": "lesson_storyboard",
        "composition": "LessonVideo",
        "aspect": "16:9",
        "fps": 30,
        "duration_range": (600, 1800),
        "allowed_scenes": [
            "LessonIntroScene", "AgendaScene", "ConceptScene", "DefinitionCardScene",
            "AccountCardScene", "JournalEntryScene", "TableScene", "ComparisonScene",
            "ExampleScene", "CommonMistakeScene", "ExamTipScene", "MiniRecapScene",
            "LessonOutroScene",
            # geriye dönük uyumluluk — lesson_storyboard.py sahneleri
            "LessonTitleScene", "LessonConceptScene", "LessonSummaryScene",
            "LessonCardScene", "LessonExampleScene",
            "TAccountScene", "CalculationStepsScene",
            # SGS konu anlatımı (sgs.py) — maks. 4 sahne, tek bileşen tekrarı validate_routing ile yakalanır
            "SplitLessonScene",
        ],
        "required_scenes": ["LessonTitleScene", "LessonConceptScene"],
    },
    "educational_reel": {
        "generator": "educational_reel_storyboard",
        "composition": "EducationalReel120",
        "aspect": "9:16",
        "fps": 30,
        "duration_range": (45, 130),
        "allowed_scenes": [
            "ReelHookScene", "ReelConceptScene", "AccountCardScene", "JournalEntryScene",
            "ReelExampleScene", "ReelMistakeScene", "ReelExamTipScene", "ReelCtaScene",
            # geriye dönük uyumluluk — eski EducationalReelScene bazlı storyboard'lar
            "EducationalReelScene",
        ],
        "required_scenes": ["EducationalReelScene"],
    },
    "motivation": {
        "generator": "motivation_storyboard",
        "composition": "MotivationVideo",
        "aspect": "9:16",
        "fps": 30,
        "duration_range": (30, 130),
        "scene_count_range": (12, 20),
        "avg_scene_seconds": (4, 7),
        "allowed_scenes": [
            "MotivationHookScene", "MotivationProblemScene", "MotivationEmpathyScene",
            "MotivationTurnScene", "MotivationStepScene", "MotivationProofScene",
            "MotivationFocusScene", "MotivationOutroScene",
            # geriye dönük uyumluluk
            "MotivationScene",
        ],
        "required_scenes": [
            "MotivationHookScene", "MotivationProblemScene",
            "MotivationStepScene", "MotivationOutroScene",
        ],
    },
    "quiz_board": {
        "generator": "quiz_storyboard",
        "composition": "QuizBoardVideo",
        "aspect": "16:9",
        "fps": 30,
        "duration_range": (30, 300),
        "allowed_scenes": [
            "QuizBoardIntroScene", "QuizBoardQuestionScene", "QuizBoardSolutionScene",
            "QuizBoardHighlightScene", "QuizBoardOutroScene",
        ],
        "required_scenes": ["QuizBoardSolutionScene"],
    },
    "infographic": {
        "generator": "infographic_storyboard",
        "composition": "InfographicVideo",
        "aspect": "9:16",
        "fps": 30,
        "duration_range": (45, 120),
        "allowed_scenes": [
            "InfographicIntroScene", "AccountCardScene", "JournalEntryScene",
            "TableScene", "RuleBoxScene", "ReelCtaScene",
            # geriye dönük uyumluluk
            "InfographicCardGridScene", "InfographicComparisonScene", "InfographicProcessScene",
        ],
        "required_scenes": ["InfographicCardGridScene"],
    },
}

# İçerik tipi takma adları → canonical tip
_ALIASES: dict[str, str] = {
    "reel":              "educational_reel",
    "bilgilendirme_kisa": "educational_reel",
    "kisa_icerik":       "educational_reel",
    "educational_reel":  "educational_reel",
    "quiz":              "quiz",
    "question_set_long": "quiz",
    "single_question":   "quiz",
    "lesson":            "lesson",
    "konu_anlatimi":     "lesson",
    "lesson_long":       "lesson",
    "sgs_topic_video":   "lesson",
    "motivation":        "motivation",
    "motivation_reel":   "motivation",
    "shorts":            "motivation",
    "infographic":       "infographic",
    "quiz_board":        "quiz_board",
    "soru_cozum_tahtasi": "quiz_board",
}


def canonical_type(content_type: str) -> str:
    """Takma adı canonical tipe çevirir; bilinmiyorsa orijinali döner."""
    return _ALIASES.get(content_type, content_type)


def get_composition(content_type: str) -> str:
    """content_type için doğru Remotion composition adını döndürür."""
    ct = canonical_type(content_type)
    cfg = CONTENT_PIPELINES.get(ct)
    if not cfg:
        raise PipelineErrorException(
            "invalid_scene_for_content_type",
            admin_detail={"reason": "unknown_content_type", "got": content_type},
            stage="routing",
        )
    return cfg["composition"]


def validate_routing(content_type: str, scenes: list[dict]) -> None:
    """
    Render öncesi hard fail — izin verilmeyen sahne veya eksik zorunlu sahne varsa
    PipelineErrorException fırlatır.
    """
    ct = canonical_type(content_type)
    cfg = CONTENT_PIPELINES.get(ct)
    if not cfg:
        raise PipelineErrorException(
            "invalid_scene_for_content_type",
            admin_detail={"reason": "unknown_content_type", "got": content_type},
            stage="routing",
        )

    allowed = set(cfg["allowed_scenes"])
    used_components = [s.get("component", "") for s in scenes]
    used_set = set(used_components)

    invalid = used_set - allowed
    if invalid:
        raise PipelineErrorException(
            "invalid_scene_for_content_type",
            admin_detail={
                "invalid_scenes": sorted(invalid),
                "allowed_scenes": sorted(allowed),
                "content_type": ct,
            },
            stage="routing",
        )

    missing = set(cfg["required_scenes"]) - used_set
    if missing:
        raise PipelineErrorException(
            "invalid_scene_for_content_type",
            admin_detail={
                "missing_required": sorted(missing),
                "content_type": ct,
            },
            stage="routing",
        )

    # Tek tip sahne tekrarı = şablon çöküşü (SplitLessonScene×4, MotivationScene×5 gibi)
    if len(used_set) == 1 and len(scenes) > 1:
        raise PipelineErrorException(
            "failed_visual_validation",
            admin_detail={
                "reason": "single_component_repeated",
                "component": used_set.pop(),
                "count": len(scenes),
            },
            stage="routing",
        )
