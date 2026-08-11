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
// Ken Burns — motivasyon sahnesi foto arka planına yavaş zoom. Yön scene.id'nin
// hash'inden belirlenir (çift→zoom-out, tek→zoom-in), böylece art arda sahnelerde
// yön dönüşümlü olur ve tüm sahneler aynı yönde "kayıp gitmiyor" hissi vermez.
export function kenBurnsScale(
  frame: number,
  durationSeconds: number,
  fps: number,
  seed: string,
): number {
  const totalFrames = Math.max(1, Math.round(durationSeconds * fps))
  const progress = Math.min(1, Math.max(0, frame / totalFrames))
  let hash = 0
  for (let i = 0; i < seed.length; i++) hash = (hash * 31 + seed.charCodeAt(i)) >>> 0
  const zoomOut = hash % 2 === 0
  return zoomOut ? 1.14 - progress * 0.08 : 1.06 + progress * 0.08
}

export interface SceneTiming {
  scene: StoryboardJSON['scenes'][number]
  start: number
  durationFrames: number
}

// EducationalReel120.tsx'in sahne-kürsör hesabıyla AYNI formül — tek kaynak.
// Card-still özelliği (2026-08-08) bunu composition DIŞINDAN (server/index.ts,
// Lambda still render öncesi hangi frame'in hangi sahnenin ortası olduğunu
// bulmak için) de kullanıyor; iki bağımsız kopya olursa still yanlış sahneden
// alınır — bu sınıf hatayı bu session zaten birkaç kez gördük.
export function getSceneTimings(scenes: StoryboardJSON['scenes']): SceneTiming[] {
  let cursor = 0
  return scenes.map(scene => {
    const start = cursor
    const safeSec = resolveSceneDurationSeconds(scene.duration_seconds, scene.id)
    const durationFrames = Math.max(TRANSITION_FRAMES + 1, Math.round(safeSec * FPS) + TRANSITION_FRAMES)
    cursor += durationFrames
    return { scene, start, durationFrames }
  })
}

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
