"""
Hata kodu merkezi — tüm pipeline hataları buradan gelir.
Frontend shared/error-codes.ts ile senkronize tutulur (generate_error_codes.py ile).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class PipelineError:
    error_code: str
    retryable: bool
    user_message: str
    admin_detail: dict
    stage: str            # llm | routing | tts | assets | render | postcheck
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PipelineErrorException(Exception):
    """Pipeline akışını durduran yapılandırılmış hata."""

    def __init__(
        self,
        error_code: str,
        user_message: str = "",
        admin_detail: dict | None = None,
        stage: str = "unknown",
    ):
        entry = REGISTRY.get(error_code, {})
        self.error_code = error_code
        self.retryable = entry.get("retryable", False)
        self.user_message = user_message or entry.get("user_message", error_code)
        self.admin_detail: dict = admin_detail or {}
        self.stage = stage
        super().__init__(error_code)

    def to_dict(self) -> dict:
        return {
            "error_code": self.error_code,
            "retryable": self.retryable,
            "user_message": self.user_message,
            "admin_detail": self.admin_detail,
            "stage": self.stage,
        }


# ── Kayıt defteri — tüm hata kodları burada ──────────────────────

REGISTRY: dict[str, dict[str, Any]] = {
    "unknown_content_type": {
        "retryable": False,
        "user_message": "Bilinmeyen içerik türü.",
    },
    "openai_insufficient_quota": {
        "retryable": False,
        "user_message": (
            "OpenAI API projesinin kredisi veya bütçesi yetersiz. "
            "Railway'deki API anahtarının doğru OpenAI projesine ait olduğunu "
            "ve projenin bütçesini kontrol edin."
        ),
    },
    "openai_rate_limit": {
        "retryable": True,
        "user_message": "Geçici API yoğunluğu. Otomatik yeniden denenecek.",
    },
    "openai_content_invalid": {
        "retryable": True,
        "user_message": "Model geçerli senaryo üretemedi. Yeniden deneniyor.",
    },
    "invalid_scene_for_content_type": {
        "retryable": False,
        "user_message": "Senaryo, seçilen içerik türüyle uyumsuz sahne içeriyor.",
    },
    "duration_validation_failed": {
        "retryable": False,
        "user_message": "İstenen süre ile üretilen senaryo süresi uyuşmuyor.",
    },
    "brand_asset_missing": {
        "retryable": False,
        "user_message": "Logo dosyası Remotion paketinde bulunamadı.",
    },
    "font_asset_missing": {
        "retryable": False,
        "user_message": "Yazı tipi dosyaları pakette bulunamadı.",
    },
    "tts_generation_failed": {
        "retryable": True,
        "user_message": "Seslendirme üretilemedi.",
    },
    "failed_audio_validation": {
        "retryable": False,
        "user_message": "Videoda işitilebilir ses bulunamadı.",
    },
    "math_validation_failed": {
        "retryable": False,
        "user_message": "Matematik çözümü doğrulanamadı.",
    },
    "unicode_validation_failed": {
        "retryable": False,
        "user_message": "Metinde bozuk karakter tespit edildi.",
    },
    "failed_visual_validation": {
        "retryable": False,
        "user_message": "Video yeterli görsel çeşitliliğe sahip değil.",
    },
    "caption_validation_failed": {
        "retryable": False,
        "user_message": "Altyazı üretilemedi veya sesle hizalanmadı.",
    },
    "lufs_validation_failed": {
        "retryable": False,
        "user_message": "Ses seviyesi hedef aralığın (-18..-14 LUFS) dışında.",
    },
    "preflight_failed": {
        "retryable": False,
        "user_message": "Render altyapısı ön kontrolü başarısız.",
    },
    "duplicate_content_detected": {
        "retryable": False,
        "user_message": "Bu konu son 60 günde zaten üretilmiş.",
    },
    "job_already_running": {
        "retryable": False,
        "user_message": "Bu iş zaten kuyrukta.",
    },
    "cost_cap_exceeded": {
        "retryable": False,
        "user_message": "İş için tanımlı maliyet üst sınırı aşıldı.",
    },
    "job_create_failed": {
        "retryable": False,
        "user_message": "Görev oluşturulamadı.",
    },
    "invalid_scene_count": {
        "retryable": False,
        "user_message": "İçerik türü için beklenen sahne sayısı üretilmedi.",
    },
    "asset_license_missing": {
        "retryable": False,
        "user_message": "Kullanılan görselin lisans bilgisi eksik.",
    },
    "image_generation_failed": {
        "retryable": True,
        "user_message": "Görsel üretilemedi.",
    },
    "image_contains_text": {
        "retryable": False,
        "user_message": "Üretilen görselde okunabilir metin var.",
    },
    "layout_overflow": {
        "retryable": False,
        "user_message": "İçerik ekrana sığmadı.",
    },
    "marketing_compliance_failed": {
        "retryable": False,
        "user_message": "Metin, meslek kurallarına uygun olmayan ifade içeriyor.",
    },
    "encoding_validation_failed": {
        "retryable": False,
        "user_message": "Video çıktısı yayın formatına uymuyor.",
    },
    "cost_tracking_broken": {
        "retryable": False,
        "user_message": "Render maliyeti okunamadı.",
    },
    "schema_drift_detected": {
        "retryable": False,
        "user_message": "Sistem yapılandırması tutarsız.",
    },
    "publish_blocked": {
        "retryable": False,
        "user_message": "Video yayın kalite kurallarını karşılamıyor.",
    },
}


def error_response(exc: PipelineErrorException) -> dict:
    """FastAPI response body'si için hazır dict."""
    return {
        "ok": False,
        "error_code": exc.error_code,
        "retryable": exc.retryable,
        "message": exc.user_message,
    }
