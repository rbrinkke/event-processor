"""
Handler Registry
Centralized registration en lookup van event handlers
"""

from typing import Dict, List, Type
import structlog

from app.handlers.base import BaseEventHandler
from app.handlers import (
    UserCreatedHandler,
    UserUpdatedHandler,
    UserStatisticsHandler,
    ActivityCreatedHandler,
    ActivityUpdatedHandler,
    ParticipantJoinedHandler,
)

logger = structlog.get_logger()


class HandlerRegistry:
    """
    Handler Registry

    Beheert alle event handlers en routeert events naar de juiste handlers.

    Key Design: Meerdere handlers kunnen luisteren naar hetzelfde event_type!
    """

    def __init__(self):
        self._handlers: Dict[str, List[BaseEventHandler]] = {}
        self._initialize_handlers()

    def _initialize_handlers(self):
        """
        Register all handlers

        HIER VOEG JE NIEUWE HANDLERS TOE!
        Dit is de enige plek waar je wijzigingen maakt bij nieuwe event types.
        """

        # User handlers
        self.register(UserCreatedHandler())
        self.register(UserStatisticsHandler())  # Luistert ook naar UserCreated!
        self.register(UserUpdatedHandler())

        # Activity handlers
        self.register(ActivityCreatedHandler())
        self.register(ActivityUpdatedHandler())
        self.register(ParticipantJoinedHandler())

        # Log registered handlers
        for event_type, handlers in self._handlers.items():
            handler_names = [h.handler_name for h in handlers]
            logger.info(
                "handlers_registered",
                event_type=event_type,
                handlers=handler_names,
                count=len(handlers)
            )

    def register(self, handler: BaseEventHandler):
        """
        Register een handler voor zijn event_type

        Args:
            handler: Een instantie van BaseEventHandler
        """
        event_type = handler.event_type

        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)

        logger.debug(
            "handler_registered",
            event_type=event_type,
            handler=handler.handler_name
        )

    def get_handlers(self, event_type: str) -> List[BaseEventHandler]:
        """
        Get alle handlers voor een event_type

        Args:
            event_type: Het event type (bijv. "UserCreated")

        Returns:
            List van handlers (kan leeg zijn)
        """
        return self._handlers.get(event_type, [])

    def has_handlers(self, event_type: str) -> bool:
        """Check of er handlers zijn voor een event_type"""
        return event_type in self._handlers and len(self._handlers[event_type]) > 0

    @property
    def registered_event_types(self) -> List[str]:
        """Get alle geregistreerde event types"""
        return list(self._handlers.keys())


# Global registry instance
handler_registry = HandlerRegistry()
