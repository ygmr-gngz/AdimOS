import { StoryboardJSON } from './types'
import { FPS } from './brand'

export const TRANSITION_FRAMES = 15

// M9 — tek kaynak, tek davranış: geçersiz duration_seconds → hata, sessiz
// varsayılan yok. Önceden üç ayrı yerde üç farklı sessiz fallback vardı:
// getReelTotalFrames → 15s, estimateTotalFrames → 0, _sceneSummary → 0.
// Hepsi bunu kullanır; hiçbiri artık kendi varsayımını üretmez.
export function resolveSceneDurationSeconds(raw: unknown, sceneId: unknown): number {
  const n = typeof raw === 'number' ? raw : typeof raw === 'string' ? Number(raw) : NaN
  if (!isFinite(n) || n <= 0) {
    throw new Error(
      `duration_validation_failed: sahne ${sceneId ?? '?'} duration_seconds geçersiz ` +
      `(${JSON.stringify(raw)}) — sessiz varsayılan kullanılmıyor.`,
    )
  }
  return n
}

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
