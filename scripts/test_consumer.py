#!/usr/bin/env python3
"""
Test Event Processor Consumer
Test consuming events from Kafka
"""

import asyncio
from app.consumer import EventConsumer
from app.config import Settings


async def test_consumer():
    """Test consuming events from Kafka"""

    print("=" * 60)
    print("🚀 EVENT PROCESSOR CONSUMER TEST")
    print("=" * 60)

    # Initialize settings
    settings = Settings()
    print(f"\n📋 Configuration:")
    print(f"   Kafka: {settings.kafka_bootstrap_servers}")
    print(f"   Topic: {settings.kafka_topic}")
    print(f"   Group: {settings.kafka_group_id}")

    # Initialize consumer
    consumer = EventConsumer()
    print(f"\n✅ Consumer initialized")

    try:
        # Start consumer
        print(f"\n🔄 Starting consumer...")
        await consumer.start()
        print(f"✅ Consumer started and connected to Kafka!")

        # Consume messages for 10 seconds
        print(f"\n📥 Consuming messages (10 seconds)...")
        print("-" * 60)

        start_time = asyncio.get_event_loop().time()
        message_count = 0

        async for message in consumer:
            message_count += 1

            print(f"\n📨 Message #{message_count}:")
            print(f"   Topic: {message.topic}")
            print(f"   Partition: {message.partition}")
            print(f"   Offset: {message.offset}")
            print(f"   Key: {message.key}")

            # Process message
            result = await consumer.process_message(message)

            if result:
                print(f"   ✅ Processed: {result.event_type}")
                print(f"      Handler: {result.handler_name}")
                print(f"      Time: {result.processing_time_ms:.2f}ms")
                if not result.success:
                    print(f"      ❌ Error: {result.error}")
            else:
                print(f"   ⏭️  Skipped (no handlers or invalid)")

            # Stop after 10 seconds
            if asyncio.get_event_loop().time() - start_time > 10:
                print(f"\n⏱️  Time limit reached")
                break

        print("-" * 60)
        print(f"\n📊 Statistics:")
        stats = consumer.stats
        for key, value in stats.items():
            print(f"   {key}: {value}")

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
    asyncio.run(test_consumer())
