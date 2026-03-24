from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str = "1ok9oo8w0A9iIezS9imJ"
    ELEVENLABS_MODEL: str
    GEMINI_API_KEY: str
    GEMINI_MODEL: str
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    TEMP_DIR: Path = Path("tmp")
    
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_BUCKET: str = "meditations"

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()

settings = get_settings()