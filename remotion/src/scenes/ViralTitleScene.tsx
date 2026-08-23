import { AbsoluteFill, Audio, Easing, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion'
import { Scene } from '../types'

const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const }
const drawn = (p: number, length: number) => ({ strokeDasharray: length, strokeDashoffset: length * (1 - p) })

export function ViralTitleScene({ scene }: { scene: Scene }) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const p1 = interpolate(frame, [8, 38], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) })
  const p2 = interpolate(frame, [90, 130], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) })
  const pen = interpolate(frame, [155, 250], [0, 1], clamp)
  const note = spring({ frame: frame - 280, fps, config: { damping: 18, stiffness: 110 } })
  const titleSize = (scene.title?.length ?? 0) > 38 ? 49 : 58
  const subSize = (scene.subtitle?.length ?? 0) > 58 ? 47 : 56
  const audioUrl = scene.tts_url || scene.audio_url
  const audioSrc = audioUrl
    ? (/^https?:\/\//i.test(audioUrl) ? audioUrl : staticFile(audioUrl.replace(/^\//, '')))
    : null

  return <AbsoluteFill style={{ background: '#FFFEFB', color: '#0B2A4A', fontFamily: 'Noto Sans, sans-serif', overflow: 'hidden' }}>
    {audioSrc ? <Audio src={audioSrc} /> : null}
    <AbsoluteFill style={{ backgroundImage: 'radial-gradient(rgba(11,42,74,.05) .8px, transparent .8px)', backgroundSize: '22px 22px' }} />
    <div style={{ position: 'absolute', top: 245, left: 86, right: 86 }}>
      <div style={{ color: '#0F766E', fontSize: 23, fontWeight: 950, letterSpacing: 3 }}>UNVANA GİDEN YOL</div>
      <div style={{ fontSize: titleSize, fontWeight: 950, lineHeight: 1.13, marginTop: 34, opacity: p1 }}>{scene.title}</div>
      <div style={{ fontSize: subSize, fontWeight: 950, lineHeight: 1.15, marginTop: 22, opacity: p2, color: '#123C64' }}>{scene.subtitle}</div>
    </div>

    <svg viewBox="0 0 900 520" style={{ position: 'absolute', left: 90, top: 820, width: 900, height: 520 }}>
      <path d="M90 385H805" fill="none" stroke="#0B2A4A" strokeWidth="9" strokeLinecap="round" {...drawn(pen, 800)} />
      <path d="M190 385V235H350V385M350 385V165H520V385M520 385V95H690V385" fill="#E8F0FF" stroke="#0B2A4A" strokeWidth="8" strokeLinejoin="round" {...drawn(pen, 1800)} />
      <text x="270" y="325" textAnchor="middle" fill="#0B2A4A" fontSize="28" fontWeight="900" opacity={pen}>EMEK</text>
      <text x="435" y="270" textAnchor="middle" fill="#0B2A4A" fontSize="28" fontWeight="900" opacity={pen}>SINAV</text>
      <text x="605" y="210" textAnchor="middle" fill="#0B2A4A" fontSize="28" fontWeight="900" opacity={pen}>UNVAN</text>
      <path d="M155 335C285 255 380 210 565 105" fill="none" stroke="#F28C28" strokeWidth="12" strokeLinecap="round" {...drawn(pen, 650)} />
      <path d="M535 102L575 98L557 136" fill="none" stroke="#F28C28" strokeWidth="12" strokeLinecap="round" strokeLinejoin="round" {...drawn(pen, 120)} />
    </svg>

    <div style={{ position: 'absolute', left: 130, right: 130, top: 1370, padding: '31px 34px', border: '5px solid #0B2A4A', borderRadius: 8, background: '#FFE279', boxShadow: '13px 14px 0 rgba(11,42,74,.1)', opacity: note, transform: `rotate(${-1.5 + (1 - note) * -3}deg) scale(${.84 + note * .16})` }}>
      <div style={{ fontSize: 31, lineHeight: 1.35, fontWeight: 900, textAlign: 'center' }}>{scene.key_takeaway}</div>
    </div>
  </AbsoluteFill>
}
