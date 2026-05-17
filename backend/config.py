import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")


def _clean_env(name: str):
    value = os.getenv(name)
    return value.strip() if isinstance(value, str) else None


def _parse_env_list(name: str):
    value = _clean_env(name)
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _merge_env_lists(*names: str):
    items = []
    for name in names:
        for value in _parse_env_list(name):
            if value not in items:
                items.append(value)
    return items


class Config:
    """Configuration management for API keys and settings"""
    
    def __init__(self):
        # IBM Watson Speech-to-Text Configuration
        self.ibm_api_key = _clean_env("IBM_SPEECH_TO_TEXT_API_KEY")
        self.ibm_url = _clean_env("IBM_SPEECH_TO_TEXT_URL")
        
        # Grok / Groq API Configuration (fallback for speech-to-text)
        self.grok_api_key = _clean_env("GROK_API_KEY") or _clean_env("XAI_API_KEY")
        self.groq_api_key = _clean_env("GROQ_API_KEY")
        
        # Google Gemini Configuration
        self.gemini_api_key = _clean_env("GEMINI_API_KEY")
        self.gemini_api_keys = _merge_env_lists("GEMINI_API_KEYS", "GEMINI_API_KEY")
        if not self.gemini_api_keys and self.gemini_api_key:
            self.gemini_api_keys = [self.gemini_api_key]
        
        # Twilio WhatsApp Configuration
        self.twilio_account_sid = _clean_env("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = _clean_env("TWILIO_AUTH_TOKEN")
        self.twilio_whatsapp_number = _clean_env("TWILIO_WHATSAPP_NUMBER")
        
        # Application Configuration
        self.environment = _clean_env("ENVIRONMENT") or "development"
    
    def is_configured(self) -> bool:
        """Check if the app has the minimum AI configuration available"""
        return bool(self.gemini_api_key and (self.is_ibm_configured() or self.is_grok_configured()))
    
    def is_gemini_configured(self) -> bool:
        """Check if Gemini API is configured"""
        return bool(self.gemini_api_keys)

    def get_gemini_api_keys(self):
        """Return Gemini API keys in priority order."""
        return list(self.gemini_api_keys)
    
    def is_ibm_configured(self) -> bool:
        """Check if IBM Watson is configured"""
        return bool(self.ibm_api_key and self.ibm_url)
    
    def is_grok_configured(self) -> bool:
        """Check if Grok / Groq fallback is configured"""
        return bool(self.grok_api_key or self.groq_api_key)

    def is_speech_configured(self) -> bool:
        """Check if at least one speech-to-text provider is configured"""
        return self.is_ibm_configured() or self.is_grok_configured()
    
    def is_twilio_configured(self) -> bool:
        """Check if Twilio WhatsApp is configured"""
        return bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_whatsapp_number)


# Global config instance
config = Config()


# Made with Bob