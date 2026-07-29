"""
İçerik türü kanonik sözleşmesi — TEK DOĞRULUK KAYNAĞI.

Frontend, DB ve pipeline tüm bu modülden türetilir.
Elle string yazma yasak — her zaman ContentType enum değerleri kullanılır.
"""
from enum import StrEnum
from app.errors.registry import PipelineErrorException


class ContentType(StrEnum):
    KONU_ANLATIMI = "konu_anlatimi"
    SORU_COZUM    = "soru_cozum"
    REELS_SHORT   = "reels_short"
    MOTIVASYON    = "motivasyon"
    GORSEL_POST   = "gorsel_post"


# Kullanıcı arayüzü / eski API / eski DB kayıtları → kanonik tür
CONTENT_TYPE_ALIASES: dict[str, str] = {
    # konu_anlatimi
    "lesson":           ContentType.KONU_ANLATIMI,
    "lesson_long":      ContentType.KONU_ANLATIMI,
    "sgs_topic_video":  ContentType.KONU_ANLATIMI,
    "ders":             ContentType.KONU_ANLATIMI,
    # soru_cozum
    "quiz":             ContentType.SORU_COZUM,
    "quiz_board":       ContentType.SORU_COZUM,
    "soru":             ContentType.SORU_COZUM,
    "soru_cozum_tahtasi": ContentType.SORU_COZUM,
    "question_set_long": ContentType.SORU_COZUM,
    "single_question":  ContentType.SORU_COZUM,
    # reels_short
    "educational_reel": ContentType.REELS_SHORT,
    "reel":             ContentType.REELS_SHORT,
    "short":            ContentType.REELS_SHORT,
    "bilgilendirme_kisa": ContentType.REELS_SHORT,
    "kisa_icerik":      ContentType.REELS_SHORT,
    # motivasyon
    "motivation":       ContentType.MOTIVASYON,
    "motivation_reel":  ContentType.MOTIVASYON,
    "shorts":           ContentType.MOTIVASYON,
    # gorsel_post
    "infographic":      ContentType.GORSEL_POST,
    "post":             ContentType.GORSEL_POST,
}

# Kullanıcıya gösterilen etiketler — hiçbir hata mesajında string yazılmaz
CONTENT_TYPE_LABELS: dict[str, str] = {
    ContentType.KONU_ANLATIMI: "Konu anlatımı",
    ContentType.SORU_COZUM:    "Soru çözüm",
    ContentType.REELS_SHORT:   "Reels / Short",
    ContentType.MOTIVASYON:    "Motivasyon",
    ContentType.GORSEL_POST:   "Görsel post",
}


def normalize_content_type(raw: str) -> str:
    """
    Gelen ham tip değerini kanonik ContentType değerine çevirir.
    Bilinmeyen tür → PipelineErrorException fırlatır.

    Örnek:
        normalize_content_type("motivation_reel") → "motivasyon"
        normalize_content_type("quiz")            → "soru_cozum"
        normalize_content_type("konu_anlatimi")   → "konu_anlatimi"
    """
    if not raw:
        raise PipelineErrorException(
            "unknown_content_type",
            user_message="İçerik türü belirtilmemiş.",
            admin_detail={"raw": raw},
            stage="routing",
        )
    key = raw.strip().lower()
    # Zaten kanonik mi?
    try:
        return ContentType(key)
    except ValueError:
        pass
    # Alias tablosunda var mı?
    mapped = CONTENT_TYPE_ALIASES.get(key)
    if mapped:
        return mapped
    # Bilinmiyor
    raise PipelineErrorException(
        "unknown_content_type",
        user_message=f"Bilinmeyen içerik türü: {raw}",
        admin_detail={"raw": raw, "known": [c.value for c in ContentType]},
        stage="routing",
    )
