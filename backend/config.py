import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # OpenAI Settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Atlassian OAuth 2.0 (3LO) Settings
    ATLASSIAN_CLIENT_ID: str = ""
    ATLASSIAN_CLIENT_SECRET: str = ""
    ATLASSIAN_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    ATLASSIAN_AUTH_URL: str = "https://auth.atlassian.com/authorize"
    ATLASSIAN_TOKEN_URL: str = "https://auth.atlassian.com/oauth/token"
    ATLASSIAN_RESOURCES_URL: str = "https://api.atlassian.com/oauth/token/accessible-resources"
    ATLASSIAN_SCOPES: str = "read:jira-work write:jira-work read:jira-user read:me offline_access"

    # App Security & CORS
    SECRET_KEY: str = "jira-ai-assistant-secret-key-production-change"
    FRONTEND_URL: str = "http://localhost:5173"
    ENVIRONMENT: str = "development"
    
    # SQLite Database Path
    DB_PATH: str = "jira_assistant.db"

    # Default Mock Mode if credentials not set
    ENABLE_MOCK_FALLBACK: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
