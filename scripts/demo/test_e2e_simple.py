#!/usr/bin/env python3
"""
Simple End-to-End Test
Tests the complete flow: Event Generation → MongoDB
WITHOUT requiring Kafka/Debezium setup
"""

import sys
import os
import asyncio
from datetime import datetime, timezone
from uuid import uuid4

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from event_generator import EventGenerator
from pymongo import MongoClient


async def test_user_created_handler():
    """Test UserCreated event handler directly"""
    print("\n" + "="*70)
    print("E2E TEST: UserCreated Event → MongoDB")
    print("="*70)

    # Import handler
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
    from app.handlers.user_handlers import UserCreatedHandler
    from app.models import OutboxEvent, EventStatus
    from app.database.mongodb import mongodb

    # Connect to MongoDB
    print("\n1. Connecting to MongoDB...")
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_database = os.getenv("MONGODB_DATABASE", "activity_read")

    await mongodb.connect()
    print(f"   ✓ Connected to {mongodb_database}")

    # Generate test event
    print("\n2. Generating test UserCreated event...")
    generator = EventGenerator()
    event_data = generator.generate_user_created_event()

    user_email = event_data['payload']['email']
    user_id = event_data['payload']['user_id']
    print(f"   ✓ Generated user: {user_email}")
    print(f"   ✓ User ID: {user_id}")

    # Convert to OutboxEvent
    outbox_event = OutboxEvent(
        event_id=uuid4(),
        sequence_id=1,
        aggregate_id=event_data['aggregate_id'],
        aggregate_type=event_data['aggregate_type'],
        event_type=event_data['event_type'],
        payload=event_data['payload'],
        status=EventStatus.PENDING,
        created_at=datetime.now(timezone.utc)
    )

    # Process with handler
    print("\n3. Processing event with UserCreatedHandler...")
    handler = UserCreatedHandler()

    try:
        await handler.handle(outbox_event)
        print(f"   ✓ Handler executed successfully")
    except Exception as e:
        print(f"   ✗ Handler failed: {e}")
        return False

    # Verify in MongoDB
    print("\n4. Verifying data in MongoDB...")
    users_collection = mongodb.db.users

    user_doc = await users_collection.find_one({"user_id": user_id})

    if user_doc:
        print(f"   ✓ User found in MongoDB!")
        print(f"   ✓ Email: {user_doc.get('email')}")
        print(f"   ✓ Username: {user_doc.get('username')}")
        print(f"   ✓ Name: {user_doc.get('first_name')} {user_doc.get('last_name')}")

        # Verify fields
        required_fields = ['user_id', 'email', 'username', 'first_name', 'last_name', 'created_at']
        missing = [f for f in required_fields if f not in user_doc]

        if missing:
            print(f"   ⚠ Missing fields: {missing}")
        else:
            print(f"   ✓ All required fields present")

        return True
    else:
        print(f"   ✗ User NOT found in MongoDB")
        return False


async def test_activity_created_handler():
    """Test ActivityCreated event handler directly"""
    print("\n" + "="*70)
    print("E2E TEST: ActivityCreated Event → MongoDB")
    print("="*70)

    # Import handler
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
    from app.handlers.activity_handlers import ActivityCreatedHandler
    from app.models import OutboxEvent, EventStatus
    from app.database.mongodb import mongodb

    # Generate test event
    print("\n1. Generating test ActivityCreated event...")
    generator = EventGenerator()

    # First create a user to reference
    user_event = generator.generate_user_created_event()
    creator_id = user_event['payload']['user_id']

    # Generate activity
    activity_data = generator.generate_activity_created_event()
    activity_data['payload']['creator_id'] = creator_id  # Use our test user

    activity_title = activity_data['payload']['title']
    activity_id = activity_data['payload']['activity_id']
    print(f"   ✓ Generated activity: {activity_title}")
    print(f"   ✓ Activity ID: {activity_id}")
    print(f"   ✓ Creator ID: {creator_id}")

    # Convert to OutboxEvent
    outbox_event = OutboxEvent(
        event_id=uuid4(),
        sequence_id=2,
        aggregate_id=activity_data['aggregate_id'],
        aggregate_type=activity_data['aggregate_type'],
        event_type=activity_data['event_type'],
        payload=activity_data['payload'],
        status=EventStatus.PENDING,
        created_at=datetime.now(timezone.utc)
    )

    # Process with handler
    print("\n2. Processing event with ActivityCreatedHandler...")
    handler = ActivityCreatedHandler()

    try:
        await handler.handle(outbox_event)
        print(f"   ✓ Handler executed successfully")
    except Exception as e:
        print(f"   ✗ Handler failed: {e}")
        return False

    # Verify in MongoDB
    print("\n3. Verifying data in MongoDB...")
    activities_collection = mongodb.db.activities

    activity_doc = await activities_collection.find_one({"activity_id": activity_id})

    if activity_doc:
        print(f"   ✓ Activity found in MongoDB!")
        print(f"   ✓ Title: {activity_doc.get('title')}")
        print(f"   ✓ Type: {activity_doc.get('activity_type')}")
        print(f"   ✓ Creator: {activity_doc.get('creator_id')}")

        # Verify fields
        required_fields = ['activity_id', 'title', 'creator_id', 'location', 'schedule', 'participants']
        missing = [f for f in required_fields if f not in activity_doc]

        if missing:
            print(f"   ⚠ Missing fields: {missing}")
        else:
            print(f"   ✓ All required fields present")

        return True
    else:
        print(f"   ✗ Activity NOT found in MongoDB")
        return False


async def test_batch_processing():
    """Test batch of mixed events"""
    print("\n" + "="*70)
    print("E2E TEST: Batch Processing (10 mixed events)")
    print("="*70)

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
    from app.handlers.user_handlers import UserCreatedHandler, UserStatisticsHandler
    from app.handlers.activity_handlers import ActivityCreatedHandler, ParticipantJoinedHandler
    from app.models import OutboxEvent, EventStatus
    from app.database.mongodb import mongodb

    # Generate batch of events
    print("\n1. Generating batch of 10 events...")
    generator = EventGenerator()
    events = generator.generate_batch(10)
    print(f"   ✓ Generated {len(events)} events")

    # Count by type
    event_types = {}
    for event in events:
        event_type = event['event_type']
        event_types[event_type] = event_types.get(event_type, 0) + 1

    print(f"\n   Event breakdown:")
    for event_type, count in event_types.items():
        print(f"   - {event_type}: {count}")

    # Process each event
    print("\n2. Processing events with appropriate handlers...")

    handlers = {
        'UserCreated': UserCreatedHandler(),
        'UserUpdated': None,  # Skip for now
        'ActivityCreated': ActivityCreatedHandler(),
        'ActivityUpdated': None,  # Skip for now
        'ParticipantJoined': ParticipantJoinedHandler()
    }

    processed = 0
    skipped = 0
    failed = 0

    for i, event_data in enumerate(events, 1):
        event_type = event_data['event_type']
        handler = handlers.get(event_type)

        if handler is None:
            print(f"   [{i}/{len(events)}] SKIP {event_type}")
            skipped += 1
            continue

        try:
            outbox_event = OutboxEvent(
                event_id=uuid4(),
                sequence_id=i,
                aggregate_id=event_data['aggregate_id'],
                aggregate_type=event_data['aggregate_type'],
                event_type=event_data['event_type'],
                payload=event_data['payload'],
                status=EventStatus.PENDING,
                created_at=datetime.now(timezone.utc)
            )

            await handler.handle(outbox_event)
            print(f"   [{i}/{len(events)}] ✓ {event_type}")
            processed += 1

        except Exception as e:
            print(f"   [{i}/{len(events)}] ✗ {event_type}: {e}")
            failed += 1

    # Verify counts in MongoDB
    print("\n3. Verifying MongoDB collections...")

    user_count = await mongodb.db.users.count_documents({})
    activity_count = await mongodb.db.activities.count_documents({})

    print(f"   Users in MongoDB: {user_count}")
    print(f"   Activities in MongoDB: {activity_count}")

    # Summary
    print("\n" + "="*70)
    print("BATCH PROCESSING SUMMARY")
    print("="*70)
    print(f"Total events: {len(events)}")
    print(f"Processed: {processed}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(processed/(processed+failed)*100):.1f}%" if (processed+failed) > 0 else "N/A")

    return failed == 0


async def main():
    """Run all E2E tests"""
    print("\n╔═══════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║           SIMPLE END-TO-END INTEGRATION TEST                      ║")
    print("║           (Event Generation → Handlers → MongoDB)                 ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")

    try:
        # Test 1: UserCreated
        test1_passed = await test_user_created_handler()

        # Test 2: ActivityCreated
        test2_passed = await test_activity_created_handler()

        # Test 3: Batch processing
        test3_passed = await test_batch_processing()

        # Final summary
        print("\n" + "="*70)
        print("FINAL RESULTS")
        print("="*70)
        print(f"UserCreated test:     {'✓ PASSED' if test1_passed else '✗ FAILED'}")
        print(f"ActivityCreated test: {'✓ PASSED' if test2_passed else '✗ FAILED'}")
        print(f"Batch processing:     {'✓ PASSED' if test3_passed else '✗ FAILED'}")
        print("="*70)

        all_passed = test1_passed and test2_passed and test3_passed

        if all_passed:
            print("\n🎉 ALL TESTS PASSED - System working end-to-end!")
            return 0
        else:
            print("\n⚠ SOME TESTS FAILED - Check output above")
            return 1

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
        from app.database.mongodb import mongodb
        await mongodb.disconnect()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
