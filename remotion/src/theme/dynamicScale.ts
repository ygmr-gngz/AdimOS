/**
 * Kart tabanlı sahnelerin ortak dinamik ölçekleme motoru.
 *
 * AccountCardScene ve (A.4'te) kardeş bileşenler (JournalEntryScene,
 * TableScene, CommonMistakeScene, RuleBoxScene) aynı mekanizmayı paylaşır.
 *
 * Tek bir scale katsayısı hesaplanır (minScale <= scale <= 1) ve TÜM
 * ölçeklenebilir font boyutlarına aynı çarpan uygulanır — alanlar ayrı ayrı
 * küçülmez, oranlar korunur. Taban (min) altına inmeden içerik sığmıyorsa
 * LayoutOverflowError fırlatılır — sessiz kırpma yasak (v4 spesifikasyonu,
 * backend error registry'deki layout_overflow koduyla eşleşir).
 */

/**
 * Ölçüm eşikleri kart tipine göre farklıdır (2026-08-05 karar):
 *   Kart tabanlı sahneler (AccountCardScene, JournalEntryScene, TableScene,
 *   CommonMistakeScene) — açık zemin üzerinde beyaz kart, kart/gölge/kenarlık
 *   kendi başına kenar (edge) sinyali üretir: kenar >= 2.2 VE içerik >= %8.
 *   Düz koyu zeminli sahneler (RuleBoxScene) — kart kenarı katkısı YOK, bu
 *   yapısal bir fark (kusur değil, "koyu zemin" kasıtlı tasarım kararı).
 *   Yapay doku eklemek metriği tatmin etmek için tasarımı bozar — bunun
 *   yerine eşik bu sahne tipi için içerik >= %8 İLE SINIRLI, kenar eşiği
 *   uygulanmaz.
 */
export const CARD_BASED_THRESHOLDS = { edgeDensityMin: 2.2, contentPixelMin: 8 }
export const FLAT_BG_THRESHOLDS = { contentPixelMin: 8 }  // kenar eşiği yok — RuleBoxScene

export class LayoutOverflowError extends Error {
  constructor(message: string) {
    super(`layout_overflow: ${message}`)
    this.name = 'LayoutOverflowError'
  }
}

/** Metnin verilen genişlik ve font boyutunda kaç satıra sarılacağının kaba tahmini. */
export function estimateLines(text: string, fontSize: number, availableWidth: number): number {
  if (!text) return 0
  const avgCharWidth = fontSize * 0.52   // Noto Sans ortalama karakter genişliği katsayısı
  const charsPerLine = Math.max(1, Math.floor(availableWidth / avgCharWidth))
  return Math.max(1, Math.ceil(text.length / charsPerLine))
}

/** Bir font grubundaki (title/body/label/entry/tip) en kısıtlayıcı min/target oranı —
 *  tek scale hepsini birden çektiği için taban budur (en az küçülme payı olan alan). */
export function fieldMinScale(fields: { target: number; min: number }[]): number {
  return Math.max(...fields.map(f => f.min / f.target))
}

/**
 * estimateHeight(scale) verilen ölçekte tahmini toplam içerik yüksekliğini (px) döner.
 * 1'den minScale'e kadar 0.01 adımlarla arar, sığan EN BÜYÜK scale'i döner.
 * minScale'de bile sığmıyorsa LayoutOverflowError fırlatır.
 */
export function solveCardScale(
  estimateHeight: (scale: number) => number,
  availableHeight: number,
  minScale: number,
  componentName: string,
): number {
  if (estimateHeight(1) <= availableHeight) return 1
  const STEP = 0.01
  for (let s = 1 - STEP; s >= minScale; s -= STEP) {
    if (estimateHeight(s) <= availableHeight) return s
  }
  if (estimateHeight(minScale) <= availableHeight) return minScale
  throw new LayoutOverflowError(
    `${componentName}: içerik taban ölçekte (scale=${minScale.toFixed(2)}) bile sığmıyor ` +
    `(tahmini yükseklik=${Math.round(estimateHeight(minScale))}px, mevcut alan=${Math.round(availableHeight)}px). ` +
    `İçerik kısaltılmalı (prompt uzunluk kuralına bakın) — sessizce kırpılmaz.`
  )
}
