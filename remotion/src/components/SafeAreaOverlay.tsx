/**
 * SafeAreaOverlay — 9:16 Reels/Shorts güvenli alan kılavuzu
 * Sadece geliştirme/preview modunda kullanılır; render sırasında show=false olmalı.
 *
 * Güvenli alan sınırları (Instagram/YouTube Shorts standartları):
 *   - Üst / alt: %10
 *   - Sol / sağ: %5
 */
interface SafeAreaOverlayProps {
  show?: boolean
}

const UNSAFE_BG = 'rgba(220, 38, 38, 0.10)'
const BORDER_COLOR = 'rgba(248, 113, 113, 0.70)'
const LABEL_COLOR = 'rgba(248, 113, 113, 0.85)'

export function SafeAreaOverlay({ show = false }: SafeAreaOverlayProps) {
  if (!show) return null

  return (
    <div style={{
      position: 'absolute', inset: 0,
      pointerEvents: 'none', zIndex: 100,
    }}>
      {/* Unsafe: üst %10 */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '10%', background: UNSAFE_BG }} />
      {/* Unsafe: alt %10 */}
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: '10%', background: UNSAFE_BG }} />
      {/* Unsafe: sol %5 */}
      <div style={{ position: 'absolute', top: 0, left: 0, bottom: 0, width: '5%', background: UNSAFE_BG }} />
      {/* Unsafe: sağ %5 */}
      <div style={{ position: 'absolute', top: 0, right: 0, bottom: 0, width: '5%', background: UNSAFE_BG }} />

      {/* Güvenli alan çerçevesi */}
      <div style={{
        position: 'absolute',
        top: '10%', left: '5%', right: '5%', bottom: '10%',
        border: `2px dashed ${BORDER_COLOR}`,
        borderRadius: 4,
      }} />

      {/* Etiket */}
      <div style={{
        position: 'absolute',
        top: '10%', left: '5%',
        transform: 'translateY(calc(-100% - 4px))',
        fontSize: 18, fontWeight: 800,
        color: LABEL_COLOR,
        letterSpacing: '0.08em', textTransform: 'uppercase',
        fontFamily: 'sans-serif',
      }}>
        Güvenli Alan
      </div>
    </div>
  )
}
