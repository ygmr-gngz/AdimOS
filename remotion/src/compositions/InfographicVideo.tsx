/**
 * InfographicVideo — İnfografik içerikten animasyonlu Reels/Shorts
 * Kartlar sırayla açılır, seslendirme her kartı anlatır, sonda tam infografik
 * Hem 9:16 (Reels) hem 16:9 (YouTube) destekler
 */
import { AbsoluteFill, Sequence } from 'remotion'
import { StoryboardJSON } from '../types'
import { FPS } from '../brand'
import { TRANSITION_FRAMES } from '../utils'
import { InfographicCardGridScene } from '../scenes/InfographicCardGridScene'
import { InfographicComparisonScene } from '../scenes/InfographicComparisonScene'
import { InfographicProcessScene } from '../scenes/InfographicProcessScene'
import { IntroScene } from '../scenes/IntroScene'
import { OutroScene } from '../scenes/OutroScene'

interface Props { storyboard: StoryboardJSON }

const SCENE_MAP: Record<string, React.FC<any>> = {
  InfographicCardGridScene,
  InfographicComparisonScene,
  InfographicProcessScene,
  IntroScene,
  OutroScene,
}

export function InfographicVideo({ storyboard }: Props) {
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
        const Component = SCENE_MAP[scene.component]
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

export function getInfographicTotalFrames(storyboard: StoryboardJSON): number {
  return storyboard.scenes.reduce(
    (acc, s) => acc + Math.round(s.duration_seconds * FPS) + TRANSITION_FRAMES,
    0
  )
}
