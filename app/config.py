"""
Configuration Management
Centralized settings using Pydantic for validation
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application Configuration"""

    # Kafka Settings
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "postgres.activity.event_outbox"
    kafka_group_id: str = "event-processor-group"
    kafka_auto_offset_reset: str = "earliest"
    kafka_enable_auto_commit: bool = False
    kafka_max_poll_records: int = 100

    # MongoDB Settings
    mongodb_uri: str = "mongodb://localhost:27017"  # Default voor sandbox/testing
    mongodb_database: str = "activity_read"
    mongodb_connect_timeout_ms: int = 5000
    mongodb_server_selection_timeout_ms: int = 5000

    # PostgreSQL Settings (optional - voor status updates)
    postgres_host: Optional[str] = None
    postgres_port: int = 5432
    postgres_db: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None

    # Application Settings
    log_level: str = "INFO"
    processing_batch_size: int = 100
    max_retries: int = 3
    retry_delay_seconds: int = 5
    shutdown_timeout_seconds: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
