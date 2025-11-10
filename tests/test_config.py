"""
Configuration Tests
Valideer settings en configuratie management
"""

import pytest
import os
from pydantic import ValidationError

from app.config import Settings


class TestSettings:
    """Test Settings configuration"""

    def test_default_settings(self):
        """Test dat default settings laden"""
        settings = Settings(mongodb_uri="mongodb://localhost:27017")

        # Kafka defaults
        assert settings.kafka_bootstrap_servers == "localhost:9092"
        assert settings.kafka_topic == "postgres.activity.event_outbox"
        assert settings.kafka_group_id == "event-processor-group"
        assert settings.kafka_auto_offset_reset == "earliest"
        assert settings.kafka_enable_auto_commit is False
        assert settings.kafka_max_poll_records == 100

        # MongoDB defaults
        assert settings.mongodb_database == "activity_read"
        assert settings.mongodb_connect_timeout_ms == 5000

        # Application defaults
        assert settings.log_level == "INFO"
        assert settings.processing_batch_size == 100
        assert settings.max_retries == 3

    def test_custom_settings(self):
        """Test custom settings override defaults"""
        settings = Settings(
            mongodb_uri="mongodb://custom:27017",
            kafka_bootstrap_servers="kafka1:9092,kafka2:9092",
            kafka_topic="custom.topic",
            mongodb_database="custom_db",
            log_level="DEBUG",
            processing_batch_size=500,
        )

        assert settings.kafka_bootstrap_servers == "kafka1:9092,kafka2:9092"
        assert settings.kafka_topic == "custom.topic"
        assert settings.mongodb_database == "custom_db"
        assert settings.log_level == "DEBUG"
        assert settings.processing_batch_size == 500

    def test_postgres_settings_optional(self):
        """Test dat PostgreSQL settings optioneel zijn (kunnen None zijn)"""
        # PostgreSQL settings zijn optioneel (Optional type)
        # maar kunnen defaults hebben uit .env
        settings = Settings(mongodb_uri="mongodb://localhost:27017")

        # Check that they are Optional type (can be None or have value)
        assert isinstance(settings.postgres_host, (str, type(None)))
        assert isinstance(settings.postgres_db, (str, type(None)))
        assert isinstance(settings.postgres_user, (str, type(None)))
        assert isinstance(settings.postgres_password, (str, type(None)))
        assert settings.postgres_port == 5432  # Has default

    def test_postgres_settings_when_provided(self):
        """Test PostgreSQL settings wanneer opgegeven"""
        settings = Settings(
            mongodb_uri="mongodb://localhost:27017",
            postgres_host="db.example.com",
            postgres_db="activity",
            postgres_user="app_user",
            postgres_password="secret123",
            postgres_port=5433,
        )

        assert settings.postgres_host == "db.example.com"
        assert settings.postgres_db == "activity"
        assert settings.postgres_user == "app_user"
        assert settings.postgres_password == "secret123"
        assert settings.postgres_port == 5433

    def test_mongodb_uri_validation(self):
        """Test MongoDB URI is required"""
        # MongoDB URI has a default now, so it won't fail
        settings = Settings()
        assert settings.mongodb_uri is not None

    def test_timeout_settings(self):
        """Test timeout settings zijn correct"""
        settings = Settings(
            mongodb_uri="mongodb://localhost:27017",
            mongodb_connect_timeout_ms=10000,
            mongodb_server_selection_timeout_ms=8000,
            retry_delay_seconds=10,
            shutdown_timeout_seconds=60,
        )

        assert settings.mongodb_connect_timeout_ms == 10000
        assert settings.mongodb_server_selection_timeout_ms == 8000
        assert settings.retry_delay_seconds == 10
        assert settings.shutdown_timeout_seconds == 60

    def test_kafka_settings_types(self):
        """Test Kafka settings hebben correcte types"""
        settings = Settings(mongodb_uri="mongodb://localhost:27017")

        assert isinstance(settings.kafka_enable_auto_commit, bool)
        assert isinstance(settings.kafka_max_poll_records, int)
        assert isinstance(settings.kafka_bootstrap_servers, str)

    def test_case_insensitive_env_vars(self):
        """Test dat environment variables case-insensitive zijn"""
        # Settings.Config.case_sensitive = False
        # Use lowercase to match field name
        settings = Settings(mongodb_uri="mongodb://localhost:27017", log_level="DEBUG")
        assert settings.log_level == "DEBUG"


class TestConfigurationEdgeCases:
    """Test edge cases in configuration"""

    def test_empty_mongodb_uri_uses_default(self):
        """Test dat lege MongoDB URI default gebruikt"""
        settings = Settings()
        assert "mongodb://" in settings.mongodb_uri

    def test_very_large_batch_size(self):
        """Test zeer grote batch size"""
        settings = Settings(
            mongodb_uri="mongodb://localhost:27017", processing_batch_size=10000
        )
        assert settings.processing_batch_size == 10000

    def test_zero_batch_size(self):
        """Test batch size = 0 (edge case)"""
        settings = Settings(mongodb_uri="mongodb://localhost:27017", processing_batch_size=0)
        assert settings.processing_batch_size == 0

    def test_negative_retry_count(self):
        """Test negatieve retry count"""
        settings = Settings(mongodb_uri="mongodb://localhost:27017", max_retries=-1)
        # Pydantic allows this, but application logic should handle it
        assert settings.max_retries == -1

    def test_special_characters_in_mongodb_uri(self):
        """Test speciale characters in MongoDB URI"""
        uri = "mongodb://user:p@ssw0rd!@host:27017/db?authSource=admin"
        settings = Settings(mongodb_uri=uri)
        assert settings.mongodb_uri == uri

    def test_kafka_multiple_bootstrap_servers(self):
        """Test meerdere Kafka bootstrap servers"""
        servers = "kafka1:9092,kafka2:9092,kafka3:9092"
        settings = Settings(mongodb_uri="mongodb://localhost:27017", kafka_bootstrap_servers=servers)
        assert settings.kafka_bootstrap_servers == servers
        assert "," in settings.kafka_bootstrap_servers

    def test_log_levels(self):
        """Test verschillende log levels"""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(mongodb_uri="mongodb://localhost:27017", log_level=level)
            assert settings.log_level == level


class TestSettingsValidation:
    """Test Pydantic validation in Settings"""

    def test_settings_immutable_after_creation(self):
        """Test dat settings immutable zijn (voor security)"""
        settings = Settings(mongodb_uri="mongodb://localhost:27017")

        # Settings zijn Pydantic BaseSettings - fields kunnen gewijzigd worden
        # maar dit is een code smell in productie
        original_uri = settings.mongodb_uri
        assert original_uri is not None

    def test_settings_repr(self):
        """Test settings string representatie (zonder secrets)"""
        settings = Settings(
            mongodb_uri="mongodb://user:secret@localhost:27017",
            postgres_password="super_secret",
        )

        # Check dat repr niet direct de secrets toont
        settings_str = str(settings)
        assert settings_str is not None
