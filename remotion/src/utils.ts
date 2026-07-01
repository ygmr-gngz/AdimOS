import { StoryboardJSON } from './types'
import { FPS } from './brand'

export const TRANSITION_FRAMES = 15

export function getTotalFrames(storyboard: StoryboardJSON): number {
  return storyboard.scenes.reduce(
    (acc, s) => acc + Math.round(s.duration_seconds * FPS) + TRANSITION_FRAMES,
    0
  )
}
