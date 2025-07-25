from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL : str
    SECRET_KEY : str
    APP_PORT : int
    DEBUG : bool = True

    class Config:
        env_file = '.env'

settings = Settings()