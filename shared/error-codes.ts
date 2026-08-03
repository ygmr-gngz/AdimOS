/**
 * Hata kodu tanımları — backend/app/errors/registry.py ile senkronize.
 * ELLE DÜZENLEME: backend'e yeni kod eklendiğinde buraya da ekle.
 */

export const ERROR_CODES = [
  "openai_insufficient_quota",
  "openai_rate_limit",
  "openai_content_invalid",
  "invalid_scene_for_content_type",
  "duration_validation_failed",
  "brand_asset_missing",
  "font_asset_missing",
  "tts_generation_failed",
  "failed_audio_validation",
  "math_validation_failed",
  "unicode_validation_failed",
  "failed_visual_validation",
  "caption_validation_failed",
  "lufs_validation_failed",
  "preflight_failed",
  "duplicate_content_detected",
  "job_already_running",
  "cost_cap_exceeded",
  "feature_not_ready",
] as const;

export type ErrorCode = (typeof ERROR_CODES)[number];

export interface PipelineErrorResponse {
  ok: false;
  error_code: ErrorCode;
  retryable: boolean;
  message: string;
}

/** Kullanıcıya gösterilecek mesajlar (TR) */
export const ERROR_MESSAGES: Record<ErrorCode, string> = {
  openai_insufficient_quota:
    "İçerik üretimi için kullanılan OpenAI API projesinin kredisi veya bütçesi yetersiz. Railway'deki API anahtarının doğru OpenAI projesine ait olduğunu ve projenin bütçesini kontrol edin.",
  openai_rate_limit:
    "Geçici API yoğunluğu. Otomatik yeniden denenecek.",
  openai_content_invalid:
    "Model geçerli senaryo üretemedi.",
  invalid_scene_for_content_type:
    "Senaryo, seçilen içerik türüyle uyumsuz sahne içeriyor.",
  duration_validation_failed:
    "İstenen süre ile üretilen senaryo süresi uyuşmuyor.",
  brand_asset_missing:
    "Logo dosyası Remotion paketinde bulunamadı.",
  font_asset_missing:
    "Yazı tipi dosyaları pakette bulunamadı.",
  tts_generation_failed:
    "Seslendirme üretilemedi.",
  failed_audio_validation:
    "Videoda işitilebilir ses bulunamadı.",
  math_validation_failed:
    "Matematik çözümü doğrulanamadı.",
  unicode_validation_failed:
    "Metinde bozuk karakter tespit edildi.",
  failed_visual_validation:
    "Video yeterli görsel çeşitliliğe sahip değil.",
  caption_validation_failed:
    "Altyazı üretilemedi veya sesle hizalanmadı.",
  lufs_validation_failed:
    "Ses seviyesi hedef aralığın (-18..-14 LUFS) dışında.",
  preflight_failed:
    "Render altyapısı ön kontrolü başarısız.",
  duplicate_content_detected:
    "Bu konu son 60 günde zaten üretilmiş.",
  job_already_running:
    "Bu iş zaten kuyrukta.",
  cost_cap_exceeded:
    "İş için tanımlı maliyet üst sınırı aşıldı.",
  feature_not_ready:
    "Motivasyon videoları görsel kütüphanesi hazırlandıktan sonra açılacak.",
};

/** retryable=false olan kodlarda "Yeniden Dene" butonu gösterilmez */
export const NON_RETRYABLE_CODES = new Set<ErrorCode>(
  ERROR_CODES.filter((c) =>
    [
      "openai_insufficient_quota",
      "invalid_scene_for_content_type",
      "duration_validation_failed",
      "brand_asset_missing",
      "font_asset_missing",
      "failed_audio_validation",
      "math_validation_failed",
      "unicode_validation_failed",
      "failed_visual_validation",
      "caption_validation_failed",
      "lufs_validation_failed",
      "preflight_failed",
      "duplicate_content_detected",
      "job_already_running",
      "cost_cap_exceeded",
      "feature_not_ready",
    ].includes(c)
  )
);
