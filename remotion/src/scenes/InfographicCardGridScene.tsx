/**
 * InfographicCardGridScene — Kavram kartları grid infografiği
 * Referans: "En Çok Sorulan Hesaplar" tarzı kart-grid sistemi
 * Kartlar sırayla spring animasyonuyla açılır
 */
import { spring, interpolate, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene, InfographicCard } from '../types'
import { PALETTE } from '../brand'

const ACCENT = PALETTE.ACCENT
const BG_DARK = PALETTE.BG_DARK
const BG_MID = PALETTE.BG_MID
const BG_CARD = PALETTE.BG_CARD

// Rozet renk haritası — kategoriye göre otomatik renk
const BADGE_COLORS: Record<string, string> = {
  'Aktif': '#22C55E',
  'Pasif': '#A78BFA',
  'Gelir': '#3B82F6',
  'Gider': '#EF4444',
  'Öz Kaynak': '#F59E0B',
  'default': ACCENT,
}

function getBadgeColor(category?: string): string {
  if (!category) return ACCENT
  return BADGE_COLORS[category] ?? ACCENT
}

interface CardItemProps {
  card: InfographicCard
  index: number
  frame: number
  fps: number
  cols: number
}

function CardItem({ card, index, frame, fps, cols }: CardItemProps) {
  const delay = 40 + index * 8
  const sc = spring({ frame, fps, config: { damping: 18, stiffness: 200 }, from: 0, to: 1, delay })
  const op = interpolate(frame, [delay, delay + 14], [0, 1], { extrapolateRight: 'clamp' })
  const badgeColor = getBadgeColor(card.category)

  return (
    <div style={{
      background: BG_CARD, border: `1px solid ${ACCENT}20`,
      borderRadius: 14, padding: '16px 18px',
      display: 'flex', flexDirection: 'column', gap: 8,
      transform: `scale(${sc})`, opacity: op,
      boxShadow: `0 4px 20px rgba(0,0,0,0.3)`,
      overflow: 'hidden', position: 'relative',
    }}>
      {/* Üst şerit — kategori rengi */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 3,
        background: badgeColor, opacity: 0.8,
      }} />

      {/* Başlık + rozet */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {card.icon && <span style={{ fontSize: cols <= 2 ? 20 : 16 }}>{card.icon}</span>}
          <span style={{
            fontSize: cols <= 2 ? 15 : 13, fontWeight: 700, color: '#FFFFFF', lineHeight: 1.3,
          }}>
            {card.title}
          </span>
        </div>
        {card.category && (
          <span style={{
            fontSize: 9, fontWeight: 800, letterSpacing: 1.5,
            color: '#fff', background: badgeColor,
            padding: '3px 8px', borderRadius: 10,
            flexShrink: 0, textTransform: 'uppercase' as const,
          }}>
            {card.category}
          </span>
        )}
      </div>

      {/* İçerik alanları */}
      {card.content && (
        <p style={{ fontSize: cols <= 2 ? 12 : 11, color: PALETTE.TEXT_MID, lineHeight: 1.55, margin: 0 }}>
          {card.content}
        </p>
      )}
      {card.rule && (
        <div style={{
          background: `${badgeColor}12`, border: `1px solid ${badgeColor}30`,
          borderRadius: 6, padding: '5px 8px',
        }}>
          <span style={{ fontSize: 10, color: badgeColor, fontWeight: 700 }}>📌 </span>
          <span style={{ fontSize: cols <= 2 ? 11 : 10, color: PALETTE.TEXT_MID }}>{card.rule}</span>
        </div>
      )}
      {card.example && (
        <div style={{ borderTop: `1px solid ${ACCENT}15`, paddingTop: 6 }}>
          <span style={{ fontSize: 9, fontWeight: 800, color: PALETTE.TEXT_DIM, letterSpacing: 1.5, textTransform: 'uppercase' as const }}>Örnek: </span>
          <span style={{ fontSize: 10, color: PALETTE.TEXT_MID, fontStyle: 'italic' }}>{card.example}</span>
        </div>
      )}
      {card.tip && (
        <div style={{ display: 'flex', gap: 5, alignItems: 'flex-start' }}>
          <span style={{ fontSize: 10, flexShrink: 0 }}>💡</span>
          <span style={{ fontSize: 10, color: PALETTE.ACCENT_LT, lineHeight: 1.5 }}>{card.tip}</span>
        </div>
      )}
    </div>
  )
}

interface Props { scene: Scene; brand: BrandConfig }

export function InfographicCardGridScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const isVertical = height > width

  const cards = scene.cards ?? []
  // Sütun sayısı: dikey=2, yatay kart sayısına göre 2-3-4
  const cols = isVertical ? 2 : (cards.length <= 4 ? 2 : cards.length <= 6 ? 3 : 4)

  const headerOpacity = interpolate(frame, [0, 24], [0, 1], { extrapolateRight: 'clamp' })
  const headerY = interpolate(frame, [0, 24], [-20, 0], { extrapolateRight: 'clamp' })
  const footerOpacity = interpolate(frame, [80, 100], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: BG_DARK,
      display: 'flex', flexDirection: 'column',
      fontFamily: brand.font_body, overflow: 'hidden', position: 'relative',
      padding: isVertical ? '28px 24px' : '32px 48px',
    }}>
      {/* Ambient glow */}
      <div style={{
        position: 'absolute', top: -60, left: '50%', transform: 'translateX(-50%)',
        width: 700, height: 300, borderRadius: '50%',
        background: `radial-gradient(ellipse, ${ACCENT}0A 0%, transparent 65%)`,
        pointerEvents: 'none',
      }} />

      {/* Üst çubuk */}
      <div style={{ height: 3, background: `linear-gradient(90deg, transparent, ${ACCENT}, transparent)`, marginBottom: isVertical ? 16 : 20, opacity: 0.7 }} />

      {/* Başlık alanı */}
      <div style={{
        opacity: headerOpacity, transform: `translateY(${headerY}px)`,
        marginBottom: isVertical ? 16 : 20,
        display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end',
      }}>
        <div>
          {scene.infographic_subtitle && (
            <p style={{ fontSize: 10, fontWeight: 800, color: ACCENT, letterSpacing: 3, textTransform: 'uppercase' as const, margin: '0 0 4px' }}>
              {scene.infographic_subtitle}
            </p>
          )}
          <h1 style={{
            fontSize: isVertical ? 22 : 28,
            fontFamily: brand.font_heading, fontWeight: 700,
            color: '#FFFFFF', margin: 0, lineHeight: 1.2,
          }}>
            {scene.infographic_title ?? scene.title ?? 'Temel Kavramlar'}
          </h1>
        </div>
        <span style={{ fontSize: 10, color: PALETTE.TEXT_DIM, letterSpacing: 1.5, flexShrink: 0 }}>
          @adimmusavir
        </span>
      </div>

      {/* Kart grid */}
      <div style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: `repeat(${cols}, 1fr)`,
        gap: isVertical ? 10 : 12,
        alignContent: 'start',
      }}>
        {cards.map((card, i) => (
          <CardItem key={i} card={card} index={i} frame={frame} fps={fps} cols={cols} />
        ))}
      </div>

      {/* Alt bilgi şeridi */}
      <div style={{
        marginTop: isVertical ? 12 : 16,
        paddingTop: 10,
        borderTop: `1px solid ${ACCENT}20`,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        opacity: footerOpacity,
      }}>
        <span style={{ fontSize: 9, color: PALETTE.TEXT_DIM, letterSpacing: 1 }}>
          {scene.footer_note ?? 'Eğitim amaçlı hazırlanmıştır.'}
        </span>
        <span style={{ fontSize: 9, color: ACCENT, fontWeight: 700, letterSpacing: 1.5 }}>
          ADIM MÜŞAVİR
        </span>
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
