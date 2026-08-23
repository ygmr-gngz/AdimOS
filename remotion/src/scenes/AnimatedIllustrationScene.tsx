import { AbsoluteFill, Img, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from 'remotion'
import { Scene } from '../types'
import { LESSON_PALETTE } from '../brand'

export function AnimatedIllustrationScene({ scene }: { scene: Scene }) {
  const frame = useCurrentFrame()
  const { durationInFrames } = useVideoConfig()
  const draw = interpolate(frame, [3, Math.min(55, durationInFrames * .34)], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic),
  })
  const noteReveal = interpolate(frame, [38, 64], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
  const settle = interpolate(frame, [30, durationInFrames], [0, 1], { extrapolateRight: 'clamp' })
  const rawUrl = scene.illustration_url || scene.visual_url
  if (!rawUrl) throw new Error(`animated_illustration_missing: scene=${scene.id ?? '?'}`)
  const url = /^(https?:|data:)/.test(rawUrl) ? rawUrl : staticFile(rawUrl.replace(/^\//, ''))
  const title = scene.title || scene.infographic_title || 'Konunun can alıcı noktası'
  const takeaway = scene.key_takeaway || scene.exam_tip || scene.common_mistake || title
  const titleSize = title.length > 42 ? 45 : title.length > 28 ? 51 : 57

  return <AbsoluteFill style={{
    backgroundColor: '#FFFEFB', color: LESSON_PALETTE.NAVY, fontFamily: 'Noto Sans, sans-serif',
    backgroundImage: 'linear-gradient(rgba(11,42,74,.045) 1px, transparent 1px), linear-gradient(90deg, rgba(11,42,74,.045) 1px, transparent 1px)',
    backgroundSize: '42px 42px', overflow: 'hidden',
  }}>
    <div style={{ position: 'absolute', top: 205, left: 74, right: 74 }}>
      <div style={{ display: 'inline-block', padding: '11px 18px', borderRadius: 999, background: '#FFF0A9', color: '#735C00', fontSize: 21, fontWeight: 900, letterSpacing: 2 }}>
        {scene.save_label || 'HIZLI BİLGİ • KAYDET'}
      </div>
      <div style={{ fontSize: titleSize, lineHeight: 1.08, fontWeight: 950, marginTop: 24, maxWidth: 850 }}>{title}</div>
    </div>

    <div style={{ position: 'absolute', top: 465, left: 35, width: 1010, height: 1000, overflow: 'hidden' }}>
      {[0, 1, 2].map((band) => {
        const offset = Math.sin(frame / (18 + band * 4)) * (12 - settle * 7) * (band === 1 ? -1 : 1)
        return <div key={band} style={{ position: 'absolute', left: 0, right: 0, top: `${band * 33.333}%`, height: '33.5%', overflow: 'hidden', clipPath: `inset(0 ${100 - draw * 100}% 0 0)` }}>
          <Img src={url} style={{ position: 'absolute', width: '100%', height: 1000, top: `${-band * 333.33}px`, objectFit: 'contain', transform: `translateX(${offset}px) scale(1.025)` }} />
        </div>
      })}
      <svg viewBox="0 0 1010 1000" style={{ position: 'absolute', inset: 0 }}>
        <path d="M130 810 Q300 750 445 805 T850 785" fill="none" stroke="#F59E0B" strokeWidth="8" strokeLinecap="round" strokeDasharray="1200" strokeDashoffset={1200 * (1 - draw)} />
        <path d="M145 210 Q220 125 315 190" fill="none" stroke="#0D9488" strokeWidth="7" strokeLinecap="round" strokeDasharray="500" strokeDashoffset={500 * (1 - draw)} />
      </svg>
    </div>

    <div style={{
      position: 'absolute', left: 125, right: 125, top: 1090, minHeight: 245,
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '34px 42px',
      background: '#FFE279', border: '4px solid #0B2A4A', boxShadow: '12px 14px 0 rgba(11,42,74,.14)',
      transform: `rotate(-1.2deg) scale(${.92 + noteReveal * .08})`, opacity: noteReveal,
    }}>
      <div style={{ fontSize: takeaway.length > 80 ? 31 : 37, lineHeight: 1.28, fontWeight: 900, textAlign: 'center', maxWidth: 760 }}>{takeaway}</div>
    </div>

    <div style={{ position: 'absolute', top: 1450, left: 150, right: 150, textAlign: 'center', color: LESSON_PALETTE.TEAL, fontSize: 24, fontWeight: 900, letterSpacing: 1, opacity: interpolate(frame, [70, 90], [0, 1], { extrapolateRight: 'clamp' }) }}>
      Tek konu • Tek kural • Net çözüm
    </div>
  </AbsoluteFill>
}
