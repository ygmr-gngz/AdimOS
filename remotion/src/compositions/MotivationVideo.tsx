/**
 * MotivationVideo — Kısa motivasyon videosu composition (15-30 sn)
 * 9:16 Shorts/Reels formatı
 */
import { AbsoluteFill, Sequence } from 'remotion'
import { StoryboardJSON } from '../types'
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
    const durationFrames = Math.round(scene.duration_seconds * FPS) + TRANSITION_FRAMES
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
    </AbsoluteFill>
  )
}

export function getMotivationTotalFrames(storyboard: StoryboardJSON): number {
  return storyboard.scenes.reduce(
    (acc, s) => acc + Math.round(s.duration_seconds * FPS) + TRANSITION_FRAMES,
    0
  )
}
