import { AbsoluteFill, Audio, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from 'remotion'
import { BrandConfig, Scene, VisualNode } from '../types'
import { BrandCornerLogo, BrandHandle, BottomGoldBar, LessonWatermark, TopNavyBar } from '../components/LessonBrand'

const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const }
const reveal = (frame: number, start: number, span = 26) => interpolate(frame, [start, start + span], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) })
const draw = (p: number, length: number) => ({ strokeDasharray: length, strokeDashoffset: length * (1 - p) })

function IconDrawing({ kind, x, progress, frame }: { kind: VisualNode['kind']; x: number; progress: number; frame: number }) {
  const smoke = Math.sin(frame / 17) * 8
  const common = { fill: '#FFFDF7', stroke: '#0B2A4A', strokeWidth: 7, strokeLinejoin: 'round' as const, ...draw(progress, 1200) }
  if (kind === 'factory') return <g transform={`translate(${x - 85} 0)`}>
    <path d="M0 250V85H55V150L115 112V158L175 118V250Z" {...common} fill="#FFF0A9" />
    <path d={`M20 70Q${40 + smoke} 35 22 5M53 70Q${77 - smoke} 35 60 0`} fill="none" stroke="#94A3B8" strokeWidth="7" strokeLinecap="round" opacity={progress} />
    <circle cx="92" cy="205" r="29" {...common} fill="#FFF" />
  </g>
  if (kind === 'document') return <g transform={`translate(${x - 72} 20)`}>
    <path d="M0 0H105L145 40V225H0Z M105 0V40H145" {...common} fill="#E8F0FF" />
    <path d="M28 82H116M28 120H116M28 158H92" fill="none" stroke="#0F766E" strokeWidth="7" strokeLinecap="round" {...draw(progress, 400)} />
  </g>
  if (kind === 'money') return <g transform={`translate(${x - 82} 55)`}>
    <rect x="0" y="0" width="164" height="110" rx="15" {...common} fill="#DDF5F0" />
    <circle cx="82" cy="55" r="28" {...common} fill="#FFF" />
    <path d="M70 55H94" stroke="#F28C28" strokeWidth="8" strokeLinecap="round" {...draw(progress, 80)} />
  </g>
  if (kind === 'person') return <g transform={`translate(${x - 60} 15)`} fill="none" stroke="#0B2A4A" strokeWidth="8" strokeLinecap="round">
    <circle cx="60" cy="48" r="40" fill="#FFF0A9" />
    <path d="M60 90V180M60 115L10 150M60 115L112 150M60 180L18 235M60 180L105 235" {...draw(progress, 700)} />
  </g>
  if (kind === 'scale') return <g transform={`translate(${x - 90} 20)`} fill="none" stroke="#0B2A4A" strokeWidth="8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M90 15V210M22 65H158M90 210H32M90 210H148M22 65L0 145H52ZM158 65L128 145H180Z" {...draw(progress, 1200)} />
  </g>
  return <g transform={`translate(${x - 80} 35)`}>
    <rect width="160" height="160" rx="28" {...common} fill="#FFE279" />
    <path d="M40 52H120M40 82H120M40 112H92" fill="none" stroke="#0B2A4A" strokeWidth="8" strokeLinecap="round" {...draw(progress, 350)} />
  </g>
}

export function LessonDrawnExplainerScene({ scene, brand }: { scene: Scene; brand: BrandConfig }) {
  const frame = useCurrentFrame()
  const { durationInFrames } = useVideoConfig()
  const nodes = (scene.visual_nodes ?? []).slice(0, 4)
  const titleSize = (scene.title?.length ?? 0) > 55 ? 39 : 47
  const xs = nodes.map((_, i) => 255 + i * (1410 / Math.max(1, nodes.length - 1)))
  return <AbsoluteFill style={{ background: '#FFFEFB', color: '#0B2A4A', fontFamily: brand.font_body, overflow: 'hidden' }}>
    <AbsoluteFill style={{ backgroundImage: 'linear-gradient(rgba(11,42,74,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(11,42,74,.035) 1px, transparent 1px)', backgroundSize: '38px 38px' }} />
    <LessonWatermark opacity={0.025} /><TopNavyBar /><BottomGoldBar /><BrandHandle handle={brand.handle} /><BrandCornerLogo logoUrl={brand.logo_url} handle={brand.handle} corner="top-right" />
    <div style={{ position: 'absolute', top: 82, left: 105, right: 105 }}>
      <div style={{ color: '#0F766E', fontSize: 18, fontWeight: 900, letterSpacing: 3 }}>ÇİZEREK ANLA</div>
      <div style={{ fontSize: titleSize, fontWeight: 950, lineHeight: 1.13, marginTop: 13 }}>{scene.title}</div>
      {scene.definition && <div style={{ fontSize: 22, color: '#475569', lineHeight: 1.45, marginTop: 13, maxWidth: 1380 }}>{scene.definition}</div>}
    </div>
    <svg viewBox="0 0 1920 620" style={{ position: 'absolute', left: 0, top: 315, width: 1920, height: 620 }}>
      {nodes.slice(0, -1).map((_, i) => {
        const p = reveal(frame, durationInFrames * (0.20 + i * 0.17), 45); const x1 = xs[i] + 105, x2 = xs[i + 1] - 115
        return <g key={`arrow-${i}`}><path d={`M${x1} 210 C${x1 + 75} 150 ${x2 - 75} 150 ${x2} 210`} fill="none" stroke="#F28C28" strokeWidth="11" strokeLinecap="round" {...draw(p, 650)} /><path d={`M${x2 - 28} 186L${x2} 210L${x2 - 30} 232`} fill="none" stroke="#F28C28" strokeWidth="11" strokeLinecap="round" strokeLinejoin="round" {...draw(p, 120)} /></g>
      })}
      {nodes.map((node, i) => { const p = reveal(frame, durationInFrames * (0.08 + i * 0.17), 45); return <g key={`${node.label}-${i}`} opacity={p}><IconDrawing kind={node.kind} x={xs[i]} progress={p} frame={frame} /><text x={xs[i]} y="330" textAnchor="middle" fill="#0B2A4A" fontSize="29" fontWeight="900">{node.label}</text>{node.detail && <text x={xs[i]} y="370" textAnchor="middle" fill="#475569" fontSize="20" fontWeight="700">{node.detail}</text>}</g> })}
    </svg>
    {scene.key_point && <div style={{ position: 'absolute', left: 260, right: 260, bottom: 95, padding: '22px 32px', background: '#FFE279', border: '4px solid #0B2A4A', borderRadius: 9, textAlign: 'center', fontSize: 27, fontWeight: 900, opacity: reveal(frame, durationInFrames * 0.78, 35), transform: 'rotate(-.6deg)' }}>{scene.key_point}</div>}
    {scene.tts_url && <Audio src={/^(https?:|data:)/.test(scene.tts_url) ? scene.tts_url : staticFile(scene.tts_url.replace(/^\//, ''))} />}
  </AbsoluteFill>
}
