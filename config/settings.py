"""
Application configuration management using Pydantic Settings.
Loads configuration from environment variables with type validation.
"""

from typing import Literal
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    # Application
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")

    # LLM Provider
    anthropic_api_key: str = Field(description="Anthropic API key")
    llm_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="LLM model to use",
    )
    llm_max_tokens: int = Field(default=4096, description="Maximum tokens for LLM")
    llm_temperature: float = Field(default=0.0, description="LLM temperature")
    llm_max_retries: int = Field(default=3, description="Maximum retries for LLM calls")
    llm_timeout_seconds: int = Field(default=30, description="LLM request timeout")

    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(
        default=60,
        description="Rate limit for requests per minute",
    )
    rate_limit_tokens_per_minute: int = Field(
        default=100000,
        description="Rate limit for tokens per minute",
    )

    # Observability
    otel_enabled: bool = Field(default=True, description="Enable OpenTelemetry")
    otel_exporter: Literal["console", "jaeger", "otlp"] = Field(
        default="console",
        description="OpenTelemetry exporter type",
    )
    metrics_port: int = Field(default=9090, description="Prometheus metrics port")

    # Mock Mode
    use_mock_tools: bool = Field(default=True, description="Use mock tools for testing")
    use_mock_llm: bool = Field(default=False, description="Use mock LLM responses")

    # Evaluation
    eval_dataset_path: str = Field(
        default="tests/evaluation/datasets",
        description="Path to evaluation datasets",
    )
    eval_run_on_ci: bool = Field(
        default=True,
        description="Run evaluation in CI",
    )
    eval_sample_size: int = Field(
        default=50,
        description="Sample size for CI evaluation",
    )

    # API
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_reload: bool = Field(default=True, description="Auto-reload in development")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.app_env == "staging"


# Singleton instance
settings = Settings()
