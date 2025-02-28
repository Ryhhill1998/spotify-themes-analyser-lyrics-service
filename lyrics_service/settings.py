from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field


class Settings(BaseSettings):
    base_url: str
    user_agent: str
    max_concurrent_scrapes: int

    @computed_field
    @property 
    def headers(self) -> dict[str, str]:
        return {"User-Agent": self.user_agent}

    model_config = SettingsConfigDict(env_file=".env")
