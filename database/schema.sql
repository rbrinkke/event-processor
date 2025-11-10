-- Event Outbox Table Schema
-- Voor Debezium CDC pattern met PostgreSQL WAL

-- Create activity schema
CREATE SCHEMA IF NOT EXISTS activity;

-- Create event_status ENUM type
DO $$ BEGIN
    CREATE TYPE activity.event_status AS ENUM ('pending', 'processing', 'processed', 'failed', 'retry');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create event_outbox table
CREATE TABLE IF NOT EXISTS activity.event_outbox (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sequence_id BIGSERIAL UNIQUE NOT NULL,
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status activity.event_status NOT NULL DEFAULT 'pending',
    retry_count INT NOT NULL DEFAULT 0,
    last_error TEXT,
    lock_id UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE
);

-- Index voor query performance
CREATE INDEX IF NOT EXISTS idx_event_outbox_processing ON activity.event_outbox (status, lock_id, sequence_id)
    WHERE status IN ('pending', 'failed');
CREATE INDEX IF NOT EXISTS idx_event_outbox_created_at ON activity.event_outbox(created_at);
CREATE INDEX IF NOT EXISTS idx_event_outbox_aggregate ON activity.event_outbox(aggregate_id, aggregate_type);
CREATE INDEX IF NOT EXISTS idx_event_outbox_event_type ON activity.event_outbox(event_type);
CREATE INDEX IF NOT EXISTS idx_event_outbox_sequence ON activity.event_outbox(sequence_id);

-- Create Debezium publication for CDC
CREATE PUBLICATION debezium_publication FOR TABLE activity.event_outbox;

-- Comments voor documentatie
COMMENT ON TABLE activity.event_outbox IS 'Outbox pattern table voor reliable event publishing via Debezium CDC';
COMMENT ON COLUMN activity.event_outbox.event_id IS 'Unique event identifier (UUID v4)';
COMMENT ON COLUMN activity.event_outbox.sequence_id IS 'Auto-incrementing sequence for ordering';
COMMENT ON COLUMN activity.event_outbox.aggregate_id IS 'ID van de aggregate (User, Activity, etc)';
COMMENT ON COLUMN activity.event_outbox.aggregate_type IS 'Type van de aggregate (User, Activity, Participant)';
COMMENT ON COLUMN activity.event_outbox.event_type IS 'Type van het event (UserCreated, ActivityUpdated, etc)';
COMMENT ON COLUMN activity.event_outbox.payload IS 'Event payload in JSON format';
COMMENT ON COLUMN activity.event_outbox.status IS 'Processing status: pending, processing, processed, failed, retry';
COMMENT ON COLUMN activity.event_outbox.retry_count IS 'Number of retry attempts';
COMMENT ON COLUMN activity.event_outbox.last_error IS 'Last error message if failed';
COMMENT ON COLUMN activity.event_outbox.lock_id IS 'Lock identifier for distributed processing';
COMMENT ON COLUMN activity.event_outbox.created_at IS 'Timestamp when event was created';
COMMENT ON COLUMN activity.event_outbox.published_at IS 'Timestamp when event was successfully published to Kafka';
