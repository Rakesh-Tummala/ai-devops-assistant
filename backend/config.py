"""Centralized environment configuration, loaded and validated once at
startup instead of being scattered across modules and read lazily on
first request."""
import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """Raised for configuration problems severe enough to refuse startup."""


@dataclass
class Settings:
    app_access_key: str = field(default_factory=lambda: os.getenv("APP_ACCESS_KEY", ""))

    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))

    github_username: str = field(default_factory=lambda: os.getenv("GITHUB_USERNAME", ""))
    github_token: str = field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))
    github_repo_name: str = field(default_factory=lambda: os.getenv("GITHUB_REPO_NAME", "ai-devops-deploy"))

    render_api_key: str = field(default_factory=lambda: os.getenv("RENDER_API_KEY", ""))

    port: str = field(default_factory=lambda: os.getenv("PORT", "10000"))

    allowed_origins: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.allowed_origins = [
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
            if origin.strip()
        ]

    def validate(self) -> List[str]:
        """Raise ConfigError for missing security-critical settings; return
        a list of human-readable warnings for settings that only disable
        individual features rather than the whole app."""
        if not self.app_access_key:
            raise ConfigError(
                "APP_ACCESS_KEY must be set — this backend has no other access "
                "control, and every route (including the deploy flow) would "
                "otherwise be open to anyone who finds the URL."
            )

        warnings = []
        if not self.groq_api_key:
            warnings.append(
                "GROQ_API_KEY not set — Chat, Log Analyzer, CI/CD Generator, "
                "and Dockerfile Generator will fail at request time."
            )
        if not self.github_username or not self.github_token:
            warnings.append(
                "GITHUB_USERNAME/GITHUB_TOKEN not set — the deploy pipeline "
                "will fail at the GitHub push step."
            )
        if not self.render_api_key:
            warnings.append(
                "RENDER_API_KEY not set — the deploy pipeline will fail at "
                "the Render step."
            )
        return warnings


settings = Settings()
