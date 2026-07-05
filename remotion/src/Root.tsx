import { Composition } from 'remotion'
import { QuizVideo, getTotalFrames } from './compositions/QuizVideo'
import { MotivationVideo, getMotivationTotalFrames } from './compositions/MotivationVideo'
import { InfographicVideo, getInfographicTotalFrames } from './compositions/InfographicVideo'
import { StoryboardJSON } from './types'
import { DEFAULT_BRAND, DIMENSIONS, FPS } from './brand'

// Remotion Studio'da önizleme için örnek storyboard
const DEMO_STORYBOARD: StoryboardJSON = {
  video_type: 'quiz',
  title: 'SGS Demo — Soru Çözümü',
  lesson_name: 'Vergi Hukuku',
  topic: 'KDV Temel Kavramlar',
  format: '16:9',
  language: 'tr',
  brand: DEFAULT_BRAND,
  scenes: [
    {
      id: 1, component: 'IntroScene', duration_seconds: 8,
      title: 'Vergi Hukuku Soru Çözümü',
      subtitle: 'SGS Akademi — KDV Soruları',
    },
    {
      id: 2, component: 'QuestionScene', duration_seconds: 20,
      question_number: 1, total_questions: 4,
      title: 'Vergi Hukuku',
      question_text: 'Katma Değer Vergisinin konusunu oluşturan işlemler aşağıdakilerden hangisinde doğru olarak verilmiştir?',
      options: [
        { label: 'A', text: 'Yalnızca mal teslimleri' },
        { label: 'B', text: 'Yalnızca hizmet ifalari' },
        { label: 'C', text: 'Mal teslimleri ve hizmet ifaleri ile ithalat' },
        { label: 'D', text: 'Yalnızca ticari faaliyetler' },
      ],
    },
    {
      id: 3, component: 'ThinkingScene', duration_seconds: 5,
      question_text: 'KDV\'nin konusunu oluşturan işlemleri düşünün...',
    },
    {
      id: 4, component: 'CorrectAnswerScene', duration_seconds: 20,
      question_number: 1, correct_label: 'C',
      options: [
        { label: 'A', text: 'Yalnızca mal teslimleri' },
        { label: 'B', text: 'Yalnızca hizmet ifalari' },
        { label: 'C', text: 'Mal teslimleri ve hizmet ifaleri ile ithalat', is_correct: true },
        { label: 'D', text: 'Yalnızca ticari faaliyetler' },
      ],
      explanation: 'KDVK md. 1\'e göre KDV\'nin konusunu ticari, sınai, zirai faaliyet ve serbest meslek kapsamındaki teslim ve hizmetler ile her türlü mal ve hizmet ithali oluşturur.',
    },
    {
      id: 5, component: 'KeyPointScene', duration_seconds: 12,
      key_point: 'KDV\'de vergiyi doğuran olay: mal teslimleri, hizmet ifaleri VE ithalat. Sadece ticari faaliyetlerle sınırlı değildir.',
    },
    {
      id: 6, component: 'OutroScene', duration_seconds: 8,
      title: 'Soru Çözümü Tamamlandı',
      subtitle: 'Diğer sorular için SGS Akademi platformunu takip edin.',
    },
  ],
}

// SplitQuizVertical demo — SafeAreaOverlay önizlemesi için
const DEMO_SPLIT_VERTICAL: StoryboardJSON = {
  video_type: 'quiz',
  title: 'SGS Demo — Dikey Soru Çözümü',
  lesson_name: 'Özel Güvenlik Kanunu',
  topic: '5188 Sayılı Kanun',
  format: '9:16',
  language: 'tr',
  brand: DEFAULT_BRAND,
  scenes: [
    {
      id: 1, component: 'SplitQuizVerticalScene', duration_seconds: 30,
      question_number: 1, total_questions: 1,
      question_text: '5188 sayılı Kanun\'a göre özel güvenlik kimlik kartının geçerlilik süresi kaç yıldır?',
      options: [
        { label: 'A', text: '3 yıl' },
        { label: 'B', text: '4 yıl' },
        { label: 'C', text: '5 yıl', is_correct: true },
        { label: 'D', text: '6 yıl' },
      ],
      correct_label: 'C',
      reveal_correct: true,
      solution_steps: [
        { type: 'text', text: '5188 sayılı ÖGK md.11 gereği kimlik kartı 5 yıl geçerlidir' },
        { type: 'text', text: 'Süre dolmadan valilik onayıyla yenilenmesi zorunludur' },
        { type: 'text', text: 'Yenileme eğitimi sertifikası şartı aranır' },
      ],
      show_safe_area: true,  // Remotion Studio'da güvenli alan kılavuzu gösterir
    },
  ],
}

// Motivasyon demo storyboard
const DEMO_MOTIVATION: StoryboardJSON = {
  video_type: 'motivation',
  title: 'Motivasyon Demo',
  format: '9:16',
  language: 'tr',
  brand: DEFAULT_BRAND,
  scenes: [
    {
      id: 1, component: 'MotivationScene', duration_seconds: 20,
      message: 'Muhasebe işletmenin dilidir. Bu dili öğrenen, işletmeyi anlatır.',
    },
  ],
}

// İnfografik demo storyboard
const DEMO_INFOGRAPHIC: StoryboardJSON = {
  video_type: 'lesson',
  title: 'İnfografik Demo',
  format: '9:16',
  language: 'tr',
  brand: DEFAULT_BRAND,
  scenes: [
    {
      id: 1, component: 'InfographicCardGridScene', duration_seconds: 15,
      infographic_title: 'Temel Hesap Grupları',
      infographic_subtitle: 'Muhasebe Dersleri',
      cards: [
        { title: 'Kasa', category: 'Aktif', content: 'Nakit ve nakit benzerleri', icon: '💵' },
        { title: 'Bankalar', category: 'Aktif', content: 'Banka mevduatları', icon: '🏦' },
        { title: 'Satışlar', category: 'Gelir', content: 'Mal ve hizmet satış gelirleri', icon: '📈' },
        { title: 'Borçlar', category: 'Pasif', content: 'Kısa vadeli yükümlülükler', icon: '📋' },
      ],
      footer_note: 'SGS Muhasebe Dersleri — Adım Müşavir',
    },
  ],
}

export function Root() {
  const dim = DIMENSIONS['16:9']
  const dimV = DIMENSIONS['9:16']

  return (
    <>
      <Composition
        id="SplitQuizVerticalDemo"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        component={QuizVideo as any}
        durationInFrames={getTotalFrames(DEMO_SPLIT_VERTICAL)}
        fps={FPS}
        width={dimV.width}
        height={dimV.height}
        defaultProps={{ storyboard: DEMO_SPLIT_VERTICAL }}
        calculateMetadata={({ props }) => {
          const sb = (props as { storyboard: StoryboardJSON }).storyboard
          return { durationInFrames: getTotalFrames(sb), width: DIMENSIONS[sb.format].width, height: DIMENSIONS[sb.format].height }
        }}
      />
      <Composition
        id="QuizVideo"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        component={QuizVideo as any}
        durationInFrames={getTotalFrames(DEMO_STORYBOARD)}
        fps={FPS}
        width={dim.width}
        height={dim.height}
        defaultProps={{ storyboard: DEMO_STORYBOARD }}
        calculateMetadata={({ props }) => {
          const sb = (props as { storyboard: StoryboardJSON }).storyboard
          return { durationInFrames: getTotalFrames(sb), width: DIMENSIONS[sb.format].width, height: DIMENSIONS[sb.format].height }
        }}
      />
      <Composition
        id="MotivationVideo"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        component={MotivationVideo as any}
        durationInFrames={getMotivationTotalFrames(DEMO_MOTIVATION)}
        fps={FPS}
        width={dimV.width}
        height={dimV.height}
        defaultProps={{ storyboard: DEMO_MOTIVATION }}
        calculateMetadata={({ props }) => {
          const sb = (props as { storyboard: StoryboardJSON }).storyboard
          return { durationInFrames: getMotivationTotalFrames(sb), width: DIMENSIONS[sb.format].width, height: DIMENSIONS[sb.format].height }
        }}
      />
      <Composition
        id="InfographicVideo"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        component={InfographicVideo as any}
        durationInFrames={getInfographicTotalFrames(DEMO_INFOGRAPHIC)}
        fps={FPS}
        width={dimV.width}
        height={dimV.height}
        defaultProps={{ storyboard: DEMO_INFOGRAPHIC }}
        calculateMetadata={({ props }) => {
          const sb = (props as { storyboard: StoryboardJSON }).storyboard
          return { durationInFrames: getInfographicTotalFrames(sb), width: DIMENSIONS[sb.format].width, height: DIMENSIONS[sb.format].height }
        }}
      />
    </>
  )
}
