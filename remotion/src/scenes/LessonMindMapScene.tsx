import React from 'react'
import { AbsoluteFill, Audio, interpolate, useCurrentFrame } from 'remotion'
import { BrandConfig, Scene } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

export const LessonMindMapScene: React.FC<Props> = ({ scene, brand }) => {
  const frame = useCurrentFrame()
  const branches = (scene.bullet_points ?? []).slice(0, 6)
  return (
    <AbsoluteFill style={{ background: '#F8F8F8', fontFamily: brand.font_body, padding: '58px 70px' }}>
      <h1 style={{ margin: 0, color: '#111827', fontSize: 48, fontWeight: 900 }}>{scene.title}</h1>
      {scene.definition && <p style={{ margin: '10px 0 0', color: '#475569', fontSize: 22 }}>{scene.definition}</p>}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '34% 66%', alignItems: 'center', position: 'relative' }}>
        <div style={{ background: '#BFC8FF', color: '#17204A', borderRadius: 18, padding: '28px 24px', fontSize: 30, textAlign: 'center', fontWeight: 800 }}>
          {scene.infographic_title ?? scene.title}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 24, paddingLeft: 110 }}>
          {branches.map((branch, index) => {
            const reveal = interpolate(frame, [12 + index * 8, 28 + index * 8], [0, 1], { extrapolateRight: 'clamp' })
            return (
              <div key={index} style={{ position: 'relative', opacity: reveal, transform: `translateX(${(1 - reveal) * 26}px)` }}>
                <div style={{ position: 'absolute', right: '100%', top: '50%', width: 110, height: 3, background: '#5B8FD6' }} />
                <div style={{ background: index % 2 ? '#A8DDD3' : '#B9D4EF', borderRadius: 16, padding: '20px 28px', color: '#172033', fontSize: 27, lineHeight: 1.3 }}>
                  {branch}
                </div>
              </div>
            )
          })}
        </div>
      </div>
      {scene.tts_url && <Audio src={scene.tts_url} />}
    </AbsoluteFill>
  )
}
