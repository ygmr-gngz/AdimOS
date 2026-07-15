import { Composition } from 'remotion'
import { QuizVideo, getTotalFrames } from './compositions/QuizVideo'
import { MotivationVideo, getMotivationTotalFrames } from './compositions/MotivationVideo'
import { InfographicVideo, getInfographicTotalFrames } from './compositions/InfographicVideo'
import { LessonVideo, getLessonTotalFrames } from './compositions/LessonVideo'
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

// Konu anlatımı demo storyboard — yeni LessonVideo tasarımı
const DEMO_LESSON: StoryboardJSON = {
  video_type: 'konu_anlatimi',
  title: 'Kasa Hesabı — Konu Anlatımı',
  lesson_name: 'Muhasebe',
  topic: 'Kasa Hesabı',
  format: '16:9',
  language: 'tr',
  brand: { ...DEFAULT_BRAND, handle: '@adimmusavir' },
  scenes: [
    {
      id: 1, component: 'LessonTitleScene', duration_seconds: 8,
      icon: '💰', title: 'Kasa Hesabı',
      subtitle: 'MUHASEBE',
      key_point: '100 Nolu Hesap — Dönen Varlıklar grubu',
    },
    {
      id: 2, component: 'LessonConceptScene', duration_seconds: 14,
      icon: '📌', title: 'Kasa Hesabı Nedir?',
      definition: 'İşletmenin kasasında bulunan yerli ve yabancı para mevcutlarını izleyen aktif karakterli bir hesaptır.',
      bullet_points: [
        'Hesap kodu: 100 — Dönen Varlıklar grubu',
        'Borç bakiyesi verir; alacak bakiyesi vermez',
        'Nakit giriş → Borçlandırılır (Artış)',
        'Nakit çıkış → Alacaklandırılır (Azalış)',
      ],
    },
    {
      id: 3, component: 'LessonCardScene', duration_seconds: 16,
      infographic_title: 'Kasa Hesabına Giren İşlemler',
      infographic_subtitle: 'Borçlandırma ve Alacaklandırma',
      cards: [
        {
          icon: '📈', title: 'Nakit Satış', category: 'Borç',
          content: 'Mal veya hizmet nakit karşılığı satıldığında kasaya para girer.',
          rule: 'Kasa hesabı BORÇLANIR',
        },
        {
          icon: '🏦', title: 'Bankadan Çekim', category: 'Borç',
          content: 'Bankadaki mevduattan nakit çekildiğinde kasaya aktarılır.',
          rule: 'Kasa BORÇ / Banka ALACAK',
        },
        {
          icon: '🛒', title: 'Nakit Alım', category: 'Alacak',
          content: 'Mal, hizmet veya demirbaş peşin alındığında kasadan para çıkar.',
          rule: 'Kasa hesabı ALACAKLANIR',
        },
        {
          icon: '💳', title: 'Borç Ödeme', category: 'Alacak',
          content: 'Alacaklılara nakit ödeme yapıldığında kasadan çıkar.',
          rule: 'Kasa ALACAK / Borç hesabı BORÇ',
        },
      ],
    },
    {
      id: 4, component: 'LessonExampleScene', duration_seconds: 20,
      title: 'Nakit Satış Örneği',
      question_text: 'İşletme 15.000 TL\'lik malı peşin sattı. KDV %20 hesabı yapılmamıştır. Bu işlemi yevmiye defterine kaydediniz.',
      journal_rows: [
        { code: '100', name: 'Kasa',          debit: 15000 },
        { code: '600', name: '    Yurt İçi Satışlar', credit: 15000, indent: true },
      ],
      explanation: 'Nakit tahsilat yapıldığı için 100 Kasa borçlandırıldı, 600 Yurt İçi Satışlar alacaklandırıldı.',
    },
    {
      id: 5, component: 'LessonSummaryScene', duration_seconds: 12,
      title: 'Kasa Hesabı — Özet',
      bullet_points: [
        'Hesap kodu 100, Dönen Varlıklar grubunda yer alır',
        'Nakit girişlerde borçlandırılır, nakit çıkışlarda alacaklandırılır',
        'Dönem sonunda her zaman borç bakiyesi (veya sıfır) verir',
        'Kasa sayım fazlası → 397 / sayım noksanı → 197 hesapla karşılaştırılır',
      ],
      key_point: 'Kasa hesabı HİÇBİR ZAMAN alacak bakiyesi vermez!',
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
      <Composition
        id="LessonVideo"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        component={LessonVideo as any}
        durationInFrames={getLessonTotalFrames(DEMO_LESSON)}
        fps={FPS}
        width={dim.width}
        height={dim.height}
        defaultProps={{ storyboard: DEMO_LESSON }}
        calculateMetadata={({ props }) => {
          const sb = (props as { storyboard: StoryboardJSON }).storyboard
          return { durationInFrames: getLessonTotalFrames(sb), width: DIMENSIONS[sb.format].width, height: DIMENSIONS[sb.format].height }
        }}
      />
      {/* LessonVideoDemo — geriye dönük uyumluluk: eski S3 bundle'ında bu ID kayıtlıydı */}
      <Composition
        id="LessonVideoDemo"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        component={LessonVideo as any}
        durationInFrames={getLessonTotalFrames(DEMO_LESSON)}
        fps={FPS}
        width={dim.width}
        height={dim.height}
        defaultProps={{ storyboard: DEMO_LESSON }}
        calculateMetadata={({ props }) => {
          const sb = (props as { storyboard: StoryboardJSON }).storyboard
          return { durationInFrames: getLessonTotalFrames(sb), width: DIMENSIONS[sb.format].width, height: DIMENSIONS[sb.format].height }
        }}
      />
    </>
  )
}
