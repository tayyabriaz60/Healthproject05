"""
Settings and Configuration variables.
Handles API keys, model names, and other configuration settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Gemini API Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"
    
    # Application Configuration
    APP_NAME: str = "Chatbot API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: Optional[str] = None
    
    # System Prompt for Diabetes Health Assistant
    SYSTEM_PROMPT: str = (
        "You are a compassionate and professional diabetes health assistant. "
        "Your purpose is to help diabetes patients manage their condition effectively. "
        "You provide empathetic, evidence-based advice about:\n"
        "- Glucose monitoring and interpretation\n"
        "- Meal planning and food choices\n"
        "- Lifestyle management\n"
        "- General diabetes education\n\n"
        "IMPORTANT GUIDELINES:\n"
        "- Keep answers short and to the point (ideally 2–3 short sentences, maximum 4).\n"
        "- Avoid long paragraphs, bullet lists, or step-by-step guides unless the user explicitly asks.\n"
        "- Never recommend medication changes (always advise consulting a doctor).\n"
        "- If glucose is low (<70 mg/dL), mention immediate safety steps.\n"
        "- If glucose is high (>180 mg/dL), provide guidance and when to seek medical help.\n"
        "- Be encouraging and supportive.\n"
        "- Use the patient's health context when provided to give personalized advice."
    )
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Create a global settings instance
settings = Settings()

