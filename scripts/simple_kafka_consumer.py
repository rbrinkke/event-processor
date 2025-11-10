#!/usr/bin/env python3
"""
Simple Kafka Consumer - No MongoDB required
Just reads and displays messages from Kafka
"""

import asyncio
import json
from aiokafka import AIOKafkaConsumer


async def consume_events():
    """Consume events from Kafka"""

    print("=" * 70)
    print("🚀 SIMPLE KAFKA CONSUMER TEST")
    print("=" * 70)

    # Create consumer
    consumer = AIOKafkaConsumer(
        'postgres.activity.event_outbox',
        bootstrap_servers='localhost:9092',
        group_id='test-consumer-group',
        auto_offset_reset='earliest',  # Read from beginning
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    print("\n📋 Configuration:")
    print(f"   Bootstrap servers: localhost:9092")
    print(f"   Topic: postgres.activity.event_outbox")
    print(f"   Group ID: test-consumer-group")

    try:
        # Start consumer
        await consumer.start()
        print("\n✅ Connected to Kafka!")

        print("\n📥 Consuming messages (10 seconds or 10 messages)...")
        print("-" * 70)

        message_count = 0
        start_time = asyncio.get_event_loop().time()

        async for message in consumer:
            message_count += 1

            print(f"\n📨 Message #{message_count}:")
            print(f"   Partition: {message.partition}")
            print(f"   Offset: {message.offset}")
            print(f"   Timestamp: {message.timestamp}")

            # Parse Debezium message
            value = message.value
            if 'after' in value:
                event_data = value['after']
                print(f"\n   🎯 Event Details:")
                print(f"      Event Type: {event_data.get('event_type', 'N/A')}")
                print(f"      Aggregate Type: {event_data.get('aggregate_type', 'N/A')}")
                print(f"      Event ID: {event_data.get('event_id', 'N/A')}")
                print(f"      Aggregate ID: {event_data.get('aggregate_id', 'N/A')}")
                print(f"      Status: {event_data.get('status', 'N/A')}")

                # Show payload
                payload = event_data.get('payload', {})
                print(f"\n   📦 Payload:")
                for key, val in payload.items():
                    print(f"      {key}: {val}")

            # Stop after 10 messages or 10 seconds
            if message_count >= 10:
                print(f"\n⏱️  Message limit reached")
                break

            if asyncio.get_event_loop().time() - start_time > 10:
                print(f"\n⏱️  Time limit reached")
                break

        print("-" * 70)
        print(f"\n📊 Summary:")
        print(f"   Total messages consumed: {message_count}")
        print(f"   Time elapsed: {asyncio.get_event_loop().time() - start_time:.2f}s")

        print(f"\n✅ Test completed successfully!")

    except KeyboardInterrupt:
        print(f"\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop consumer
        await consumer.stop()
        print(f"\n✅ Consumer stopped")


if __name__ == "__main__":
    asyncio.run(consume_events())
