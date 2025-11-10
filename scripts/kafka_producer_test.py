#!/usr/bin/env python3
"""
Kafka Producer Test Script
Simuleert Debezium CDC events naar Kafka
"""

import json
import asyncio
from datetime import datetime
from uuid import uuid4
from aiokafka import AIOKafkaProducer


async def send_test_event():
    """Send test event to Kafka"""

    # Create Kafka producer
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    # Start producer
    await producer.start()
    print("✅ Kafka Producer connected to localhost:9092")

    try:
        # Create test Debezium CDC message
        event_id = str(uuid4())
        aggregate_id = str(uuid4())

        debezium_message = {
            "op": "c",  # create operation
            "ts_ms": int(datetime.utcnow().timestamp() * 1000),
            "after": {
                "event_id": event_id,
                "sequence_id": 1,
                "aggregate_id": aggregate_id,
                "aggregate_type": "User",
                "event_type": "UserCreated",
                "payload": {
                    "email": "kafka-test@example.com",
                    "username": "kafkauser",
                    "first_name": "Kafka",
                    "last_name": "Test"
                },
                "status": "pending",
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat()
            },
            "source": {
                "version": "2.4",
                "connector": "postgresql",
                "name": "postgres",
                "ts_ms": int(datetime.utcnow().timestamp() * 1000),
                "db": "activity",
                "schema": "public",
                "table": "event_outbox"
            }
        }

        # Send to Kafka
        topic = "postgres.activity.event_outbox"
        await producer.send_and_wait(topic, value=debezium_message)

        print(f"📤 Sent UserCreated event to Kafka:")
        print(f"   Event ID: {event_id}")
        print(f"   Aggregate ID: {aggregate_id}")
        print(f"   Topic: {topic}")
        print(f"   Email: kafka-test@example.com")

    finally:
        # Stop producer
        await producer.stop()
        print("✅ Kafka Producer stopped")


async def send_multiple_events():
    """Send multiple test events"""

    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    await producer.start()
    print("✅ Kafka Producer connected")

    try:
        topic = "postgres.activity.event_outbox"

        # UserCreated
        user_id = str(uuid4())
        await producer.send_and_wait(topic, value={
            "op": "c",
            "ts_ms": int(datetime.utcnow().timestamp() * 1000),
            "after": {
                "event_id": str(uuid4()),
                "sequence_id": 1,
                "aggregate_id": user_id,
                "aggregate_type": "User",
                "event_type": "UserCreated",
                "payload": {"email": "user@test.com", "username": "testuser"},
                "status": "pending",
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat()
            },
            "source": {"version": "2.4"}
        })
        print("📤 Sent UserCreated event")

        # ActivityCreated
        activity_id = str(uuid4())
        await producer.send_and_wait(topic, value={
            "op": "c",
            "ts_ms": int(datetime.utcnow().timestamp() * 1000),
            "after": {
                "event_id": str(uuid4()),
                "sequence_id": 2,
                "aggregate_id": activity_id,
                "aggregate_type": "Activity",
                "event_type": "ActivityCreated",
                "payload": {
                    "title": "Kafka Test Activity",
                    "description": "Activity from Kafka",
                    "creator_user_id": user_id,
                    "max_participants": 10
                },
                "status": "pending",
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat()
            },
            "source": {"version": "2.4"}
        })
        print("📤 Sent ActivityCreated event")

        # ParticipantJoined
        await producer.send_and_wait(topic, value={
            "op": "c",
            "ts_ms": int(datetime.utcnow().timestamp() * 1000),
            "after": {
                "event_id": str(uuid4()),
                "sequence_id": 3,
                "aggregate_id": activity_id,
                "aggregate_type": "Activity",
                "event_type": "ParticipantJoined",
                "payload": {"user_id": user_id},
                "status": "pending",
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat()
            },
            "source": {"version": "2.4"}
        })
        print("📤 Sent ParticipantJoined event")

        print(f"\n✅ Sent 3 events to Kafka topic: {topic}")

    finally:
        await producer.stop()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "multiple":
        print("Sending multiple test events...")
        asyncio.run(send_multiple_events())
    else:
        print("Sending single test event...")
        asyncio.run(send_test_event())
