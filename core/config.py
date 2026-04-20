from typing import Optional
from pydantic_settings import BaseSettings


class Ayarlar(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    SETTINGS_ENCRYPTION_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    AI_PROVIDER: str = ""

    class Config:
        env_file = ".env"

    @property
    def etkili_sifreleme_anahtari(self) -> str:
        return self.SETTINGS_ENCRYPTION_KEY or self.SECRET_KEY


ayarlar = Ayarlar()
