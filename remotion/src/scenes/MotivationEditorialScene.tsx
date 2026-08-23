import { AbsoluteFill, Audio, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { BrandConfig, Scene } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

const NAVY = '#0B2A4A'
const TEAL = '#0F766E'
const ORANGE = '#F28C28'
const PAPER = '#FFFEFB'

function EditorialIllustration({ kind, smiling = false }: { kind: string; smiling?: boolean }) {
  if (smiling) {
    const label = kind === 'coffee' ? 'KAHVE SOĞUDU' : kind === 'calendar' ? 'BUGÜN BAŞLA'
      : kind === 'calculator' ? 'NETLER KONUŞSUN' : kind === 'checklist' ? 'BİR TIK DAHA'
      : 'UNVANA DOĞRU'
    return <svg width="640" height="420" viewBox="0 0 640 420" fill="none" aria-hidden="true">
      <path d="M80 340C180 370 455 372 560 340" stroke="#D8D2C5" strokeWidth="6" strokeLinecap="round" />
      {kind === 'coffee' ? <>
        <path d="M205 145H410V300C410 330 380 350 307 350C235 350 205 330 205 300V145Z" fill="#FFF0A9" stroke={NAVY} strokeWidth="8" />
        <path d="M410 185H475C520 185 520 270 410 270" stroke={NAVY} strokeWidth="8" />
        <path d="M255 110C225 70 285 65 255 25M330 110C300 70 360 65 330 25" stroke={TEAL} strokeWidth="7" strokeLinecap="round" />
      </> : kind === 'calculator' ? <>
        <rect x="205" y="55" width="235" height="300" rx="30" fill="#E8F0FF" stroke={NAVY} strokeWidth="8" />
        <rect x="245" y="95" width="155" height="58" rx="10" fill="#FFF" stroke={NAVY} strokeWidth="6" />
        {[0,1,2].map(r => [0,1,2].map(c => <circle key={`${r}-${c}`} cx={270+c*55} cy={205+r*55} r="16" fill={r === 2 && c === 2 ? ORANGE : TEAL} />))}
      </> : <>
        <rect x="150" y="65" width="340" height="280" rx="28" fill="#FAF7EF" stroke={NAVY} strokeWidth="8" />
        {[0,1,2].map(i => <g key={i}><rect x="205" y={125+i*62} width="30" height="30" rx="5" stroke={TEAL} strokeWidth="6" /><path d={`M212 ${140+i*62}l10 10 22-28`} stroke={ORANGE} strokeWidth="7" strokeLinecap="round" /><path d={`M270 ${140+i*62}h145`} stroke={NAVY} strokeWidth="7" strokeLinecap="round" /></g>)}
      </>}
      <rect x="170" y="350" width="300" height="52" rx="12" fill="#FFE279" stroke={NAVY} strokeWidth="5" />
      <text x="320" y="385" textAnchor="middle" fill={NAVY} fontSize="24" fontWeight="900">{label}</text>
    </svg>
  }
  const isTarget = kind.includes('Focus') || kind.includes('Outro')
  const isProblem = kind.includes('Problem') || kind.includes('Empathy')
  return (
    <svg width="640" height="420" viewBox="0 0 640 420" fill="none" aria-hidden="true">
      <path d="M86 90C160 55 242 68 320 112C401 70 487 60 554 92V340C477 313 401 320 320 362C240 320 162 313 86 340V90Z" fill="#FAF7EF" stroke={NAVY} strokeWidth="7" />
      <path d="M320 112V362M108 122C178 96 243 105 292 132M348 132C408 102 471 99 532 120" stroke={NAVY} strokeWidth="5" strokeLinecap="round" />
      {isTarget ? (
        <>
          <circle cx="430" cy="220" r="72" stroke={TEAL} strokeWidth="10" />
          <circle cx="430" cy="220" r="42" stroke={TEAL} strokeWidth="8" />
          <circle cx="430" cy="220" r="12" fill={ORANGE} />
          <path d="M500 144L436 213M500 144L496 180M500 144L464 148" stroke={NAVY} strokeWidth="10" strokeLinecap="round" />
        </>
      ) : (
        <>
          {[0, 1, 2].map(i => <rect key={i} x="150" y={158 + i * 58} width="30" height="30" rx="4" stroke={i === 0 || !isProblem ? TEAL : ORANGE} strokeWidth="6" />)}
          {!isProblem && <path d="M157 172L167 182L187 153" stroke={TEAL} strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />}
          {[0, 1, 2].map(i => <path key={i} d={`M202 ${173 + i * 58}H276`} stroke={NAVY} strokeWidth="6" strokeLinecap="round" />)}
          <path d="M370 255C408 235 451 208 486 166" stroke={TEAL} strokeWidth="10" strokeLinecap="round" />
          <path d="M462 169L489 162L484 190" stroke={TEAL} strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
        </>
      )}
      <path d="M72 365C190 388 452 389 568 365" stroke="#D8D2C5" strokeWidth="5" strokeLinecap="round" />
    </svg>
  )
}

export function MotivationEditorialScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const kind = String(scene.component ?? 'MotivationScene')
  const headline = scene.step_title ?? scene.title ?? scene.message ?? ''
  const body = scene.narration ?? scene.message ?? ''
  const kicker = kind.includes('Hook') ? 'BUGÜNÜN KÜÇÜK ADIMI'
    : kind.includes('Problem') ? 'BAŞLAMAYI KOLAYLAŞTIR'
    : kind.includes('Empathy') ? 'YALNIZ DEĞİLSİN'
    : kind.includes('Step') ? `ADIM ${scene.step_number ?? 1}`
    : kind.includes('Focus') ? 'HEDEFİNE ODAKLAN'
    : 'YARIN DEVAM ET'
  const enter = spring({ frame, fps, config: { damping: 20, stiffness: 150 } })
  const opacity = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: 'clamp' })
  const audioUrl = scene.audioUrl ?? scene.tts_url
  const smiling = scene.motivation_style === 'smiling'

  return (
    <AbsoluteFill style={{ background: PAPER, overflow: 'hidden', fontFamily: brand.font_body }}>
      <AbsoluteFill style={{
        backgroundImage: 'radial-gradient(rgba(11,42,74,0.035) 0.8px, transparent 0.8px)',
        backgroundSize: '18px 18px',
      }} />
      <div style={{ position: 'absolute', left: 92, right: 92, top: 260, opacity, transform: `translateY(${(1 - enter) * 45}px)` }}>
        <div style={{ color: TEAL, fontSize: 25, fontWeight: 800, letterSpacing: 3, marginBottom: 28 }}>{kicker}</div>
        <div style={{ width: 86, height: 7, borderRadius: 8, background: ORANGE, marginBottom: 30 }} />
        <div style={{ color: NAVY, fontFamily: brand.font_heading, fontWeight: 800, fontSize: headline.length > 66 ? 58 : 70, lineHeight: 1.13, letterSpacing: -1.5 }}>
          {headline}
        </div>
        {body && body !== headline && (
          <div style={{ color: '#334155', fontSize: body.length > 150 ? 34 : 39, lineHeight: 1.45, fontWeight: 500, marginTop: 34, maxWidth: 860 }}>
            {body}
          </div>
        )}
      </div>
      <div style={{ position: 'absolute', left: 220, bottom: 210, opacity, transform: `translateY(${(1 - enter) * 35}px)` }}>
        <EditorialIllustration kind={String(scene.illustration_kind ?? kind)} smiling={smiling} />
      </div>
      <div style={{ position: 'absolute', left: 92, bottom: 104, display: 'flex', alignItems: 'center', gap: 18, color: NAVY }}>
        <div style={{ width: 14, height: 14, borderRadius: 99, background: ORANGE }} />
        <span style={{ fontSize: 27, fontWeight: 800 }}>{smiling ? 'Gülümse, sonra bir soru daha.' : 'Küçük adım. Gerçek ilerleme.'}</span>
      </div>
      {audioUrl && <Audio src={audioUrl} />}
    </AbsoluteFill>
  )
}
