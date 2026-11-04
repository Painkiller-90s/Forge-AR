from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    mongodb_url: str
    mongodb_db_name: str

    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int

    # Cloudflare R2
    r2_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str

    #spotify
    spotify_client_id: str | None = None
    spotify_client_secret: str | None = None

    #lastfm
    lastfm_api_key: str | None = None

    #apify
    apify_api_token: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        hide_input_in_errors=True
    )

settings = Settings()