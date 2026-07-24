/**
 * InfographicVideo — İnfografik içerikten animasyonlu Reels/Shorts
 * Kartlar sırayla açılır, seslendirme her kartı anlatır, sonda tam infografik
 * Hem 9:16 (Reels) hem 16:9 (YouTube) destekler
 */
import { AbsoluteFill, Sequence } from 'remotion'
import { StoryboardJSON } from '../types'
import { BrandOverlay } from '../components/BrandOverlay'
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
    // NaN koruması — duration_seconds string veya undefined gelebilir
    const raw = scene.duration_seconds as number | string | undefined | null
    const safeSec = (typeof raw === 'number' && isFinite(raw) && raw > 0) ? raw
      : (typeof raw === 'string' && Number(raw) > 0) ? Number(raw) : 15
    const durationFrames = Math.round(safeSec * FPS) + TRANSITION_FRAMES
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
      <BrandOverlay brand={brand} theme="dark" watermarkOpacity={0.10} />
    </AbsoluteFill>
  )
}

export function getInfographicTotalFrames(storyboard: StoryboardJSON): number {
  return storyboard.scenes.reduce(
    (acc, s) => acc + Math.round(s.duration_seconds * FPS) + TRANSITION_FRAMES,
    0
  )
}
