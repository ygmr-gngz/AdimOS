import { StoryboardJSON } from './types'
import { FPS } from './brand'

export const TRANSITION_FRAMES = 15

// getCompositionsOnLambda inputProps:{} ile çağrıldığında storyboard undefined gelir;
// calculateMetadata'nın crash etmemesi için null-safe yapıldı.
// duration_seconds string veya undefined gelebilir (GPT çıktısı garantisiz) — NaN koruması eklendi.
export function getTotalFrames(storyboard: StoryboardJSON | undefined | null): number {
  if (!storyboard?.scenes?.length) return 900   // fallback: 30 sn
  return storyboard.scenes.reduce((acc, s) => {
    const raw = s.duration_seconds as number | string | undefined | null
    const sec = (typeof raw === 'number' && isFinite(raw) && raw > 0)
      ? raw
      : (typeof raw === 'string' && Number(raw) > 0)
        ? Number(raw)
        : 30   // güvenli fallback: 30 sn/sahne
    return acc + Math.round(sec * FPS) + TRANSITION_FRAMES
  }, 0)
}
