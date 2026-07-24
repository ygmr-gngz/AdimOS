/**
 * MotivationVideo — Kısa motivasyon videosu composition (15-30 sn)
 * 9:16 Shorts/Reels formatı
 */
import { AbsoluteFill, Sequence } from 'remotion'
import { StoryboardJSON } from '../types'
import { BrandOverlay } from '../components/BrandOverlay'
import { FPS } from '../brand'
import { TRANSITION_FRAMES } from '../utils'
import { MotivationScene } from '../scenes/MotivationScene'
import { IntroScene } from '../scenes/IntroScene'
import { OutroScene } from '../scenes/OutroScene'

interface Props { storyboard: StoryboardJSON }

export function MotivationVideo({ storyboard }: Props) {
  const { brand, scenes } = storyboard

  let cursor = 0
  const timings = scenes.map(scene => {
    const start = cursor
    const raw = scene.duration_seconds as number | string | undefined | null
    const safeSec = (typeof raw === 'number' && isFinite(raw) && raw > 0) ? raw
      : (typeof raw === 'string' && Number(raw) > 0) ? Number(raw) : 20
    const durationFrames = Math.round(safeSec * FPS) + TRANSITION_FRAMES
    cursor += durationFrames
    return { scene, start, durationFrames }
  })

  return (
    <AbsoluteFill style={{ background: '#08121E' }}>
      {timings.map(({ scene, start, durationFrames }) => {
        let Component: React.FC<{ scene: typeof scene; brand: typeof brand }> | null = null
        if (scene.component === 'MotivationScene') Component = MotivationScene
        else if (scene.component === 'IntroScene') Component = IntroScene
        else if (scene.component === 'OutroScene') Component = OutroScene

        if (!Component) return null
        return (
          <Sequence key={scene.id} from={start} durationInFrames={durationFrames}>
            <AbsoluteFill>
              <Component scene={scene} brand={brand} />
            </AbsoluteFill>
          </Sequence>
        )
      })}
      <BrandOverlay brand={brand} theme="dark" watermarkOpacity={0.10} />
    </AbsoluteFill>
  )
}

export function getMotivationTotalFrames(storyboard: StoryboardJSON): number {
  return (storyboard?.scenes ?? []).reduce((acc, s) => {
    const raw = s.duration_seconds as number | string | undefined | null
    const safeSec = (typeof raw === 'number' && isFinite(raw) && raw > 0) ? raw
      : (typeof raw === 'string' && Number(raw) > 0) ? Number(raw) : 20
    return acc + Math.round(safeSec * FPS) + TRANSITION_FRAMES
  }, 0)
}
