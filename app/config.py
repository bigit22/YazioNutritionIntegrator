from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    allowed_user_ids: list[int] = Field(default_factory=list)
    webhook_base_url: str = ""
    webhook_secret: str = ""
    webhook_path: str = "/webhook/telegram"

    database_url: str

    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"

    user_timezone: str = "Asia/Krasnoyarsk"

    yazio_base_url: str = "https://yzapi.yazio.com/v22"
    yazio_bearer_token: str
    yazio_notification_token: str = ""
    yazio_user_agent: str = "YAZIO/26.31.0 (com.yazio.ios.YAZIO; build:2607310147; iOS 26.4.2) Alamofire/5.12.0"

    request_timeout: float = 30.0

    @field_validator("allowed_user_ids", mode="before")
    @classmethod
    def parse_allowed_user_ids(cls, value: str | list[int]) -> list[int]:
        if isinstance(value, list): return [int(x) for x in value]
        if isinstance(value, str):
            if not value.strip(): return []
            return [int(x.strip()) for x in value.split(",") if x.strip()]
        return []

    @property
    def webhook_url(self) -> str:
        return f"{self.webhook_base_url.rstrip('/')}{self.webhook_path}"


settings = Settings()
