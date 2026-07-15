import { AbsoluteFill, Sequence } from 'remotion'
import { StoryboardJSON, Scene, SceneComponent } from '../types'
import { FPS, LESSON_PALETTE as L } from '../brand'
import { getTotalFrames, TRANSITION_FRAMES } from '../utils'
import { LessonTitleScene } from '../scenes/LessonTitleScene'
import { LessonConceptScene } from '../scenes/LessonConceptScene'
import { LessonCardScene } from '../scenes/LessonCardScene'
import { LessonExampleScene } from '../scenes/LessonExampleScene'
import { LessonSummaryScene } from '../scenes/LessonSummaryScene'
// Eski sahne tipleri — ortak varlıktan kullanılmaya devam ediyor
import { IntroScene } from '../scenes/IntroScene'
import { OutroScene } from '../scenes/OutroScene'
import { JournalEntryScene } from '../scenes/JournalEntryScene'
import { TAccountScene } from '../scenes/TAccountScene'
import { CalculationStepsScene } from '../scenes/CalculationStepsScene'
import { InfographicCardGridScene } from '../scenes/InfographicCardGridScene'
import { InfographicComparisonScene } from '../scenes/InfographicComparisonScene'
import { InfographicProcessScene } from '../scenes/InfographicProcessScene'

function LessonSceneRenderer({ scene, brand }: { scene: Scene; brand: StoryboardJSON['brand'] }) {
  const p = { scene, brand }
  switch (scene.component as SceneComponent) {
    // ── Yeni Lesson sahneleri ──────────────────────────────────
    case 'LessonTitleScene':   return <LessonTitleScene {...p} />
    case 'LessonConceptScene': return <LessonConceptScene {...p} />
    case 'LessonCardScene':    return <LessonCardScene {...p} />
    case 'LessonExampleScene': return <LessonExampleScene {...p} />
    case 'LessonSummaryScene': return <LessonSummaryScene {...p} />

    // ── Ortak sahneler ─────────────────────────────────────────
    case 'IntroScene': return <IntroScene {...p} />
    case 'OutroScene': return <OutroScene {...p} />
    case 'JournalEntryScene': return <JournalEntryScene {...p} />
    case 'TAccountScene': return <TAccountScene {...p} />
    case 'CalculationStepsScene': return <CalculationStepsScene {...p} />
    case 'InfographicCardGridScene': return <InfographicCardGridScene {...p} />
    case 'InfographicComparisonScene': return <InfographicComparisonScene {...p} />
    case 'InfographicProcessScene': return <InfographicProcessScene {...p} />

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
    const durationFrames = Math.round(scene.duration_seconds * FPS) + TRANSITION_FRAMES
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
    </AbsoluteFill>
  )
}

export { getTotalFrames as getLessonTotalFrames }
