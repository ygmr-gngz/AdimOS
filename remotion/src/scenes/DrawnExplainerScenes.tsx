import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { Scene } from '../types'
import { LESSON_PALETTE } from '../brand'

const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const }
const reveal = (frame: number, from: number, span = 20) => interpolate(frame, [from, from + span], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) })
const drawn = (progress: number, length: number) => ({ strokeDasharray: length, strokeDashoffset: length * (1 - progress) })

const GridPaper = () => <AbsoluteFill style={{
  backgroundColor: '#FFFEFB',
  backgroundImage: 'linear-gradient(rgba(11,42,74,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(11,42,74,.05) 1px, transparent 1px)',
  backgroundSize: '42px 42px',
}} />

export function DrawnAccountingExampleScene({ scene }: { scene: Scene }) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const ali = spring({ frame: frame - 15, fps, config: { damping: 16, stiffness: 95 } })
  // Zamanlama seslendirmeyi izler: kişi → girdiler → üretim → çıktılar → doğrulama.
  const inputDraw = reveal(frame, 110, 55)
  const factoryDraw = reveal(frame, 285, 55)
  const outputDraw = reveal(frame, 470, 55)
  const equation = reveal(frame, 710, 40)
  const inputMove = interpolate(frame, [220, 355], [0, 1], clamp)
  const outputMove = interpolate(frame, [570, 700], [0, 1], clamp)

  return <AbsoluteFill style={{ color: LESSON_PALETTE.NAVY, fontFamily: 'Noto Sans, sans-serif' }}>
    <GridPaper />
    <div style={{ position: 'absolute', top: 195, left: 70, right: 70 }}>
      <div style={{ color: LESSON_PALETTE.TEAL, fontSize: 23, fontWeight: 900, letterSpacing: 3 }}>ALİ'NİN FABRİKASI • BASİT ÖRNEK</div>
      <div style={{ fontSize: 55, fontWeight: 950, lineHeight: 1.08, marginTop: 22 }}>Miktar dengesi nasıl kurulur?</div>
    </div>

    <svg viewBox="0 0 1080 1050" style={{ position: 'absolute', top: 440, left: 0, width: 1080, height: 1050 }}>
      {/* Ali — çizgiler gerçekten çizilir */}
      <g opacity={ali} transform={`translate(0 ${(1 - ali) * 35})`} fill="none" stroke="#0B2A4A" strokeWidth="8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="135" cy="205" r="48" fill="#FFF0A9" />
        <path d="M105 198 Q135 225 165 198 M115 180 l12 -8 M143 172 l14 8 M135 253 L135 390 M135 290 L70 345 M135 290 L205 335 M135 390 L85 490 M135 390 L190 490" {...drawn(reveal(frame, 15, 55), 900)} />
        <text x="135" y="555" textAnchor="middle" fill="#0B2A4A" stroke="none" fontSize="34" fontWeight="900">Ali</text>
      </g>

      {/* Girdi kartları ve fabrikaya giden ok */}
      <g opacity={inputDraw}>
        <rect x="245" y="95" width="245" height="115" rx="24" fill="#DDF5F0" stroke="#0D9488" strokeWidth="6" />
        <text x="367" y="142" textAnchor="middle" fill="#0B2A4A" fontSize="25" fontWeight="800">DBYM</text>
        <text x="367" y="183" textAnchor="middle" fill="#0B2A4A" fontSize="34" fontWeight="950">10.000</text>
        <rect x="245" y="240" width="245" height="125" rx="24" fill="#E8F0FF" stroke="#2B7FE0" strokeWidth="6" />
        <text x="367" y="286" textAnchor="middle" fill="#0B2A4A" fontSize="23" fontWeight="800">Yeni Başlanan</text>
        <text x="367" y="332" textAnchor="middle" fill="#0B2A4A" fontSize="34" fontWeight="950">15.000</text>
        <path d="M430 425 C520 425 510 360 585 360" fill="none" stroke="#0D9488" strokeWidth="11" {...drawn(inputDraw, 500)} />
        <path d="M566 338 L592 360 L565 382" fill="none" stroke="#0D9488" strokeWidth="11" {...drawn(inputDraw, 100)} />
        <circle cx={430 + inputMove * 145} cy={425 - Math.sin(inputMove * Math.PI) * 65} r="20" fill="#F59E0B" />
      </g>

      {/* Fabrika */}
      <g opacity={factoryDraw} stroke="#0B2A4A" strokeWidth="8" strokeLinejoin="round">
        <path d="M585 280 L585 560 L800 560 L800 360 L735 405 L735 350 L670 405 L670 280 Z" fill="#FFF0A9" {...drawn(factoryDraw, 1500)} />
        <path d="M620 280 L620 190 L680 190 L680 280" fill="#D8E7F8" {...drawn(factoryDraw, 500)} />
        <circle cx="693" cy="478" r="55" fill="#FFF" {...drawn(factoryDraw, 400)} />
        <path d="M693 438 V518 M653 478 H733" fill="none" {...drawn(factoryDraw, 300)} />
        <text x="693" y="625" textAnchor="middle" fill="#0B2A4A" stroke="none" fontSize="29" fontWeight="900">ÜRETİM SÜRECİ</text>
      </g>

      {/* Çıktılar */}
      <g opacity={outputDraw}>
        <path d="M805 425 C865 425 860 320 915 320" fill="none" stroke="#F59E0B" strokeWidth="11" {...drawn(outputDraw, 450)} />
        <path d="M895 298 L922 320 L895 342" fill="none" stroke="#F59E0B" strokeWidth="11" {...drawn(outputDraw, 100)} />
        <circle cx={805 + outputMove * 105} cy={425 - Math.sin(outputMove * Math.PI) * 105} r="20" fill="#0D9488" />
        <rect x="835" y="90" width="220" height="118" rx="24" fill="#E5F6D8" stroke="#3A8D4D" strokeWidth="6" />
        <text x="945" y="136" textAnchor="middle" fill="#0B2A4A" fontSize="22" fontWeight="800">Tamamlanan</text>
        <text x="945" y="181" textAnchor="middle" fill="#0B2A4A" fontSize="32" fontWeight="950">20.000</text>
        <rect x="835" y="235" width="220" height="118" rx="24" fill="#FFE7D4" stroke="#E07828" strokeWidth="6" />
        <text x="945" y="281" textAnchor="middle" fill="#0B2A4A" fontSize="24" fontWeight="800">DSYM</text>
        <text x="945" y="326" textAnchor="middle" fill="#0B2A4A" fontSize="32" fontWeight="950">5.000</text>
      </g>

      {/* Formül sonucu */}
      <g opacity={equation} transform={`translateY(${(1 - equation) * 35})`}>
        <rect x="120" y="720" width="840" height="205" rx="32" fill="#FFE279" stroke="#0B2A4A" strokeWidth="7" />
        <text x="540" y="790" textAnchor="middle" fill="#0B2A4A" fontSize="28" fontWeight="900">GİRENLER = ÇIKANLAR</text>
        <text x="540" y="855" textAnchor="middle" fill="#0B2A4A" fontSize="37" fontWeight="950">10.000 + 15.000 = 20.000 + 5.000</text>
        <text x="540" y="902" textAnchor="middle" fill="#0D9488" fontSize="28" fontWeight="900">25.000 = 25.000 ✓</text>
      </g>
    </svg>
    <div style={{ position: 'absolute', bottom: 165, left: 90, right: 90, textAlign: 'center', fontSize: 27, fontWeight: 900, color: LESSON_PALETTE.TEAL, opacity: equation }}>Formülü değil, akışı hatırla.</div>
  </AbsoluteFill>
}

export function DrawnQuestionExplainerScene({ scene }: { scene: Scene }) {
  const frame = useCurrentFrame()
  const options = scene.options || []
  const question = reveal(frame, 5, 25)
  // Önce soru okunur, ardından ipucu, eleme ve açıklama sırayla gelir.
  const clue = reveal(frame, 235, 35)
  const eliminate = reveal(frame, 410, 55)
  const answer = reveal(frame, 590, 40)
  const why = reveal(frame, 710, 40)

  return <AbsoluteFill style={{ color: LESSON_PALETTE.NAVY, fontFamily: 'Noto Sans, sans-serif' }}>
    <GridPaper />
    <div style={{ position: 'absolute', top: 190, left: 68, right: 68, opacity: question }}>
      <div style={{ color: LESSON_PALETTE.TEAL, fontSize: 23, fontWeight: 900, letterSpacing: 3 }}>TEK SORUDA ÖĞREN</div>
      <div style={{ fontSize: 43, fontWeight: 950, lineHeight: 1.2, marginTop: 24 }}>{scene.question_text}</div>
      <div style={{ height: 8, width: `${clue * 74}%`, background: '#FFE279', borderRadius: 6, marginTop: 16 }} />
      <div style={{ color: '#9A6A00', fontSize: 24, fontWeight: 900, marginTop: 10, opacity: clue }}>İpucu: “üretime giren” ifadesine odaklan.</div>
    </div>

    <div style={{ position: 'absolute', top: 595, left: 65, right: 65, display: 'flex', flexDirection: 'column', gap: 16 }}>
      {options.map((option, index) => {
        const show = reveal(frame, 55 + index * 24, 18)
        const isCorrect = option.label === scene.correct_label
        const wrongFade = !isCorrect ? eliminate : 0
        return <div key={option.label} style={{
          position: 'relative', display: 'flex', alignItems: 'center', gap: 18, padding: '21px 25px',
          borderRadius: 22, border: `4px solid ${isCorrect && answer ? '#22C55E' : '#DCE5E9'}`,
          background: isCorrect && answer ? '#EAF9EF' : '#FFF', opacity: show * (1 - wrongFade * .45),
          transform: `translateX(${(1 - show) * 35}px)`,
        }}>
          <div style={{ width: 55, height: 55, borderRadius: 17, display: 'grid', placeItems: 'center', background: isCorrect && answer ? '#22C55E' : '#0B2A4A', color: '#FFF', fontSize: 27, fontWeight: 950 }}>{option.label}</div>
          <div style={{ fontSize: 30, fontWeight: 800 }}>{option.text}</div>
          {!isCorrect && <svg viewBox="0 0 700 80" style={{ position: 'absolute', left: 90, right: 20, top: 12, height: 70, opacity: eliminate }}>
            <path d="M0 42 Q250 25 650 45" fill="none" stroke="#E05858" strokeWidth="7" strokeLinecap="round" {...drawn(eliminate, 700)} />
          </svg>}
        </div>
      })}
    </div>

    <div style={{ position: 'absolute', top: 1325, left: 90, right: 90, padding: '30px 34px', borderRadius: 28, background: '#FFE279', border: '4px solid #0B2A4A', opacity: why, transform: `translateY(${(1 - why) * 35}px)` }}>
      <div style={{ fontSize: 22, fontWeight: 950, color: '#8A6300', letterSpacing: 2 }}>NEDEN?</div>
      <div style={{ fontSize: 32, lineHeight: 1.34, fontWeight: 850, marginTop: 10 }}>{scene.explanation}</div>
      <div style={{ fontSize: 28, color: LESSON_PALETTE.TEAL, fontWeight: 950, marginTop: 18 }}>Akılda kalsın: {scene.memory_hook}</div>
    </div>
  </AbsoluteFill>
}
