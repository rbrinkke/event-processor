"""
Handler Tests
Tests voor event handlers met mocked MongoDB
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import OutboxEvent, EventStatus
from app.handlers.user_handlers import (
    UserCreatedHandler,
    UserUpdatedHandler,
    UserStatisticsHandler,
)
from app.handlers.activity_handlers import (
    ActivityCreatedHandler,
    ParticipantJoinedHandler,
)


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB collection"""
    with patch("app.handlers.user_handlers.mongodb") as mock:
        collection = AsyncMock()
        mock.collection.return_value = collection
        yield collection


@pytest.fixture
def sample_user_event():
    """Create sample user created event"""
    return OutboxEvent(
        event_id=uuid4(),
        sequence_id=1,
        aggregate_id=uuid4(),
        aggregate_type="User",
        event_type="UserCreated",
        payload={
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
        },
        status=EventStatus.PENDING,
        created_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
class TestUserCreatedHandler:
    """Test UserCreatedHandler"""

    async def test_event_type(self):
        """Test dat handler het juiste event type heeft"""
        handler = UserCreatedHandler()
        assert handler.event_type == "UserCreated"

    async def test_handler_name(self):
        """Test handler name property"""
        handler = UserCreatedHandler()
        assert handler.handler_name == "UserCreatedHandler"

    async def test_handle_user_created(self, mock_mongodb, sample_user_event):
        """Test verwerking van UserCreated event"""
        handler = UserCreatedHandler()

        # Mock MongoDB insert
        mock_mongodb.insert_one = AsyncMock()

        # Handle event
        await handler.handle(sample_user_event)

        # Verify MongoDB insert was called
        mock_mongodb.insert_one.assert_called_once()

        # Verify document structure
        call_args = mock_mongodb.insert_one.call_args[0][0]
        assert call_args["_id"] == str(sample_user_event.aggregate_id)
        assert call_args["email"] == "test@example.com"
        assert call_args["username"] == "testuser"
        assert call_args["name"] == "Test User"

    async def test_validate_event(self, sample_user_event):
        """Test event validation"""
        handler = UserCreatedHandler()
        is_valid = await handler.validate(sample_user_event)
        assert is_valid is True


@pytest.mark.asyncio
class TestUserUpdatedHandler:
    """Test UserUpdatedHandler"""

    async def test_event_type(self):
        """Test event type"""
        handler = UserUpdatedHandler()
        assert handler.event_type == "UserUpdated"

    async def test_handle_user_updated(self, mock_mongodb):
        """Test user update handling"""
        handler = UserUpdatedHandler()

        event = OutboxEvent(
            event_id=uuid4(),
            sequence_id=2,
            aggregate_id=uuid4(),
            aggregate_type="User",
            event_type="UserUpdated",
            payload={"email": "newemail@example.com", "first_name": "Updated"},
            status=EventStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        # Mock MongoDB update
        mock_result = MagicMock()
        mock_result.matched_count = 1
        mock_result.modified_count = 1
        mock_mongodb.update_one = AsyncMock(return_value=mock_result)

        # Handle event
        await handler.handle(event)

        # Verify update was called
        mock_mongodb.update_one.assert_called_once()

        # Verify update fields
        call_args = mock_mongodb.update_one.call_args[0]
        assert call_args[0] == {"_id": str(event.aggregate_id)}
        update_doc = call_args[1]["$set"]
        assert "email" in update_doc
        assert update_doc["email"] == "newemail@example.com"

    async def test_handle_user_not_found(self, mock_mongodb):
        """Test handling wanneer user niet gevonden wordt"""
        handler = UserUpdatedHandler()

        event = OutboxEvent(
            event_id=uuid4(),
            sequence_id=2,
            aggregate_id=uuid4(),
            aggregate_type="User",
            event_type="UserUpdated",
            payload={"email": "test@example.com"},
            status=EventStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        # Mock MongoDB update - user not found
        mock_result = MagicMock()
        mock_result.matched_count = 0
        mock_mongodb.update_one = AsyncMock(return_value=mock_result)

        # Should raise ValueError
        with pytest.raises(ValueError, match="User not found"):
            await handler.handle(event)


@pytest.mark.asyncio
class TestUserStatisticsHandler:
    """Test UserStatisticsHandler"""

    async def test_event_type(self):
        """Test dat statistics handler ook naar UserCreated luistert"""
        handler = UserStatisticsHandler()
        assert handler.event_type == "UserCreated"

    async def test_handle_statistics_update(self, mock_mongodb, sample_user_event):
        """Test statistics update"""
        handler = UserStatisticsHandler()

        # Mock MongoDB update
        mock_mongodb.update_one = AsyncMock()

        # Handle event
        await handler.handle(sample_user_event)

        # Verify statistics update
        mock_mongodb.update_one.assert_called_once()
        call_args = mock_mongodb.update_one.call_args[0]
        assert call_args[0] == {"_id": "global_stats"}
        assert "$inc" in call_args[1]
        assert call_args[1]["$inc"]["total_users"] == 1


@pytest.mark.asyncio
class TestActivityCreatedHandler:
    """Test ActivityCreatedHandler"""

    async def test_event_type(self):
        """Test event type"""
        handler = ActivityCreatedHandler()
        assert handler.event_type == "ActivityCreated"

    async def test_handle_activity_created(self):
        """Test activity creation"""
        with patch("app.handlers.activity_handlers.mongodb") as mock_mongodb:
            collection = AsyncMock()
            mock_mongodb.collection.return_value = collection

            handler = ActivityCreatedHandler()

            event = OutboxEvent(
                event_id=uuid4(),
                sequence_id=1,
                aggregate_id=uuid4(),
                aggregate_type="Activity",
                event_type="ActivityCreated",
                payload={
                    "title": "Test Activity",
                    "description": "Test description",
                    "creator_user_id": str(uuid4()),
                    "max_participants": 10,
                },
                status=EventStatus.PENDING,
                created_at=datetime.utcnow(),
            )

            # Mock MongoDB insert
            collection.insert_one = AsyncMock()

            # Handle event
            await handler.handle(event)

            # Verify insert
            collection.insert_one.assert_called_once()
            doc = collection.insert_one.call_args[0][0]
            assert doc["_id"] == str(event.aggregate_id)
            assert doc["title"] == "Test Activity"
            assert doc["participants"]["current_count"] == 0


@pytest.mark.asyncio
class TestParticipantJoinedHandler:
    """Test ParticipantJoinedHandler"""

    async def test_event_type(self):
        """Test event type"""
        handler = ParticipantJoinedHandler()
        assert handler.event_type == "ParticipantJoined"

    async def test_handle_participant_joined(self):
        """Test participant joining"""
        with patch("app.handlers.activity_handlers.mongodb") as mock_mongodb:
            collection = AsyncMock()
            mock_mongodb.collection.return_value = collection

            handler = ParticipantJoinedHandler()

            user_id = str(uuid4())
            activity_id = uuid4()

            event = OutboxEvent(
                event_id=uuid4(),
                sequence_id=1,
                aggregate_id=activity_id,
                aggregate_type="Activity",
                event_type="ParticipantJoined",
                payload={"user_id": user_id},
                status=EventStatus.PENDING,
                created_at=datetime.utcnow(),
            )

            # Mock MongoDB update
            mock_result = MagicMock()
            mock_result.matched_count = 1
            collection.update_one = AsyncMock(return_value=mock_result)

            # Handle event
            await handler.handle(event)

            # Verify update
            collection.update_one.assert_called_once()
            call_args = collection.update_one.call_args[0]
            assert call_args[0] == {"_id": str(activity_id)}
            assert "$addToSet" in call_args[1]
            assert "$inc" in call_args[1]
            assert call_args[1]["$inc"]["participants.current_count"] == 1
