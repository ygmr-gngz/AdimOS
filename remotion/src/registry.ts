/**
 * registry.ts — Sahne bileşeni kaydı.
 *
 * Kanonik tür → izinli Remotion bileşen adları.
 * Adlar buradan türetilir; koda gömülmez, uydurulmaz.
 * Backend allowed_scenes listesi ve structured output şeması bu kaynaktan üretilir.
 *
 * registry.test.ts: bu kayıttaki adların src/scenes/ dışa aktarımlarıyla
 * birebir eşleşmesini doğrular (fazlalık veya eksik ad → test kırılır).
 */

export interface CompositionRegistryEntry {
  /** Remotion Root.tsx'deki Composition id */
  compositionId: string
  /** '16:9' | '9:16' */
  aspect: string
  /** İzinli sahne bileşeni adları */
  components: string[]
  /** Zorunlu sahne alanları (storyboard doğrulaması için) */
  required: string[]
}

export const SCENE_REGISTRY: Record<string, CompositionRegistryEntry> = {

  // ── konu_anlatimi → LessonVideo (16:9) ─────────────────────────
  LessonVideo: {
    compositionId: "LessonVideo",
    aspect:        "16:9",
    components: [
      "LessonTitleScene",
      "LessonConceptScene",
      "LessonCardScene",
      "LessonExampleScene",
      "LessonSummaryScene",
      "LessonInfographicScene",
      "LessonMindMapScene",
      "AccountCardScene",
      "TableScene",
      "JournalEntryScene",
      "RuleBoxScene",
      "CommonMistakeScene",
      "SplitLessonScene",
      // Gelecekte eklenecek (Bölüm 10):
      // "MistakeScene", "ExamTipScene", "RecapScene", "ComparisonScene"
    ],
    required: ["component", "duration_seconds"],
  },

  // ── soru_cozum → QuizVideo (16:9) ──────────────────────────────
  QuizVideo: {
    compositionId: "QuizVideo",
    aspect:        "16:9",
    components: [
      "IntroScene",
      "QuestionScene",
      "ThinkingScene",
      "OptionAnalysisScene",
      "CorrectAnswerScene",
      "KeyPointScene",
      "OutroScene",
      "ChalkboardSolutionScene",
      "SplitQuizScene",
      "TAccountScene",
      "CalculationStepsScene",
      "JournalEntryScene",
    ],
    required: ["component", "duration_seconds"],
  },

  // ── soru_cozum → SplitQuizVerticalDemo (9:16) ──────────────────
  SplitQuizVerticalDemo: {
    compositionId: "SplitQuizVerticalDemo",
    aspect:        "9:16",
    components: [
      "SplitQuizVerticalScene",
    ],
    required: ["component", "duration_seconds"],
  },

  // ── reels_short → EducationalReel / EducationalReel120 (9:16) ──
  EducationalReel: {
    compositionId: "EducationalReel",
    aspect:        "9:16",
    components: [
      "EducationalReelScene",     // genel amaçlı (segment_type ile yönlendirme)
      "ReelHookScene",            // → EducationalReelScene segment_type=hook
      "ReelConceptScene",         // → EducationalReelScene segment_type=content
      "ReelExampleScene",         // → EducationalReelScene segment_type=content
      "ReelMistakeScene",         // → EducationalReelScene segment_type=mistake
      "ReelExamTipScene",         // → EducationalReelScene segment_type=tip
      "ReelCtaScene",             // → EducationalReelScene segment_type=outro
      "AccountCardScene",
      "TableScene",
      "JournalEntryScene",
      "RuleBoxScene",
      "CommonMistakeScene",
    ],
    required: ["component", "duration_seconds"],
  },

  // Reels storyboard'undan türetilen statik 4:5 Instagram özet postu.
  SummaryPostVideo: {
    compositionId: "SummaryPostVideo",
    aspect:        "4:5",
    components: [
      "EducationalReelScene", "ReelHookScene", "ReelConceptScene",
      "ReelExampleScene", "ReelMistakeScene", "ReelExamTipScene", "ReelCtaScene",
      "AccountCardScene", "TableScene", "JournalEntryScene", "RuleBoxScene", "CommonMistakeScene",
    ],
    required: ["component", "duration_seconds"],
  },

  // ── motivasyon → MotivationVideo (9:16) ────────────────────────
  MotivationVideo: {
    compositionId: "MotivationVideo",
    aspect:        "9:16",
    components: [
      "MotivationHookScene",
      "MotivationProblemScene",
      "MotivationEmpathyScene",
      "MotivationStepScene",
      "MotivationFocusScene",
      "MotivationOutroScene",
      "MotivationScene",          // eski/genel amaçlı
    ],
    required: ["component", "duration_seconds"],
  },

  // ── gorsel_post → InfographicVideo (9:16) ──────────────────────
  InfographicVideo: {
    compositionId: "InfographicVideo",
    aspect:        "9:16",
    components: [
      "AccountCardScene",
      "InfographicCardGridScene",
      "InfographicComparisonScene",
      "InfographicProcessScene",
    ],
    required: ["component", "duration_seconds"],
  },

  // ── quiz_board → QuizBoardVideo (16:9, canonical dışı) ─────────
  // Sahneler QuizBoardVideo.tsx içinde tanımlıdır.
  QuizBoardVideo: {
    compositionId: "QuizBoardVideo",
    aspect:        "16:9",
    components: [
      "QuizBoardIntroScene",
      "QuizBoardQuestionScene",
      "QuizBoardSolutionScene",
      "QuizBoardHighlightScene",
      "QuizBoardOutroScene",
    ],
    required: ["component", "duration_seconds"],
  },
}

/** Kompozisyon ID'sinden izinli bileşen adlarını döndür. */
export function getAllowedComponents(compositionId: string): string[] {
  return SCENE_REGISTRY[compositionId]?.components ?? []
}

/** Tüm kayıtlı bileşen adlarının düz listesi (tekrar içerebilir). */
export function allRegisteredComponents(): string[] {
  return Object.values(SCENE_REGISTRY).flatMap(e => e.components)
}
