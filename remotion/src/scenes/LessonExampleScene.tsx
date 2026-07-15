import React from 'react'
import { AbsoluteFill, Audio, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { LESSON_PALETTE as L } from '../brand'
import { LessonWatermark, TopNavyBar, BottomGoldBar, BrandHandle } from '../components/LessonBrand'
import { Scene, BrandConfig } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

export const LessonExampleScene: React.FC<Props> = ({ scene, brand }) => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const rows = scene.journal_rows ?? []
  const steps = scene.calculation_steps ?? []

  const spr = (delay: number) =>
    spring({ frame: frame - delay, fps, config: { damping: 16, stiffness: 130, mass: 1 } })

  return (
    <AbsoluteFill style={{ background: L.BG, fontFamily: 'Lato' }}>
      <LessonWatermark />
      <TopNavyBar />
      <BottomGoldBar />
      <BrandHandle handle={brand.handle} />

      <AbsoluteFill style={{
        display: 'flex', flexDirection: 'column',
        padding: '72px 100px 60px', gap: 28,
      }}>
        {/* Başlık */}
        <div style={{
          opacity: spr(0), transform: `translateY(${(1 - spr(0)) * 16}px)`,
        }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 10,
            background: L.GOLD_DIM, border: `1px solid ${L.GOLD}`,
            borderRadius: 20, padding: '5px 18px', marginBottom: 16,
          }}>
            <span style={{ fontSize: 16 }}>📝</span>
            <span style={{ fontSize: 13, fontWeight: 800, color: L.NAVY, letterSpacing: 1.5, textTransform: 'uppercase' }}>
              ÖRNEK
            </span>
          </div>
          <h2 style={{
            fontSize: 38, fontWeight: 900, color: L.NAVY,
            fontFamily: brand.font_heading ?? 'Playfair Display',
            margin: 0, lineHeight: 1.2,
          }}>
            {scene.title}
          </h2>
        </div>

        {/* Senaryo kutusu */}
        {scene.question_text && (
          <div style={{
            opacity: spr(8), transform: `translateY(${(1 - spr(8)) * 14}px)`,
            background: 'rgba(43,127,224,0.07)', border: '1.5px solid rgba(43,127,224,0.25)',
            borderRadius: 14, padding: '20px 28px',
          }}>
            <p style={{
              fontSize: 19, color: L.DARK, lineHeight: 1.65,
              margin: 0,
            }}>
              {scene.question_text}
            </p>
          </div>
        )}

        {/* Yevmiye kaydı */}
        {rows.length > 0 && (
          <div style={{
            opacity: spr(14), transform: `translateY(${(1 - spr(14)) * 14}px)`,
          }}>
            <div style={{
              fontSize: 13, fontWeight: 800, color: L.GOLD,
              letterSpacing: 1.5, textTransform: 'uppercase',
              marginBottom: 10,
            }}>
              YEVMİYE KAYDI
            </div>
            <div style={{
              background: L.BG_CARD, border: `1.5px solid ${L.BORDER}`,
              borderRadius: 12, overflow: 'hidden',
            }}>
              {/* Başlık */}
              <div style={{
                display: 'flex', borderBottom: `1px solid ${L.BORDER}`,
                padding: '10px 20px', background: L.NAVY_DIM,
              }}>
                <span style={{ flex: '0 0 70px', fontSize: 11, fontWeight: 800, color: L.NAVY, letterSpacing: 1 }}>KOD</span>
                <span style={{ flex: 1, fontSize: 11, fontWeight: 800, color: L.NAVY, letterSpacing: 1 }}>HESAP ADI</span>
                <span style={{ width: 140, textAlign: 'right', fontSize: 11, fontWeight: 800, color: L.NAVY, letterSpacing: 1 }}>BORÇ</span>
                <span style={{ width: 140, textAlign: 'right', fontSize: 11, fontWeight: 800, color: L.NAVY, letterSpacing: 1 }}>ALACAK</span>
              </div>
              {rows.map((row, i) => {
                const rowIn = spr(18 + i * 4)
                return (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center',
                    padding: '11px 20px',
                    borderBottom: i < rows.length - 1 ? `1px solid ${L.BORDER}` : 'none',
                    background: i % 2 === 0 ? L.BG : L.BG_ALT,
                    opacity: rowIn, transform: `translateX(${(1 - rowIn) * 12}px)`,
                  }}>
                    <span style={{
                      flex: '0 0 70px', fontSize: 13, color: L.DIM, fontWeight: 700,
                      fontVariantNumeric: 'tabular-nums',
                    }}>
                      {row.code ?? ''}
                    </span>
                    <span style={{
                      flex: 1, fontSize: 16, color: L.DARK, fontWeight: row.indent ? 400 : 700,
                      paddingLeft: row.indent ? 24 : 0,
                    }}>
                      {row.name}
                    </span>
                    <span style={{
                      width: 140, textAlign: 'right', fontSize: 16,
                      color: row.debit ? L.NAVY : L.DIM,
                      fontWeight: row.debit ? 700 : 400,
                      fontVariantNumeric: 'tabular-nums',
                    }}>
                      {row.debit != null ? row.debit.toLocaleString('tr-TR') : '—'}
                    </span>
                    <span style={{
                      width: 140, textAlign: 'right', fontSize: 16,
                      color: row.credit ? L.NAVY : L.DIM,
                      fontWeight: row.credit ? 700 : 400,
                      fontVariantNumeric: 'tabular-nums',
                    }}>
                      {row.credit != null ? row.credit.toLocaleString('tr-TR') : '—'}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Hesaplama adımları */}
        {steps.length > 0 && (
          <div style={{
            display: 'flex', flexDirection: 'column', gap: 10,
            opacity: spr(14), transform: `translateY(${(1 - spr(14)) * 14}px)`,
          }}>
            {steps.map((step, i) => {
              const stepIn = spr(18 + i * 5)
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 16,
                  background: step.is_result ? L.NAVY_DIM : L.BG_CARD,
                  border: `1.5px solid ${step.is_result ? L.GOLD : L.BORDER}`,
                  borderRadius: 10, padding: '12px 20px',
                  opacity: stepIn, transform: `translateX(${(1 - stepIn) * 16}px)`,
                }}>
                  <span style={{ flex: 1, fontSize: 17, color: L.MID }}>{step.label}</span>
                  <span style={{
                    fontSize: step.is_result ? 22 : 19, fontWeight: step.is_result ? 900 : 700,
                    color: step.is_result ? L.NAVY : L.DARK,
                    fontVariantNumeric: 'tabular-nums',
                  }}>
                    {step.value}
                  </span>
                </div>
              )
            })}
          </div>
        )}

        {/* Açıklama */}
        {scene.explanation && (
          <div style={{
            opacity: spr(28), transform: `translateY(${(1 - spr(28)) * 12}px)`,
            background: L.GREEN_BG, border: `1px solid ${L.GREEN}`,
            borderRadius: 12, padding: '14px 22px',
          }}>
            <p style={{ fontSize: 17, color: '#166534', margin: 0, lineHeight: 1.55 }}>
              ✅ {scene.explanation}
            </p>
          </div>
        )}
      </AbsoluteFill>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </AbsoluteFill>
  )
}
