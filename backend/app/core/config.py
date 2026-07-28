from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    WEBHOOK_SECRET: str = ""

    # YouTube
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    YOUTUBE_REFRESH_TOKEN: str = ""
    YOUTUBE_REDIRECT_URI: str = "https://adimos-production.up.railway.app/api/v1/oauth/youtube/callback"

    # Remotion render servisi
    REMOTION_URL: str = ""

    # Instagram / Meta
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_ACCESS_TOKEN: str = ""
    META_VERIFY_TOKEN: str = ""
    FACEBOOK_PAGE_ID: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""

    # TTS
    TTS_VOICE_ID: str = "nova"           # OpenAI ses kimliği (nova | alloy | echo | fable | onyx | shimmer)
    TTS_MODEL: str = "tts-1-hd"
    TTS_SPEED: float = 0.93

    # Remotion preflight
    REMOTION_PREFLIGHT_STRICT: bool = False   # True → preflight başarısızsa render başlamaz

    # Özellik bayrağı — "false" metni yanlışlıkla truthy sayılmasın
    # Kabul edilen true değerleri: 1, true, yes, on (büyük/küçük harf fark etmez)
    # Varsayılan: kapalı (güvenli varsayılan)
    INSTAGRAM_DM_ENABLED: bool = False

    class Config:
        env_file = (".env", "../.env")
        extra = "ignore"


settings = Settings()
