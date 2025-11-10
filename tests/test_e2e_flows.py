"""
End-to-End Flow Tests
Simuleer complete event processing flows van begin tot eind
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import OutboxEvent, EventStatus, DebeziumPayload
from app.registry import handler_registry


@pytest.mark.asyncio
class TestEndToEndFlows:
    """Test complete event processing flows"""

    async def test_user_lifecycle_flow(self):
        """Test complete user lifecycle: create → update → statistics"""
        with patch("app.handlers.user_handlers.mongodb") as mock_mongodb:
            collection = AsyncMock()
            mock_mongodb.collection.return_value = collection
            collection.insert_one = AsyncMock()
            collection.update_one = AsyncMock(
                return_value=MagicMock(matched_count=1, modified_count=1)
            )

            user_id = uuid4()

            # STEP 1: User Created Event
            create_event = OutboxEvent(
                event_id=uuid4(),
                sequence_id=1,
                aggregate_id=user_id,
                aggregate_type="User",
                event_type="UserCreated",
                payload={
                    "email": "john@example.com",
                    "username": "johndoe",
                    "first_name": "John",
                    "last_name": "Doe",
                },
                status=EventStatus.PENDING,
                created_at=datetime.utcnow(),
            )

            # Get handlers for UserCreated (should be 2: main + statistics)
            handlers = handler_registry.get_handlers("UserCreated")
            assert len(handlers) == 2, "Should have 2 handlers for UserCreated"

            # Execute all handlers
            for handler in handlers:
                await handler.handle(create_event)

            # Verify both insert calls happened (user doc + statistics)
            assert collection.insert_one.call_count >= 1
            assert collection.update_one.call_count >= 1

            # STEP 2: User Updated Event
            update_event = OutboxEvent(
                event_id=uuid4(),
                sequence_id=2,
                aggregate_id=user_id,
                aggregate_type="User",
                event_type="UserUpdated",
                payload={"email": "john.doe@example.com", "bio": "Software Engineer"},
                status=EventStatus.PENDING,
                created_at=datetime.utcnow(),
            )

            update_handlers = handler_registry.get_handlers("UserUpdated")
            for handler in update_handlers:
                await handler.handle(update_event)

            # Verify update happened
            assert collection.update_one.call_count >= 2

    async def test_activity_with_participants_flow(self):
        """Test complete activity flow: create → participants join"""
        with patch("app.handlers.activity_handlers.mongodb") as mock_mongodb:
            collection = AsyncMock()
            mock_mongodb.collection.return_value = collection
            collection.insert_one = AsyncMock()
            collection.update_one = AsyncMock(
                return_value=MagicMock(matched_count=1)
            )

            activity_id = uuid4()
            creator_id = uuid4()
            participant1_id = uuid4()
            participant2_id = uuid4()

            # STEP 1: Activity Created
            create_event = OutboxEvent(
                event_id=uuid4(),
                sequence_id=1,
                aggregate_id=activity_id,
                aggregate_type="Activity",
                event_type="ActivityCreated",
                payload={
                    "title": "Weekend Hiking Trip",
                    "description": "Join us for a mountain hike",
                    "creator_user_id": str(creator_id),
                    "max_participants": 10,
                    "location_name": "Blue Mountains",
                },
                status=EventStatus.PENDING,
                created_at=datetime.utcnow(),
            )

            handlers = handler_registry.get_handlers("ActivityCreated")
            for handler in handlers:
                await handler.handle(create_event)

            collection.insert_one.assert_called_once()
            activity_doc = collection.insert_one.call_args[0][0]
            assert activity_doc["title"] == "Weekend Hiking Trip"
            assert activity_doc["participants"]["current_count"] == 0

            # STEP 2: First Participant Joins
            join_event_1 = OutboxEvent(
                event_id=uuid4(),
                sequence_id=2,
                aggregate_id=activity_id,
                aggregate_type="Activity",
                event_type="ParticipantJoined",
                payload={"user_id": str(participant1_id)},
                status=EventStatus.PENDING,
                created_at=datetime.utcnow(),
            )

            join_handlers = handler_registry.get_handlers("ParticipantJoined")
            for handler in join_handlers:
                await handler.handle(join_event_1)

            # STEP 3: Second Participant Joins
            join_event_2 = OutboxEvent(
                event_id=uuid4(),
                sequence_id=3,
                aggregate_id=activity_id,
                aggregate_type="Activity",
                event_type="ParticipantJoined",
                payload={"user_id": str(participant2_id)},
                status=EventStatus.PENDING,
                created_at=datetime.utcnow(),
            )

            for handler in join_handlers:
                await handler.handle(join_event_2)

            # Verify both participants were added
            assert collection.update_one.call_count == 2

    async def test_debezium_to_handler_full_flow(self):
        """Test complete CDC flow: Debezium message → Event → Handler"""
        with patch("app.handlers.user_handlers.mongodb") as mock_mongodb:
            collection = AsyncMock()
            mock_mongodb.collection.return_value = collection
            collection.insert_one = AsyncMock()

            event_id = uuid4()
            aggregate_id = uuid4()

            # Simulate Debezium CDC message (from Kafka)
            debezium_message = DebeziumPayload(
                op="c",  # create operation
                ts_ms=1699876543210,
                after={
                    "event_id": str(event_id),
                    "sequence_id": 1,
                    "aggregate_id": str(aggregate_id),
                    "aggregate_type": "User",
                    "event_type": "UserCreated",
                    "payload": {
                        "email": "alice@example.com",
                        "username": "alice",
                        "first_name": "Alice",
                        "last_name": "Smith",
                    },
                    "status": "pending",
                    "retry_count": 0,
                    "created_at": datetime.utcnow().isoformat(),
                },
                source={
                    "version": "2.4",
                    "connector": "postgresql",
                    "name": "postgres",
                    "table": "event_outbox",
                },
            )

            # Convert Debezium message to OutboxEvent
            event = debezium_message.to_outbox_event()
            assert event.event_id == event_id
            assert event.event_type == "UserCreated"

            # Process through handlers
            handlers = handler_registry.get_handlers(event.event_type)
            for handler in handlers:
                await handler.handle(event)

            # Verify processing
            assert collection.insert_one.call_count >= 1
            user_doc = collection.insert_one.call_args[0][0]
            assert user_doc["email"] == "alice@example.com"

    async def test_multiple_events_sequence(self):
        """Test processing a sequence of multiple events in order"""
        with patch("app.handlers.user_handlers.mongodb") as mock_user_db, patch(
            "app.handlers.activity_handlers.mongodb"
        ) as mock_activity_db:

            user_collection = AsyncMock()
            mock_user_db.collection.return_value = user_collection
            user_collection.insert_one = AsyncMock()

            activity_collection = AsyncMock()
            mock_activity_db.collection.return_value = activity_collection
            activity_collection.insert_one = AsyncMock()

            # Create 3 users and 2 activities
            events = [
                OutboxEvent(
                    event_id=uuid4(),
                    sequence_id=i + 1,
                    aggregate_id=uuid4(),
                    aggregate_type="User" if i < 3 else "Activity",
                    event_type="UserCreated" if i < 3 else "ActivityCreated",
                    payload={
                        "email": f"user{i}@example.com",
                        "username": f"user{i}",
                        "first_name": f"User{i}",
                        "last_name": "Test",
                    }
                    if i < 3
                    else {
                        "title": f"Activity {i-2}",
                        "creator_user_id": str(uuid4()),
                        "max_participants": 10,
                    },
                    status=EventStatus.PENDING,
                    created_at=datetime.utcnow(),
                )
                for i in range(5)
            ]

            # Process all events
            for event in events:
                handlers = handler_registry.get_handlers(event.event_type)
                for handler in handlers:
                    await handler.handle(event)

            # Verify all were processed
            # 3 users + statistics updates
            assert user_collection.insert_one.call_count >= 3
            # 2 activities
            assert activity_collection.insert_one.call_count == 2


@pytest.mark.asyncio
class TestErrorRecoveryFlows:
    """Test error handling and recovery scenarios"""

    async def test_handler_failure_isolation(self):
        """Test that one handler failure doesn't stop others"""
        with patch("app.handlers.user_handlers.mongodb") as mock_mongodb:
            # First handler will fail
            collection = AsyncMock()
            collection.insert_one = AsyncMock(
                side_effect=Exception("Database connection lost")
            )
            collection.update_one = AsyncMock()  # Second handler will succeed
            mock_mongodb.collection.return_value = collection

            event = OutboxEvent(
                event_id=uuid4(),
                sequence_id=1,
                aggregate_id=uuid4(),
                aggregate_type="User",
                event_type="UserCreated",
                payload={"email": "test@example.com", "username": "test"},
                status=EventStatus.PENDING,
                created_at=datetime.utcnow(),
            )

            handlers = handler_registry.get_handlers("UserCreated")
            errors = []

            # Try to execute all handlers, collecting errors
            for handler in handlers:
                try:
                    await handler.handle(event)
                except Exception as e:
                    errors.append((handler.handler_name, str(e)))

            # We expect one handler to fail (UserCreatedHandler)
            # But UserStatisticsHandler should still execute
            assert len(errors) >= 1
            # Statistics handler should have been attempted
            assert collection.update_one.called or collection.insert_one.call_count > 1

    async def test_concurrent_event_processing(self):
        """Test processing multiple events concurrently"""
        import asyncio

        with patch("app.handlers.user_handlers.mongodb") as mock_mongodb:
            collection = AsyncMock()
            mock_mongodb.collection.return_value = collection
            collection.insert_one = AsyncMock()

            # Create 10 concurrent events
            events = [
                OutboxEvent(
                    event_id=uuid4(),
                    sequence_id=i,
                    aggregate_id=uuid4(),
                    aggregate_type="User",
                    event_type="UserCreated",
                    payload={
                        "email": f"user{i}@example.com",
                        "username": f"user{i}",
                        "first_name": f"User{i}",
                        "last_name": "Test",
                    },
                    status=EventStatus.PENDING,
                    created_at=datetime.utcnow(),
                )
                for i in range(10)
            ]

            # Process all events concurrently
            async def process_event(event):
                handlers = handler_registry.get_handlers(event.event_type)
                for handler in handlers:
                    await handler.handle(event)

            # Run all concurrently
            await asyncio.gather(*[process_event(e) for e in events])

            # All events should be processed
            # 10 events × 2 handlers (UserCreatedHandler + UserStatisticsHandler)
            assert collection.insert_one.call_count >= 10
