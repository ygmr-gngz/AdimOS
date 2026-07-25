/**
 * MathFormula — LaTeX matematik ifadelerini KaTeX ile render eder.
 *
 * MathExpression tipindeki alanları kullanır:
 *   { latex, plain_text, spoken_text }
 *
 * Öncelik sırası:
 *   1. latex  → KaTeX HTML render
 *   2. plain_text → düz metin fallback
 *   3. Hiçbiri yoksa null
 */
import React from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { MathExpression } from '../types'

interface MathFormulaProps {
  expr?: MathExpression
  /** Sadece latex string geçmek isteyenler için */
  latex?: string
  plainText?: string
  fontSize?: number
  color?: string
  /** true → display mode (ortalanmış blok), false → inline */
  displayMode?: boolean
  className?: string
}

export function MathFormula({
  expr,
  latex,
  plainText,
  fontSize = 28,
  color = '#0B2A4A',
  displayMode = false,
}: MathFormulaProps) {
  const latexSrc  = expr?.latex  ?? latex   ?? null
  const plainSrc  = expr?.plain_text ?? plainText ?? null

  if (!latexSrc && !plainSrc) return null

  if (latexSrc) {
    try {
      const html = katex.renderToString(latexSrc, {
        throwOnError: false,
        displayMode,
        output: 'html',
        trust: false,
        strict: 'ignore',
      })
      return (
        <span
          style={{
            fontSize,
            color,
            lineHeight: displayMode ? 2 : 1.4,
            display: displayMode ? 'block' : 'inline',
          }}
          // eslint-disable-next-line react/no-danger
          dangerouslySetInnerHTML={{ __html: html }}
        />
      )
    } catch {
      // KaTeX parse hatası — plain_text'e düş
    }
  }

  return (
    <span
      style={{
        fontSize,
        color,
        fontFamily: 'monospace',
        lineHeight: 1.4,
      }}
    >
      {plainSrc ?? latexSrc}
    </span>
  )
}
