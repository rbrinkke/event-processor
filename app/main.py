"""
Main Application Entry Point
Orchestrates de event processing service
"""

import asyncio
import signal
import sys

import structlog

from app.config import settings
from app.consumer import EventConsumer
from app.database.mongodb import mongodb
from app.registry import handler_registry

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()


class Application:
    """
    Main Application

    Beheert de lifecycle van de event processor
    """

    def __init__(self):
        self.consumer = EventConsumer()
        self.shutdown_event = asyncio.Event()

    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""

        def signal_handler(sig, frame):
            logger.info("shutdown_signal_received", signal=sig)
            self.shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def startup(self):
        """Application startup"""
        logger.info(
            "application_starting",
            version="1.0.0",
            kafka_topic=settings.kafka_topic,
            mongodb_database=settings.mongodb_database,
        )

        # Connect to MongoDB
        await mongodb.connect()

        # Initialize Kafka consumer
        await self.consumer.initialize()

        # Log registered handlers
        logger.info(
            "handlers_ready", event_types=handler_registry.registered_event_types
        )

        logger.info("application_started")

    async def shutdown(self):
        """Application shutdown"""
        logger.info("application_shutting_down")

        # Stop consumer
        await self.consumer.shutdown()

        # Disconnect MongoDB
        await mongodb.disconnect()

        logger.info("application_stopped")

    async def run(self):
        """Main application loop"""
        try:
            # Startup
            await self.startup()

            # Start consuming events
            consume_task = asyncio.create_task(self.consumer.consume())

            # Wait for shutdown signal
            await self.shutdown_event.wait()

            # Cancel consumption
            consume_task.cancel()
            try:
                await consume_task
            except asyncio.CancelledError:
                pass

        except Exception as e:
            logger.error("application_error", error=str(e), error_type=type(e).__name__)
            raise
        finally:
            await self.shutdown()


async def main():
    """Entry point"""
    app = Application()
    app.setup_signal_handlers()

    try:
        await app.run()
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt")
    except Exception as e:
        logger.error("fatal_error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
