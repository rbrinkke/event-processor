"""
Model Tests
Tests voor Pydantic event models en data validation
"""

from datetime import datetime
from uuid import uuid4

from app.models import EventStatus, OutboxEvent, DebeziumPayload, ProcessingResult


class TestEventStatus:
    """Test EventStatus enum"""

    def test_event_status_values(self):
        """Test dat alle status waarden correct zijn"""
        assert EventStatus.PENDING == "pending"
        assert EventStatus.PROCESSING == "processing"
        assert EventStatus.PROCESSED == "processed"
        assert EventStatus.FAILED == "failed"


class TestOutboxEvent:
    """Test OutboxEvent model"""

    def test_create_valid_event(self):
        """Test aanmaken van een geldig event"""
        event_id = uuid4()
        aggregate_id = uuid4()
        created_at = datetime.utcnow()

        event = OutboxEvent(
            event_id=event_id,
            sequence_id=1,
            aggregate_id=aggregate_id,
            aggregate_type="User",
            event_type="UserCreated",
            payload={"email": "test@example.com"},
            status=EventStatus.PENDING,
            created_at=created_at,
        )

        assert event.event_id == event_id
        assert event.sequence_id == 1
        assert event.aggregate_id == aggregate_id
        assert event.aggregate_type == "User"
        assert event.event_type == "UserCreated"
        assert event.payload["email"] == "test@example.com"
        assert event.status == EventStatus.PENDING
        assert event.retry_count == 0
        assert event.last_error is None
        assert event.created_at == created_at

    def test_event_with_optional_fields(self):
        """Test event met optionele velden"""
        lock_id = uuid4()
        published_at = datetime.utcnow()

        event = OutboxEvent(
            event_id=uuid4(),
            sequence_id=1,
            aggregate_id=uuid4(),
            aggregate_type="User",
            event_type="UserCreated",
            payload={},
            status=EventStatus.PROCESSED,
            retry_count=3,
            last_error="Test error",
            lock_id=lock_id,
            created_at=datetime.utcnow(),
            published_at=published_at,
        )

        assert event.retry_count == 3
        assert event.last_error == "Test error"
        assert event.lock_id == lock_id
        assert event.published_at == published_at


class TestDebeziumPayload:
    """Test Debezium CDC message format"""

    def test_create_payload(self):
        """Test aanmaken van Debezium payload"""
        payload = DebeziumPayload(
            op="c",
            ts_ms=1234567890,
            after={
                "event_id": str(uuid4()),
                "sequence_id": 1,
                "aggregate_id": str(uuid4()),
                "aggregate_type": "User",
                "event_type": "UserCreated",
                "payload": {"test": "data"},
                "status": "pending",
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat(),
            },
            source={"version": "2.4"},
        )

        assert payload.op == "c"
        assert payload.ts_ms == 1234567890
        assert "event_id" in payload.after

    def test_to_outbox_event_conversion(self):
        """Test conversie van Debezium payload naar OutboxEvent"""
        event_id = uuid4()
        aggregate_id = uuid4()
        now = datetime.utcnow()

        payload = DebeziumPayload(
            op="c",
            ts_ms=1234567890,
            after={
                "event_id": str(event_id),
                "sequence_id": 1,
                "aggregate_id": str(aggregate_id),
                "aggregate_type": "User",
                "event_type": "UserCreated",
                "payload": {"email": "test@example.com"},
                "status": "pending",
                "retry_count": 0,
                "created_at": now.isoformat(),
            },
            source={"version": "2.4"},
        )

        event = payload.to_outbox_event()

        assert isinstance(event, OutboxEvent)
        assert event.event_id == event_id
        assert event.aggregate_id == aggregate_id
        assert event.event_type == "UserCreated"
        assert event.payload["email"] == "test@example.com"


class TestProcessingResult:
    """Test ProcessingResult model"""

    def test_successful_result(self):
        """Test successful processing result"""
        event_id = uuid4()

        result = ProcessingResult(
            success=True,
            event_id=event_id,
            event_type="UserCreated",
            handler_name="UserCreatedHandler",
            processing_time_ms=45.5,
        )

        assert result.success is True
        assert result.event_id == event_id
        assert result.event_type == "UserCreated"
        assert result.handler_name == "UserCreatedHandler"
        assert result.processing_time_ms == 45.5
        assert result.error is None

    def test_failed_result(self):
        """Test failed processing result"""
        result = ProcessingResult(
            success=False,
            event_id=uuid4(),
            event_type="UserCreated",
            handler_name="UserCreatedHandler",
            error="Connection timeout",
            processing_time_ms=1000.0,
        )

        assert result.success is False
        assert result.error == "Connection timeout"
