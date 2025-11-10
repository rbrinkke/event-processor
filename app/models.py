"""
Event Models
Pydantic models voor event validation en type safety
"""

from pydantic import BaseModel, Field, UUID4
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EventStatus(str, Enum):
    """Event processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class OutboxEvent(BaseModel):
    """
    Event Outbox Model
    Represents a single event from the event_outbox table
    """
    event_id: UUID4
    sequence_id: int
    aggregate_id: UUID4
    aggregate_type: str
    event_type: str
    payload: Dict[str, Any]
    status: EventStatus
    retry_count: int = 0
    last_error: Optional[str] = None
    lock_id: Optional[UUID4] = None
    created_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID4: lambda v: str(v)
        }


class DebeziumPayload(BaseModel):
    """
    Debezium CDC Message Format
    The structure that Debezium sends to Kafka
    """
    op: str  # 'c' = create, 'u' = update, 'd' = delete, 'r' = read (snapshot)
    ts_ms: int  # Timestamp
    before: Optional[Dict[str, Any]] = None
    after: Dict[str, Any]
    source: Dict[str, Any]

    def to_outbox_event(self) -> OutboxEvent:
        """Convert Debezium payload to OutboxEvent"""
        return OutboxEvent(**self.after)


class ProcessingResult(BaseModel):
    """Result of event processing"""
    success: bool
    event_id: UUID4
    event_type: str
    handler_name: str
    error: Optional[str] = None
    processing_time_ms: float
