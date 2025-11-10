"""
Consumer Tests
Tests voor Kafka consumer met message processing
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.consumer import EventConsumer
from app.models import DebeziumPayload, EventStatus


@pytest.mark.asyncio
class TestEventConsumer:
    """Test EventConsumer class"""

    async def test_consumer_initialization(self):
        """Test dat consumer correct initialiseert"""
        consumer = EventConsumer()

        assert consumer.consumer is None
        assert consumer.running is False
        assert consumer._processing_count == 0
        assert consumer._error_count == 0

    async def test_consumer_stats(self):
        """Test consumer statistics property"""
        consumer = EventConsumer()

        stats = consumer.stats
        assert stats["running"] is False
        assert stats["total_processed"] == 0
        assert stats["total_errors"] == 0
        assert "uptime_seconds" in stats

    async def test_process_message_valid_event(self):
        """Test processing van een geldig Kafka message"""
        consumer = EventConsumer()

        # Mock Kafka message
        mock_message = MagicMock()
        mock_message.partition = 0
        mock_message.offset = 123
        mock_message.value = {
            "op": "c",
            "ts_ms": 1699876543210,
            "after": {
                "event_id": str(uuid4()),
                "sequence_id": 1,
                "aggregate_id": str(uuid4()),
                "aggregate_type": "User",
                "event_type": "UserCreated",
                "payload": {"email": "test@example.com", "username": "testuser"},
                "status": "pending",
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat(),
            },
            "source": {"version": "2.4"},
        }

        # Mock handler registry
        with patch("app.consumer.handler_registry") as mock_registry, patch(
            "app.handlers.user_handlers.mongodb"
        ):
            mock_handler = AsyncMock()
            mock_handler.validate = AsyncMock(return_value=True)
            mock_handler.handle = AsyncMock()
            mock_registry.get_handlers.return_value = [mock_handler]

            # Process message
            result = await consumer.process_message(mock_message)

            # Verify
            assert result is not None
            assert result.success is True
            assert consumer._processing_count == 1
            mock_handler.handle.assert_called_once()

    async def test_process_message_skip_delete_operation(self):
        """Test dat delete operations worden geskipped"""
        consumer = EventConsumer()

        mock_message = MagicMock()
        mock_message.partition = 0
        mock_message.offset = 456
        mock_message.value = {
            "op": "d",  # delete operation
            "ts_ms": 1699876543210,
            "after": {},
            "source": {"version": "2.4"},
        }

        result = await consumer.process_message(mock_message)

        # Delete operations should be skipped
        assert result is None
        assert consumer._processing_count == 0

    async def test_process_message_skip_snapshot_operation(self):
        """Test dat snapshot operations worden geskipped"""
        consumer = EventConsumer()

        mock_message = MagicMock()
        mock_message.partition = 0
        mock_message.offset = 789
        mock_message.value = {
            "op": "r",  # read/snapshot operation
            "ts_ms": 1699876543210,
            "after": {
                "event_id": str(uuid4()),
                "sequence_id": 1,
                "aggregate_id": str(uuid4()),
                "aggregate_type": "User",
                "event_type": "UserCreated",
                "payload": {},
                "status": "pending",
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat(),
            },
            "source": {"version": "2.4"},
        }

        result = await consumer.process_message(mock_message)

        assert result is None

    async def test_process_message_no_handlers_found(self):
        """Test handling wanneer geen handlers gevonden worden"""
        consumer = EventConsumer()

        mock_message = MagicMock()
        mock_message.partition = 0
        mock_message.offset = 111
        mock_message.value = {
            "op": "c",
            "ts_ms": 1699876543210,
            "after": {
                "event_id": str(uuid4()),
                "sequence_id": 1,
                "aggregate_id": str(uuid4()),
                "aggregate_type": "Unknown",
                "event_type": "UnknownEvent",
                "payload": {},
                "status": "pending",
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat(),
            },
            "source": {"version": "2.4"},
        }

        with patch("app.consumer.handler_registry") as mock_registry:
            mock_registry.get_handlers.return_value = []

            result = await consumer.process_message(mock_message)

            # Should return None when no handlers
            assert result is None

    async def test_process_message_handler_validation_fails(self):
        """Test wanneer handler validatie faalt"""
        consumer = EventConsumer()

        mock_message = MagicMock()
        mock_message.value = {
            "op": "c",
            "ts_ms": 1699876543210,
            "after": {
                "event_id": str(uuid4()),
                "sequence_id": 1,
                "aggregate_id": str(uuid4()),
                "aggregate_type": "User",
                "event_type": "UserCreated",
                "payload": {},
                "status": "pending",
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat(),
            },
            "source": {"version": "2.4"},
        }

        with patch("app.consumer.handler_registry") as mock_registry:
            mock_handler = AsyncMock()
            mock_handler.validate = AsyncMock(return_value=False)  # Validation fails
            mock_handler.handle = AsyncMock()
            mock_registry.get_handlers.return_value = [mock_handler]

            result = await consumer.process_message(mock_message)

            # Handler.handle should NOT be called
            mock_handler.handle.assert_not_called()

    async def test_process_message_handler_exception(self):
        """Test error handling wanneer handler faalt"""
        consumer = EventConsumer()

        mock_message = MagicMock()
        mock_message.partition = 0
        mock_message.offset = 222
        mock_message.value = {
            "op": "c",
            "ts_ms": 1699876543210,
            "after": {
                "event_id": str(uuid4()),
                "sequence_id": 1,
                "aggregate_id": str(uuid4()),
                "aggregate_type": "User",
                "event_type": "UserCreated",
                "payload": {},
                "status": "pending",
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat(),
            },
            "source": {"version": "2.4"},
        }

        with patch("app.consumer.handler_registry") as mock_registry:
            mock_handler = AsyncMock()
            mock_handler.validate = AsyncMock(return_value=True)
            mock_handler.handle = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            mock_handler.handler_name = "TestHandler"
            mock_registry.get_handlers.return_value = [mock_handler]

            result = await consumer.process_message(mock_message)

            # Should still return result (not None), but error count increases
            assert consumer._error_count == 1

    async def test_process_message_multiple_handlers(self):
        """Test processing met meerdere handlers"""
        consumer = EventConsumer()

        mock_message = MagicMock()
        mock_message.partition = 0
        mock_message.offset = 333
        mock_message.value = {
            "op": "c",
            "ts_ms": 1699876543210,
            "after": {
                "event_id": str(uuid4()),
                "sequence_id": 1,
                "aggregate_id": str(uuid4()),
                "aggregate_type": "User",
                "event_type": "UserCreated",
                "payload": {},
                "status": "pending",
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat(),
            },
            "source": {"version": "2.4"},
        }

        with patch("app.consumer.handler_registry") as mock_registry, patch(
            "app.handlers.user_handlers.mongodb"
        ):
            # Create 3 mock handlers
            handlers = []
            for i in range(3):
                handler = AsyncMock()
                handler.validate = AsyncMock(return_value=True)
                handler.handle = AsyncMock()
                handler.handler_name = f"Handler{i}"
                handlers.append(handler)

            mock_registry.get_handlers.return_value = handlers

            result = await consumer.process_message(mock_message)

            # All 3 handlers should be called
            for handler in handlers:
                handler.handle.assert_called_once()

            assert result.success is True

    async def test_process_message_invalid_payload(self):
        """Test handling van invalid message payload"""
        consumer = EventConsumer()

        mock_message = MagicMock()
        mock_message.partition = 0
        mock_message.offset = 444
        mock_message.value = {
            "op": "c",
            "ts_ms": 1699876543210,
            # Missing required 'after' field
            "source": {"version": "2.4"},
        }

        result = await consumer.process_message(mock_message)

        # Should handle error gracefully
        assert result is None
        assert consumer._error_count == 1

    async def test_consumer_processing_metrics(self):
        """Test dat processing metrics correct worden bijgehouden"""
        consumer = EventConsumer()

        assert consumer._processing_count == 0
        assert consumer._error_count == 0

        # Simulate successful processing
        consumer._processing_count = 10
        consumer._error_count = 2

        stats = consumer.stats
        assert stats["total_processed"] == 10
        assert stats["total_errors"] == 2


@pytest.mark.asyncio
class TestConsumerEdgeCases:
    """Test edge cases in consumer"""

    async def test_process_message_empty_payload(self):
        """Test message met lege payload"""
        consumer = EventConsumer()

        mock_message = MagicMock()
        mock_message.value = {
            "op": "c",
            "ts_ms": 1699876543210,
            "after": {
                "event_id": str(uuid4()),
                "sequence_id": 1,
                "aggregate_id": str(uuid4()),
                "aggregate_type": "User",
                "event_type": "UserCreated",
                "payload": {},  # Empty payload
                "status": "pending",
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat(),
            },
            "source": {"version": "2.4"},
        }

        with patch("app.consumer.handler_registry") as mock_registry, patch(
            "app.handlers.user_handlers.mongodb"
        ):
            mock_handler = AsyncMock()
            mock_handler.validate = AsyncMock(return_value=True)
            mock_handler.handle = AsyncMock()
            mock_registry.get_handlers.return_value = [mock_handler]

            result = await consumer.process_message(mock_message)

            # Should process even with empty payload
            assert result is not None
            mock_handler.handle.assert_called_once()

    async def test_process_message_very_large_payload(self):
        """Test message met zeer grote payload"""
        consumer = EventConsumer()

        # Create large payload (1000 fields)
        large_payload = {f"field_{i}": f"value_{i}" for i in range(1000)}

        mock_message = MagicMock()
        mock_message.value = {
            "op": "c",
            "ts_ms": 1699876543210,
            "after": {
                "event_id": str(uuid4()),
                "sequence_id": 1,
                "aggregate_id": str(uuid4()),
                "aggregate_type": "User",
                "event_type": "UserCreated",
                "payload": large_payload,
                "status": "pending",
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat(),
            },
            "source": {"version": "2.4"},
        }

        with patch("app.consumer.handler_registry") as mock_registry, patch(
            "app.handlers.user_handlers.mongodb"
        ):
            mock_handler = AsyncMock()
            mock_handler.validate = AsyncMock(return_value=True)
            mock_handler.handle = AsyncMock()
            mock_registry.get_handlers.return_value = [mock_handler]

            result = await consumer.process_message(mock_message)

            # Should handle large payloads
            assert result is not None
            assert len(result.event_type) > 0
