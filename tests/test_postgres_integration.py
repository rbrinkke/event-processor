"""
PostgreSQL Integration Tests
Tests met echte PostgreSQL database in sandbox
"""

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from uuid import uuid4

from app.config import Settings


@pytest.fixture
def pg_connection():
    """Create PostgreSQL connection"""
    settings = Settings()

    conn = psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password or "",
    )
    yield conn
    conn.close()


@pytest.fixture
def pg_cursor(pg_connection):
    """Create PostgreSQL cursor"""
    cursor = pg_connection.cursor(cursor_factory=RealDictCursor)
    yield cursor
    cursor.close()


class TestPostgreSQLConnection:
    """Test PostgreSQL database connectivity"""

    def test_connection_successful(self, pg_connection):
        """Test dat we kunnen connecten met PostgreSQL"""
        assert pg_connection is not None
        assert pg_connection.closed == 0

    def test_database_exists(self, pg_cursor):
        """Test dat activity database bestaat"""
        pg_cursor.execute("SELECT current_database();")
        result = pg_cursor.fetchone()
        assert result["current_database"] == "activity"

    def test_event_outbox_table_exists(self, pg_cursor):
        """Test dat event_outbox tabel bestaat"""
        pg_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'event_outbox'
            );
        """)
        result = pg_cursor.fetchone()
        assert result["exists"] is True


class TestEventOutboxTable:
    """Test event_outbox table structure en data"""

    def test_table_columns(self, pg_cursor):
        """Test dat alle kolommen bestaan"""
        pg_cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'event_outbox'
            ORDER BY ordinal_position;
        """)
        columns = pg_cursor.fetchall()

        column_names = [col["column_name"] for col in columns]

        expected_columns = [
            "event_id",
            "sequence_id",
            "aggregate_id",
            "aggregate_type",
            "event_type",
            "payload",
            "status",
            "retry_count",
            "last_error",
            "lock_id",
            "created_at",
            "published_at",
        ]

        for col in expected_columns:
            assert col in column_names, f"Column {col} not found"

    def test_table_indexes(self, pg_cursor):
        """Test dat alle indices bestaan"""
        pg_cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'event_outbox';
        """)
        indexes = pg_cursor.fetchall()
        index_names = [idx["indexname"] for idx in indexes]

        expected_indexes = [
            "event_outbox_pkey",
            "idx_event_outbox_status",
            "idx_event_outbox_created_at",
            "idx_event_outbox_aggregate",
            "idx_event_outbox_event_type",
            "idx_event_outbox_sequence",
        ]

        for idx in expected_indexes:
            assert idx in index_names, f"Index {idx} not found"

    def test_read_test_data(self, pg_cursor):
        """Test dat we test data kunnen lezen"""
        pg_cursor.execute("""
            SELECT
                event_id,
                aggregate_type,
                event_type,
                status,
                payload
            FROM event_outbox
            WHERE status = 'pending'
            ORDER BY sequence_id;
        """)
        events = pg_cursor.fetchall()

        # Verify we have test data
        assert len(events) > 0, "No test data found"

        # Verify data structure
        for event in events:
            assert "event_id" in event
            assert "aggregate_type" in event
            assert "event_type" in event
            assert "status" in event
            assert "payload" in event
            assert event["status"] == "pending"

    def test_read_user_events(self, pg_cursor):
        """Test dat we User events kunnen lezen"""
        pg_cursor.execute("""
            SELECT * FROM event_outbox
            WHERE aggregate_type = 'User'
            AND status = 'pending'
            ORDER BY sequence_id;
        """)
        events = pg_cursor.fetchall()

        assert len(events) >= 1, "No User events found"

        # Check event types
        event_types = [e["event_type"] for e in events]
        assert any("User" in et for et in event_types)

    def test_read_activity_events(self, pg_cursor):
        """Test dat we Activity events kunnen lezen"""
        pg_cursor.execute("""
            SELECT * FROM event_outbox
            WHERE aggregate_type = 'Activity'
            AND status = 'pending'
            ORDER BY sequence_id;
        """)
        events = pg_cursor.fetchall()

        assert len(events) >= 1, "No Activity events found"

        # Check event types
        event_types = [e["event_type"] for e in events]
        assert any("Activity" in et for et in event_types)


class TestEventInsertion:
    """Test inserten van nieuwe events"""

    def test_insert_new_event(self, pg_connection, pg_cursor):
        """Test dat we nieuwe events kunnen inserten"""
        event_id = uuid4()
        aggregate_id = uuid4()

        pg_cursor.execute("""
            INSERT INTO event_outbox (
                event_id,
                aggregate_id,
                aggregate_type,
                event_type,
                payload,
                status,
                created_at
            ) VALUES (
                %s, %s, %s, %s, %s::jsonb, %s, %s
            ) RETURNING event_id, sequence_id;
        """, (
            str(event_id),  # Convert UUID to string
            str(aggregate_id),  # Convert UUID to string
            "User",
            "UserCreated",
            '{"email": "integration@test.com"}',
            "pending",
            datetime.utcnow(),
        ))

        result = pg_cursor.fetchone()
        pg_connection.commit()

        assert str(result["event_id"]) == str(event_id)
        assert result["sequence_id"] is not None

    def test_sequence_id_auto_increments(self, pg_connection, pg_cursor):
        """Test dat sequence_id automatisch increment"""
        # Get current max sequence_id
        pg_cursor.execute("SELECT MAX(sequence_id) as max_seq FROM event_outbox;")
        max_seq_before = pg_cursor.fetchone()["max_seq"]

        # Insert new event
        pg_cursor.execute("""
            INSERT INTO event_outbox (
                event_id,
                aggregate_id,
                aggregate_type,
                event_type,
                payload,
                status
            ) VALUES (
                %s, %s, %s, %s, %s::jsonb, %s
            ) RETURNING sequence_id;
        """, (
            str(uuid4()),  # Convert UUID to string
            str(uuid4()),  # Convert UUID to string
            "User",
            "UserCreated",
            '{"test": true}',
            "pending",
        ))

        result = pg_cursor.fetchone()
        pg_connection.commit()

        # Verify sequence_id increased
        assert result["sequence_id"] > max_seq_before


class TestStatusConstraint:
    """Test status constraint validation"""

    def test_valid_status_values(self, pg_connection, pg_cursor):
        """Test dat valid status waarden accepteerd worden"""
        valid_statuses = ["pending", "processing", "processed", "failed", "retry"]

        for status in valid_statuses:
            event_id = str(uuid4())  # Convert UUID to string
            pg_cursor.execute("""
                INSERT INTO event_outbox (
                    event_id,
                    aggregate_id,
                    aggregate_type,
                    event_type,
                    payload,
                    status
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s);
            """, (
                event_id,
                str(uuid4()),  # Convert UUID to string
                "User",
                "UserCreated",
                '{"test": true}',
                status,
            ))
            pg_connection.commit()

            # Verify inserted
            pg_cursor.execute("SELECT status FROM event_outbox WHERE event_id = %s;", (event_id,))
            result = pg_cursor.fetchone()
            assert result["status"] == status

    def test_invalid_status_rejected(self, pg_connection, pg_cursor):
        """Test dat invalid status waarden gerejected worden"""
        with pytest.raises(psycopg2.errors.CheckViolation):
            pg_cursor.execute("""
                INSERT INTO event_outbox (
                    event_id,
                    aggregate_id,
                    aggregate_type,
                    event_type,
                    payload,
                    status
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s);
            """, (
                str(uuid4()),  # Convert UUID to string
                str(uuid4()),  # Convert UUID to string
                "User",
                "UserCreated",
                '{"test": true}',
                "invalid_status",
            ))
            pg_connection.commit()

        pg_connection.rollback()
