"""
Registry Tests
Tests voor handler registry pattern
"""

from app.registry import HandlerRegistry
from app.handlers.user_handlers import UserCreatedHandler


class TestHandlerRegistry:
    """Test HandlerRegistry"""

    def test_registry_initialization(self):
        """Test dat registry correct initialiseert met handlers"""
        registry = HandlerRegistry()

        # Verify handler types zijn geregistreerd
        event_types = registry.registered_event_types
        assert "UserCreated" in event_types
        assert "UserUpdated" in event_types
        assert "ActivityCreated" in event_types
        assert "ParticipantJoined" in event_types

    def test_get_handlers_for_event_type(self):
        """Test ophalen van handlers voor een event type"""
        registry = HandlerRegistry()

        # UserCreated heeft 2 handlers
        handlers = registry.get_handlers("UserCreated")
        assert len(handlers) == 2
        handler_names = [h.handler_name for h in handlers]
        assert "UserCreatedHandler" in handler_names
        assert "UserStatisticsHandler" in handler_names

    def test_get_handlers_for_unknown_event(self):
        """Test ophalen van handlers voor onbekend event"""
        registry = HandlerRegistry()

        handlers = registry.get_handlers("UnknownEvent")
        assert len(handlers) == 0
        assert handlers == []

    def test_has_handlers(self):
        """Test has_handlers check"""
        registry = HandlerRegistry()

        assert registry.has_handlers("UserCreated") is True
        assert registry.has_handlers("UnknownEvent") is False

    def test_register_new_handler(self):
        """Test registreren van nieuwe handler"""
        registry = HandlerRegistry()

        # Get initial handler count for UserCreated
        initial_count = len(registry.get_handlers("UserCreated"))

        # Register een extra handler voor UserCreated
        handler = UserCreatedHandler()
        registry.register(handler)

        # Verify dat er nu 1 handler meer is
        new_count = len(registry.get_handlers("UserCreated"))
        assert new_count == initial_count + 1

    def test_multiple_handlers_same_event(self):
        """Test dat meerdere handlers voor hetzelfde event werken"""
        registry = HandlerRegistry()

        # UserCreated heeft al 2 handlers
        handlers = registry.get_handlers("UserCreated")
        assert len(handlers) >= 2

        # Alle handlers moeten UserCreated als event_type hebben
        for handler in handlers:
            assert handler.event_type == "UserCreated"
