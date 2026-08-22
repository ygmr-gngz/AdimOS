import { AbsoluteFill } from 'remotion'
import type { Scene, StoryboardJSON } from '../types'
import { T } from '../theme/tokens'

interface Props { storyboard: StoryboardJSON }

function firstText(scene: Scene, keys: string[]): string {
  for (const key of keys) {
    const value = (scene as unknown as Record<string, unknown>)[key]
    if (typeof value === 'string' && value.trim()) return value.trim()
  }
  return ''
}

export function SummaryPostVideo({ storyboard }: Props) {
  const cards = storyboard.scenes.slice(0, 6)
  if (cards.length < 4) {
    throw new Error(`invalid_scene_count: SummaryPostVideo en az 4 sahne ister, gelen=${cards.length}`)
  }
  const brand = storyboard.brand

  return (
    <AbsoluteFill style={{ background: T.color.canvas, fontFamily: T.font.body, color: T.color.navy900 }}>
      <header style={{ height: 230, background: T.color.navy900, padding: '52px 64px 38px' }}>
        <div style={{ color: T.color.gold500, fontSize: 24, fontWeight: 800, letterSpacing: 4 }}>
          ADIM MÜŞAVİR · HIZLI ÖZET
        </div>
        <div style={{ color: '#fff', fontSize: 58, lineHeight: 1.08, fontWeight: 900, marginTop: 14 }}>
          {storyboard.title || 'EN ÇOK SORULAN HESAPLAR'}
        </div>
        <div style={{ width: 180, height: 6, borderRadius: 99, background: T.color.gold500, marginTop: 18 }} />
      </header>

      <main style={{ flex: 1, padding: '44px 54px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {cards.map((scene, index) => {
          const row = scene as unknown as Record<string, unknown>
          const code = firstText(scene, ['accountCode', 'code']) || String(index + 1).padStart(2, '0')
          const name = firstText(scene, ['accountName', 'title', 'infographic_title']) || scene.component
          const summary = firstText(scene, ['purpose', 'definition', 'key_point', 'explanation', 'subtitle'])
          const rule = firstText(scene, ['rule', 'exam_tip', 'common_mistake'])
            || (typeof row.nature === 'string' ? T.natureRule(row.nature) : '')
          const nature = typeof row.nature === 'string' ? row.nature : ''
          const accent = nature ? T.natureColor(nature) : T.color.navy500
          return (
            <section key={scene.id} style={{
              background: T.color.surface, border: `2px solid ${T.color.border}`, borderRadius: 22,
              padding: '28px 30px', display: 'flex', flexDirection: 'column', minHeight: 250,
              boxShadow: T.shadow.card,
            }}>
              <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                <span style={{ background: accent, color: '#fff', borderRadius: 10, padding: '8px 14px', fontSize: 30, fontWeight: 900 }}>
                  {code}
                </span>
                <strong style={{ fontSize: 30, lineHeight: 1.15, flex: 1 }}>{name}</strong>
                {nature && <span style={{ color: accent, fontSize: 25, fontWeight: 900 }}>({nature})</span>}
              </div>
              <p style={{ fontSize: 23, lineHeight: 1.35, margin: '22px 0 0', color: T.color.text }}>
                {summary || 'Temel tanım ve kullanım amacı.'}
              </p>
              {rule && <p style={{ fontSize: 22, lineHeight: 1.3, margin: 'auto 0 0', paddingTop: 14, color: accent, fontWeight: 800 }}>{rule}</p>}
            </section>
          )
        })}
      </main>

      <footer style={{ height: 118, padding: '0 58px', background: T.color.navy800, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <strong style={{ fontSize: 27 }}>ADIM MÜŞAVİR</strong>
        <span style={{ color: T.color.gold500, fontSize: 25, fontWeight: 800 }}>{brand.handle || '@adimmusavir'}</span>
        <span style={{ fontSize: 21, opacity: 0.82 }}>Muhasebeyi adım adım öğren.</span>
      </footer>
    </AbsoluteFill>
  )
}
