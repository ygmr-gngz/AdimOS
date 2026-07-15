import { StoryboardJSON } from './types'
import { FPS } from './brand'

export const TRANSITION_FRAMES = 15

// getCompositionsOnLambda inputProps:{} ile çağrıldığında storyboard undefined gelir;
// calculateMetadata'nın crash etmemesi için null-safe yapıldı.
export function getTotalFrames(storyboard: StoryboardJSON | undefined | null): number {
  if (!storyboard?.scenes?.length) return 900   // fallback: 30 sn
  return storyboard.scenes.reduce(
    (acc, s) => acc + Math.round(s.duration_seconds * FPS) + TRANSITION_FRAMES,
    0
  )
}
