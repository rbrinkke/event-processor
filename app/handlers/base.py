"""
Base Event Handler
Abstract base class voor alle event handlers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import structlog

from app.models import OutboxEvent
from app.database.mongodb import mongodb

logger = structlog.get_logger()


class BaseEventHandler(ABC):
    """
    Base Event Handler

    Elke handler implementeert deze interface.
    Dit zorgt voor consistentie en makkelijke uitbreiding.
    """

    @property
    @abstractmethod
    def event_type(self) -> str:
        """Het event type dat deze handler afhandelt"""
        pass

    @property
    def handler_name(self) -> str:
        """Naam van de handler (voor logging)"""
        return self.__class__.__name__

    @abstractmethod
    async def handle(self, event: OutboxEvent) -> None:
        """
        Process the event

        Args:
            event: The outbox event to process

        Raises:
            Exception: Als processing faalt
        """
        pass

    async def validate(self, event: OutboxEvent) -> bool:
        """
        Optional validation logic

        Override in subclass als je specifieke validatie wilt
        """
        return True

    def log_event(self, event: OutboxEvent, message: str, **kwargs):
        """Helper voor structured logging"""
        logger.info(
            message,
            handler=self.handler_name,
            event_type=event.event_type,
            event_id=str(event.event_id),
            aggregate_id=str(event.aggregate_id),
            **kwargs
        )

    def log_error(self, event: OutboxEvent, error: Exception, **kwargs):
        """Helper voor error logging"""
        logger.error(
            "handler_error",
            handler=self.handler_name,
            event_type=event.event_type,
            event_id=str(event.event_id),
            error=str(error),
            error_type=type(error).__name__,
            **kwargs
        )
