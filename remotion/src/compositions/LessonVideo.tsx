import { AbsoluteFill, Sequence } from 'remotion'
import { StoryboardJSON, Scene, SceneComponent } from '../types'
import { BrandOverlay } from '../components/BrandOverlay'
import { FPS, LESSON_PALETTE as L } from '../brand'
import { getTotalFrames, TRANSITION_FRAMES } from '../utils'
import { LessonTitleScene } from '../scenes/LessonTitleScene'
import { LessonConceptScene } from '../scenes/LessonConceptScene'
import { LessonCardScene } from '../scenes/LessonCardScene'
import { LessonExampleScene } from '../scenes/LessonExampleScene'
import { LessonSummaryScene } from '../scenes/LessonSummaryScene'
// Geriye dönük uyumluluk — eski pipeline bu tip üretiyordu
import { SplitLessonScene } from '../scenes/SplitLessonScene'
// Eski sahne tipleri — ortak varlıktan kullanılmaya devam ediyor
import { IntroScene } from '../scenes/IntroScene'
import { OutroScene } from '../scenes/OutroScene'
import { JournalEntryScene } from '../scenes/JournalEntryScene'
import { TAccountScene } from '../scenes/TAccountScene'
import { CalculationStepsScene } from '../scenes/CalculationStepsScene'
import { InfographicCardGridScene } from '../scenes/InfographicCardGridScene'
import { InfographicComparisonScene } from '../scenes/InfographicComparisonScene'
import { InfographicProcessScene } from '../scenes/InfographicProcessScene'
import { ChalkboardSolutionScene } from '../scenes/ChalkboardSolutionScene'

function LessonSceneRenderer({ scene, brand }: { scene: Scene; brand: StoryboardJSON['brand'] }) {
  const p = { scene, brand }
  switch (scene.component as SceneComponent) {
    // ── Yeni Lesson sahneleri ──────────────────────────────────
    case 'LessonTitleScene':   return <LessonTitleScene {...p} />
    case 'LessonConceptScene': return <LessonConceptScene {...p} />
    case 'LessonCardScene':    return <LessonCardScene {...p} />
    case 'LessonExampleScene': return <LessonExampleScene {...p} />
    case 'LessonSummaryScene': return <LessonSummaryScene {...p} />

    // ── Geriye dönük uyumluluk — eski pipeline SplitLessonScene üretiyordu ──
    case 'SplitLessonScene': return <SplitLessonScene {...p} />

    // ── Ortak sahneler ─────────────────────────────────────────
    case 'IntroScene': return <IntroScene {...p} />
    case 'OutroScene': return <OutroScene {...p} />
    case 'JournalEntryScene': return <JournalEntryScene {...p} />
    case 'TAccountScene': return <TAccountScene {...p} />
    case 'CalculationStepsScene': return <CalculationStepsScene {...p} />
    case 'InfographicCardGridScene': return <InfographicCardGridScene {...p} />
    case 'InfographicComparisonScene': return <InfographicComparisonScene {...p} />
    case 'InfographicProcessScene': return <InfographicProcessScene {...p} />
    case 'ChalkboardSolutionScene': return <ChalkboardSolutionScene {...p} />

    default:
      return (
        <AbsoluteFill style={{
          background: L.BG,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <p style={{ color: L.NAVY, fontSize: 24, fontFamily: 'Lato' }}>
            {scene.title ?? scene.component}
          </p>
        </AbsoluteFill>
      )
  }
}

interface LessonVideoProps { storyboard: StoryboardJSON }

export function LessonVideo({ storyboard }: LessonVideoProps) {
  const { brand, scenes } = storyboard

  let cursor = 0
  const timings = scenes.map(scene => {
    const start = cursor
    // duration_seconds GPT'den string veya undefined gelebilir — NaN koruması
    const raw = scene.duration_seconds as number | string | undefined | null
    const safeSec = (typeof raw === 'number' && isFinite(raw) && raw > 0)
      ? raw
      : (typeof raw === 'string' && Number(raw) > 0)
        ? Number(raw)
        : 30
    const durationFrames = Math.max(TRANSITION_FRAMES + 1, Math.round(safeSec * FPS) + TRANSITION_FRAMES)
    cursor += durationFrames
    return { scene, start, durationFrames }
  })

  return (
    <AbsoluteFill style={{ background: L.BG }}>
      {timings.map(({ scene, start, durationFrames }) => (
        <Sequence key={scene.id} from={start} durationInFrames={durationFrames}>
          <AbsoluteFill>
            <LessonSceneRenderer scene={scene} brand={brand} />
          </AbsoluteFill>
        </Sequence>
      ))}
      <BrandOverlay brand={brand} theme="light" />
    </AbsoluteFill>
  )
}

export { getTotalFrames as getLessonTotalFrames }
