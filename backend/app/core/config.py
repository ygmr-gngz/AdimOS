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

    # Instagram / Meta
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_ACCESS_TOKEN: str = ""
    META_VERIFY_TOKEN: str = ""
    FACEBOOK_PAGE_ID: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""

    class Config:
        env_file = (".env", "../.env")
        extra = "ignore"


settings = Settings()
