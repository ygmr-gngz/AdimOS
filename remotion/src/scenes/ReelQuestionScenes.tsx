import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion'
import { Scene } from '../types'
import { LESSON_PALETTE } from '../brand'

const shell = { background: '#FFFEFB', color: LESSON_PALETTE.NAVY, fontFamily: 'Noto Sans, sans-serif' }

export function ReelQuestionScene({ scene }: { scene: Scene }) {
  const frame = useCurrentFrame()
  return <AbsoluteFill style={shell}>
    <div style={{ position: 'absolute', top: 210, left: 65, right: 65 }}>
      <div style={{ color: LESSON_PALETTE.TEAL, fontSize: 24, fontWeight: 900, letterSpacing: 3 }}>TEK SORUDA ÖĞREN</div>
      <div style={{ fontSize: 43, fontWeight: 900, lineHeight: 1.22, marginTop: 28 }}>{scene.question_text}</div>
    </div>
    <div style={{ position: 'absolute', top: 610, left: 65, right: 65, display: 'flex', flexDirection: 'column', gap: 20 }}>
      {(scene.options || []).map((option, index) => {
        const show = interpolate(frame, [18 + index * 12, 30 + index * 12], [0, 1], { extrapolateRight: 'clamp' })
        return <div key={option.label} style={{ opacity: show, transform: `translateX(${(1 - show) * 45}px)`, display: 'flex', alignItems: 'center', gap: 20, padding: '24px 28px', border: '3px solid #DDE5EA', borderRadius: 24, background: 'white' }}>
          <div style={{ width: 58, height: 58, borderRadius: 18, background: LESSON_PALETTE.NAVY, color: 'white', display: 'grid', placeItems: 'center', fontWeight: 900, fontSize: 28 }}>{option.label}</div>
          <div style={{ fontSize: 31, fontWeight: 700, lineHeight: 1.25 }}>{option.text}</div>
        </div>
      })}
    </div>
    <div style={{ position: 'absolute', bottom: 175, left: 0, right: 0, textAlign: 'center', fontSize: 28, color: LESSON_PALETTE.TEAL, fontWeight: 900, opacity: interpolate(frame, [75, 90], [0, 1], { extrapolateRight: 'clamp' }) }}>Cevabını seç…</div>
  </AbsoluteFill>
}

export function ReelAnswerScene({ scene }: { scene: Scene }) {
  const frame = useCurrentFrame()
  const { durationInFrames } = useVideoConfig()
  const correct = (scene.options || []).find(option => option.label === scene.correct_label)
  const reveal = interpolate(frame, [8, 26], [0, 1], { extrapolateRight: 'clamp' })
  return <AbsoluteFill style={shell}>
    <div style={{ position: 'absolute', top: 215, left: 70, right: 70, textAlign: 'center' }}>
      <div style={{ fontSize: 25, color: LESSON_PALETTE.GREEN, fontWeight: 900, letterSpacing: 3 }}>KURAL • DOĞRU CEVAP</div>
      <div style={{ margin: '35px auto', width: 150, height: 150, borderRadius: 50, background: LESSON_PALETTE.GREEN, color: 'white', display: 'grid', placeItems: 'center', fontSize: 82, fontWeight: 900, transform: `scale(${0.7 + reveal * 0.3})` }}>{scene.correct_label}</div>
      <div style={{ fontSize: 40, fontWeight: 900, lineHeight: 1.25 }}>{correct?.text}</div>
    </div>
    <div style={{ position: 'absolute', top: 700, left: 65, right: 65, padding: '38px 40px', borderRadius: 32, background: '#EAF7F3', borderLeft: `10px solid ${LESSON_PALETTE.TEAL}`, opacity: reveal }}>
      <div style={{ fontSize: 24, color: LESSON_PALETTE.TEAL, fontWeight: 900, marginBottom: 16 }}>MANTIĞI NEDİR?</div>
      <div style={{ fontSize: 35, lineHeight: 1.43, fontWeight: 700 }}>{scene.explanation}</div>
    </div>
    <div style={{ position: 'absolute', top: 1260, left: 85, right: 85, padding: '30px 35px', borderRadius: 28, background: LESSON_PALETTE.NAVY, color: 'white', textAlign: 'center', opacity: interpolate(frame, [Math.min(75, durationInFrames * .55), Math.min(95, durationInFrames * .72)], [0, 1], { extrapolateRight: 'clamp' }) }}>
      <div style={{ fontSize: 22, color: '#F7C66A', fontWeight: 900, letterSpacing: 2 }}>AKILDA KALSIN</div>
      <div style={{ fontSize: 36, lineHeight: 1.3, fontWeight: 900, marginTop: 12 }}>{scene.memory_hook}</div>
    </div>
  </AbsoluteFill>
}
