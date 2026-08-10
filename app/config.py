"""Application configuration.

Values are read from environment variables and an optional ``.env`` file.
See ``.env.example`` for the full list of supported variables.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Filesystem layout -----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
APP_DIR = BASE_DIR / "app"
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
CSS_DIR = STATIC_DIR / "css"
FONTS_DIR = STATIC_DIR / "fonts"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service
    app_name: str = "resume-renderer"
    app_version: str = "1.0.0"
    api_description: str = (
        "Renders verified resume JSON into a full standalone HTML document "
        "or an A4 PDF."
    )
    log_level: str = "INFO"

    # HTTP
    cors_origins: str = "*"  # comma-separated list

    # Templates
    supported_templates: str = "classic,modern,executive"  # comma-separated
    default_template: str = "classic"

    # PDF rendering (Playwright / Chromium)
    playwright_no_sandbox: bool = True
    playwright_browser_path: str = ""
    playwright_render_timeout_ms: int = 30_000
    pdf_format: str = "A4"
    pdf_print_background: bool = True
    pdf_prefer_css_page_size: bool = True

    # Limits
    max_payload_bytes: int = 1_000_000

    @property
    def template_list(self) -> tuple[str, ...]:
        return tuple(
            name.strip()
            for name in self.supported_templates.split(",")
            if name.strip()
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    def ensure_directories(self) -> None:
        """Create the runtime directories that must exist before startup."""
        for directory in (STATIC_DIR, CSS_DIR, FONTS_DIR, TEMPLATES_DIR):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
