"""
Settings and configuration for Project Prometheus.
"""
import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    api_key_required: bool = Field(default=False, env="API_KEY_REQUIRED")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    
    # Database Configuration (for future use)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Agent Configuration
    max_agents: int = Field(default=100, env="MAX_AGENTS")
    agent_timeout_seconds: int = Field(default=300, env="AGENT_TIMEOUT_SECONDS")
    
    # Task Configuration
    max_tasks_per_agent: int = Field(default=50, env="MAX_TASKS_PER_AGENT")
    task_timeout_seconds: int = Field(default=600, env="TASK_TIMEOUT_SECONDS")
    
    # Safety Configuration
    safety_checks_enabled: bool = Field(default=True, env="SAFETY_CHECKS_ENABLED")
    max_safety_violations: int = Field(default=5, env="MAX_SAFETY_VIOLATIONS")
    emergency_halt_on_critical: bool = Field(default=True, env="EMERGENCY_HALT_ON_CRITICAL")
    
    # Performance Configuration
    max_concurrent_tasks: int = Field(default=10, env="MAX_CONCURRENT_TASKS")
    message_queue_size: int = Field(default=1000, env="MESSAGE_QUEUE_SIZE")
    
    # Monitoring Configuration
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    prometheus_metrics_port: int = Field(default=9090, env="PROMETHEUS_METRICS_PORT")
    
    # Security Configuration
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    request_timeout_seconds: int = Field(default=30, env="REQUEST_TIMEOUT_SECONDS")
    rate_limit_requests_per_minute: int = Field(default=100, env="RATE_LIMIT_RPM")
    
    # External Services
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Project Prometheus Specific
    project_name: str = Field(default="Project Prometheus", env="PROJECT_NAME")
    project_version: str = Field(default="0.1.0", env="PROJECT_VERSION")
    
    # Research Configuration
    default_research_phases: list = Field(
        default=[
            "initialization",
            "architecture_design", 
            "symbolic_reasoning_development",
            "embodied_learning",
            "safety_validation",
            "integration_testing",
            "deployment"
        ],
        env="DEFAULT_RESEARCH_PHASES"
    )
    
    # Simulation Configuration
    simulation_environments_enabled: bool = Field(default=True, env="SIMULATION_ENABLED")
    max_simulation_steps: int = Field(default=10000, env="MAX_SIMULATION_STEPS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_database_url() -> Optional[str]:
    """Get database URL from settings or environment."""
    settings = get_settings()
    return settings.database_url or os.getenv("DATABASE_URL")


def get_redis_url() -> str:
    """Get Redis URL from settings."""
    settings = get_settings()
    return settings.redis_url


def is_development() -> bool:
    """Check if running in development environment."""
    settings = get_settings()
    return settings.environment.lower() in ["development", "dev", "local"]


def is_production() -> bool:
    """Check if running in production environment."""
    settings = get_settings()
    return settings.environment.lower() in ["production", "prod"]


def get_log_config() -> dict:
    """Get logging configuration."""
    settings = get_settings()
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": settings.log_format,
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console"],
        },
        "loggers": {
            "prometheus": {
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO", 
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }