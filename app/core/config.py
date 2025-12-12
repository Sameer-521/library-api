from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = 'Library-API'
    admin_email: str = ''
    database_url: str = ''
    test_database_url: str = ''

    hash_algorithm: str = ''
    secret_key: str = ''

    access_token_expire_minutes: int = 15
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')