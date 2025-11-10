"""
Kafka Consumer
High-performance async Kafka consumer met error handling
"""

import asyncio
import json
from typing import Optional, Dict, Any
import time

from aiokafka import AIOKafkaConsumer
import structlog

from app.config import settings
from app.models import DebeziumPayload, ProcessingResult
from app.registry import handler_registry

logger = structlog.get_logger()


class EventConsumer:
    """
    Kafka Event Consumer

    Consumeert events van Kafka topic en routeert ze naar handlers
    """

    def __init__(self):
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        self._processing_count = 0
        self._error_count = 0
        self._start_time = time.time()

    async def initialize(self):
        """Initialize Kafka consumer"""
        try:
            self.consumer = AIOKafkaConsumer(
                settings.kafka_topic,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=settings.kafka_group_id,
                auto_offset_reset=settings.kafka_auto_offset_reset,
                enable_auto_commit=settings.kafka_enable_auto_commit,
                max_poll_records=settings.kafka_max_poll_records,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )

            await self.consumer.start()

            logger.info(
                "kafka_consumer_started",
                topic=settings.kafka_topic,
                group_id=settings.kafka_group_id,
                bootstrap_servers=settings.kafka_bootstrap_servers,
            )

        except Exception as e:
            logger.error("kafka_consumer_init_failed", error=str(e))
            raise

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("kafka_consumer_shutting_down")
        self.running = False

        if self.consumer:
            await self.consumer.stop()

        # Log statistics
        uptime = time.time() - self._start_time
        logger.info(
            "kafka_consumer_stopped",
            total_processed=self._processing_count,
            total_errors=self._error_count,
            uptime_seconds=round(uptime, 2),
        )

    async def process_message(self, message) -> Optional[ProcessingResult]:
        """
        Process a single Kafka message

        Args:
            message: Kafka ConsumerRecord

        Returns:
            ProcessingResult or None if skipped
        """
        start_time = time.time()

        try:
            # Parse Debezium CDC message
            debezium_payload = DebeziumPayload(**message.value)

            # Skip deletes and snapshots
            if debezium_payload.op in ("d", "r"):
                logger.debug(
                    "message_skipped",
                    op=debezium_payload.op,
                    partition=message.partition,
                    offset=message.offset,
                )
                return None

            # Convert to OutboxEvent
            event = debezium_payload.to_outbox_event()

            # Get handlers for this event type
            handlers = handler_registry.get_handlers(event.event_type)

            if not handlers:
                logger.warning(
                    "no_handlers_found",
                    event_type=event.event_type,
                    event_id=str(event.event_id),
                )
                return None

            # Execute all handlers for this event
            logger.info(
                "processing_event",
                event_type=event.event_type,
                event_id=str(event.event_id),
                handler_count=len(handlers),
            )

            for handler in handlers:
                try:
                    # Validate event (if handler implements validation)
                    if not await handler.validate(event):
                        logger.warning(
                            "event_validation_failed",
                            handler=handler.handler_name,
                            event_type=event.event_type,
                            event_id=str(event.event_id),
                        )
                        continue

                    # Process event
                    await handler.handle(event)

                except Exception as handler_error:
                    logger.error(
                        "handler_failed",
                        handler=handler.handler_name,
                        event_type=event.event_type,
                        event_id=str(event.event_id),
                        error=str(handler_error),
                        error_type=type(handler_error).__name__,
                    )
                    # Continue met volgende handler (niet stoppen!)
                    self._error_count += 1

            # Processing complete
            processing_time = (time.time() - start_time) * 1000  # milliseconds
            self._processing_count += 1

            logger.info(
                "event_processed",
                event_type=event.event_type,
                event_id=str(event.event_id),
                processing_time_ms=round(processing_time, 2),
                total_processed=self._processing_count,
            )

            return ProcessingResult(
                success=True,
                event_id=event.event_id,
                event_type=event.event_type,
                handler_name="multiple",
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(
                "message_processing_failed",
                error=str(e),
                error_type=type(e).__name__,
                partition=message.partition,
                offset=message.offset,
            )
            self._error_count += 1
            return None

    async def consume(self):
        """
        Main consumption loop

        Consumeert berichten van Kafka en verwerkt ze asynchroon
        """
        self.running = True

        logger.info("starting_event_consumption")

        try:
            async for message in self.consumer:
                if not self.running:
                    logger.info("consumption_stopped_by_flag")
                    break

                # Process message
                await self.process_message(message)

                # Commit offset (manual commit)
                if not settings.kafka_enable_auto_commit:
                    await self.consumer.commit()

        except asyncio.CancelledError:
            logger.info("consumption_cancelled")
        except Exception as e:
            logger.error("consumption_error", error=str(e), error_type=type(e).__name__)
            raise
        finally:
            await self.shutdown()

    @property
    def stats(self) -> Dict[str, Any]:
        """Get consumer statistics"""
        return {
            "running": self.running,
            "total_processed": self._processing_count,
            "total_errors": self._error_count,
            "uptime_seconds": round(time.time() - self._start_time, 2),
        }
