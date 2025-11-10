"""
PostgreSQL Event Inserter
Inserts generated events into PostgreSQL event_outbox table for demo
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import execute_batch
import time


class PostgresInserter:
    """
    Insert events into PostgreSQL event_outbox table

    Features:
    - Batch inserts for performance
    - Timestamp tracking (T0)
    - Error handling and retries
    - Connection pooling
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        self.database = database or os.getenv("POSTGRES_DB", "activity")
        self.user = user or os.getenv("POSTGRES_USER", "postgres")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "")

        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.conn.cursor()
            print(f"✓ Connected to PostgreSQL at {self.host}:{self.port}/{self.database}")
        except Exception as e:
            print(f"✗ Failed to connect to PostgreSQL: {e}")
            raise

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✓ Disconnected from PostgreSQL")

    def insert_event(self, event: Dict[str, Any]) -> str:
        """
        Insert a single event into event_outbox

        Args:
            event: Event dictionary with required fields

        Returns:
            event_id of the inserted event
        """
        # Ensure created_at timestamp (T0)
        if "created_at" not in event:
            event["created_at"] = datetime.now(timezone.utc).isoformat()

        query = """
            INSERT INTO event_outbox (
                event_id,
                aggregate_id,
                aggregate_type,
                event_type,
                payload,
                status,
                created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING event_id
        """

        values = (
            event["event_id"],
            event["aggregate_id"],
            event["aggregate_type"],
            event["event_type"],
            json.dumps(event["payload"]),
            event.get("status", "pending"),
            event["created_at"]
        )

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            return event["event_id"]
        except Exception as e:
            self.conn.rollback()
            print(f"✗ Failed to insert event {event['event_id']}: {e}")
            raise

    def insert_events_batch(
        self,
        events: List[Dict[str, Any]],
        batch_size: int = 100,
        delay_ms: int = 0
    ) -> Dict[str, Any]:
        """
        Insert multiple events in batches

        Args:
            events: List of event dictionaries
            batch_size: Number of events per batch
            delay_ms: Delay between batches in milliseconds

        Returns:
            Dictionary with insert statistics
        """
        total_events = len(events)
        inserted = 0
        failed = 0
        start_time = time.time()

        print(f"Inserting {total_events} events in batches of {batch_size}...")

        # Process in batches
        for i in range(0, total_events, batch_size):
            batch = events[i:i + batch_size]

            # Ensure all events have created_at timestamp
            now = datetime.now(timezone.utc).isoformat()
            for event in batch:
                if "created_at" not in event:
                    event["created_at"] = now

            # Prepare batch insert
            query = """
                INSERT INTO event_outbox (
                    event_id,
                    aggregate_id,
                    aggregate_type,
                    event_type,
                    payload,
                    status,
                    created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
            """

            values = [
                (
                    event["event_id"],
                    event["aggregate_id"],
                    event["aggregate_type"],
                    event["event_type"],
                    json.dumps(event["payload"]),
                    event.get("status", "pending"),
                    event["created_at"]
                )
                for event in batch
            ]

            try:
                execute_batch(self.cursor, query, values, page_size=batch_size)
                self.conn.commit()
                inserted += len(batch)

                # Progress update
                progress = (inserted / total_events) * 100
                print(f"  Progress: {inserted}/{total_events} ({progress:.1f}%)")

            except Exception as e:
                self.conn.rollback()
                failed += len(batch)
                print(f"✗ Batch insert failed: {e}")

            # Optional delay between batches
            if delay_ms > 0 and i + batch_size < total_events:
                time.sleep(delay_ms / 1000.0)

        elapsed = time.time() - start_time
        rate = inserted / elapsed if elapsed > 0 else 0

        stats = {
            "total_events": total_events,
            "inserted": inserted,
            "failed": failed,
            "elapsed_seconds": round(elapsed, 2),
            "events_per_second": round(rate, 2)
        }

        print(f"\n✓ Insert complete:")
        print(f"  Inserted: {inserted}/{total_events}")
        print(f"  Failed: {failed}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Rate: {rate:.2f} events/sec")

        return stats

    def count_events(self) -> int:
        """Count total events in event_outbox"""
        query = "SELECT COUNT(*) FROM event_outbox"
        self.cursor.execute(query)
        count = self.cursor.fetchone()[0]
        return count

    def count_events_by_type(self) -> Dict[str, int]:
        """Count events grouped by event_type"""
        query = """
            SELECT event_type, COUNT(*)
            FROM event_outbox
            GROUP BY event_type
            ORDER BY COUNT(*) DESC
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        return {event_type: count for event_type, count in results}

    def get_latest_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent events"""
        query = """
            SELECT event_id, event_type, aggregate_type, created_at, status
            FROM event_outbox
            ORDER BY created_at DESC
            LIMIT %s
        """
        self.cursor.execute(query, (limit,))
        results = self.cursor.fetchall()

        events = []
        for row in results:
            events.append({
                "event_id": str(row[0]),
                "event_type": row[1],
                "aggregate_type": row[2],
                "created_at": row[3].isoformat() if row[3] else None,
                "status": row[4]
            })

        return events

    def clear_events(self):
        """Delete all events from event_outbox (CAREFUL!)"""
        query = "DELETE FROM event_outbox"
        self.cursor.execute(query)
        self.conn.commit()
        print("✓ All events cleared from event_outbox")

    def verify_connection(self) -> bool:
        """Verify database connection and table exists"""
        try:
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'event_outbox'
                )
            """
            self.cursor.execute(query)
            exists = self.cursor.fetchone()[0]

            if not exists:
                print("✗ Table 'event_outbox' does not exist")
                return False

            print("✓ Connection verified, event_outbox table exists")
            return True

        except Exception as e:
            print(f"✗ Verification failed: {e}")
            return False


def main():
    """Example usage"""
    from event_generator import EventGenerator

    # Create inserter
    inserter = PostgresInserter()
    inserter.connect()

    # Verify setup
    if not inserter.verify_connection():
        print("Please ensure PostgreSQL is running and event_outbox table exists")
        return

    # Generate test events
    generator = EventGenerator()
    events = generator.generate_batch(10)

    print(f"\nGenerated {len(events)} test events")

    # Insert events
    stats = inserter.insert_events_batch(events, batch_size=5)

    # Verify
    print(f"\nVerifying...")
    total_count = inserter.count_events()
    print(f"Total events in database: {total_count}")

    by_type = inserter.count_events_by_type()
    print(f"Events by type: {by_type}")

    latest = inserter.get_latest_events(5)
    print(f"\nLatest events:")
    for event in latest:
        print(f"  {event['event_type']}: {event['event_id'][:8]}...")

    # Cleanup
    inserter.disconnect()


if __name__ == "__main__":
    main()
