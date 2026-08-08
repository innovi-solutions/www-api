from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Supabase (Phase 2)
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # Resend (Phase 3)
    resend_api_key: str = ""
    stakeholder_emails: str = ""   # comma-separated
    from_email: str = "leads@innovi-solutions.com"

    # Security (Phase 4)
    turnstile_secret: str = ""

    # CORS
    allowed_origins: str = "http://localhost:3000"

    @property
    def stakeholder_list(self) -> list[str]:
        return [e.strip() for e in self.stakeholder_emails.split(",") if e.strip()]

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

settings = Settings()