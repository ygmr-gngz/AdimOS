import { AbsoluteFill, Sequence, Audio } from 'remotion'
import { StoryboardJSON, Scene, SceneComponent } from '../types'
import { FPS } from '../brand'
import { IntroScene } from '../scenes/IntroScene'
import { QuestionScene } from '../scenes/QuestionScene'
import { ThinkingScene } from '../scenes/ThinkingScene'
import { OptionAnalysisScene } from '../scenes/OptionAnalysisScene'
import { CorrectAnswerScene } from '../scenes/CorrectAnswerScene'
import { KeyPointScene } from '../scenes/KeyPointScene'
import { OutroScene } from '../scenes/OutroScene'

// Her sahne arasında 1 saniyelik siyah geçiş
const TRANSITION_FRAMES = 15

function SceneRenderer({ scene, brand }: { scene: Scene; brand: StoryboardJSON['brand'] }) {
  const props = { scene, brand }
  switch (scene.component as SceneComponent) {
    case 'IntroScene': return <IntroScene {...props} />
    case 'QuestionScene': return <QuestionScene {...props} />
    case 'ThinkingScene': return <ThinkingScene {...props} />
    case 'OptionAnalysisScene': return <OptionAnalysisScene {...props} />
    case 'CorrectAnswerScene': return <CorrectAnswerScene {...props} />
    case 'KeyPointScene': return <KeyPointScene {...props} />
    case 'OutroScene': return <OutroScene {...props} />
    default:
      return (
        <div style={{
          width: '100%', height: '100%',
          background: brand.background_color,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <p style={{ color: brand.primary_color, fontSize: 24, fontFamily: brand.font_body }}>
            {scene.title ?? scene.component}
          </p>
        </div>
      )
  }
}

interface QuizVideoProps {
  storyboard: StoryboardJSON
}

export function QuizVideo({ storyboard }: QuizVideoProps) {
  const { brand, scenes } = storyboard

  // Kümülatif başlangıç frame'lerini hesapla
  let cursor = 0
  const sceneTimings = scenes.map(scene => {
    const start = cursor
    const durationFrames = Math.round(scene.duration_seconds * FPS) + TRANSITION_FRAMES
    cursor += durationFrames
    return { scene, start, durationFrames }
  })

  return (
    <AbsoluteFill style={{ background: brand.background_color }}>
      {sceneTimings.map(({ scene, start, durationFrames }) => (
        <Sequence key={scene.id} from={start} durationInFrames={durationFrames}>
          <AbsoluteFill>
            <SceneRenderer scene={scene} brand={brand} />
          </AbsoluteFill>
        </Sequence>
      ))}
    </AbsoluteFill>
  )
}

// Storyboard'dan toplam frame sayısını hesapla
export function getTotalFrames(storyboard: StoryboardJSON): number {
  return storyboard.scenes.reduce(
    (acc, s) => acc + Math.round(s.duration_seconds * FPS) + TRANSITION_FRAMES,
    0
  )
}
