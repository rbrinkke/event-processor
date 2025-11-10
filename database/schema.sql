-- Event Outbox Table Schema
-- Voor Debezium CDC pattern met PostgreSQL WAL

-- Create event_outbox table
CREATE TABLE IF NOT EXISTS event_outbox (
    event_id UUID PRIMARY KEY,
    sequence_id BIGSERIAL NOT NULL,
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    lock_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,

    -- Indexes voor performance
    CONSTRAINT status_check CHECK (status IN ('pending', 'processing', 'processed', 'failed', 'retry'))
);

-- Index voor query performance
CREATE INDEX IF NOT EXISTS idx_event_outbox_status ON event_outbox(status);
CREATE INDEX IF NOT EXISTS idx_event_outbox_created_at ON event_outbox(created_at);
CREATE INDEX IF NOT EXISTS idx_event_outbox_aggregate ON event_outbox(aggregate_id, aggregate_type);
CREATE INDEX IF NOT EXISTS idx_event_outbox_event_type ON event_outbox(event_type);
CREATE INDEX IF NOT EXISTS idx_event_outbox_sequence ON event_outbox(sequence_id);

-- Comments voor documentatie
COMMENT ON TABLE event_outbox IS 'Outbox pattern table voor reliable event publishing via Debezium CDC';
COMMENT ON COLUMN event_outbox.event_id IS 'Unique event identifier (UUID v4)';
COMMENT ON COLUMN event_outbox.sequence_id IS 'Auto-incrementing sequence for ordering';
COMMENT ON COLUMN event_outbox.aggregate_id IS 'ID van de aggregate (User, Activity, etc)';
COMMENT ON COLUMN event_outbox.aggregate_type IS 'Type van de aggregate (User, Activity, Participant)';
COMMENT ON COLUMN event_outbox.event_type IS 'Type van het event (UserCreated, ActivityUpdated, etc)';
COMMENT ON COLUMN event_outbox.payload IS 'Event payload in JSON format';
COMMENT ON COLUMN event_outbox.status IS 'Processing status: pending, processing, processed, failed, retry';
COMMENT ON COLUMN event_outbox.retry_count IS 'Number of retry attempts';
COMMENT ON COLUMN event_outbox.last_error IS 'Last error message if failed';
COMMENT ON COLUMN event_outbox.lock_id IS 'Lock identifier for distributed processing';
COMMENT ON COLUMN event_outbox.created_at IS 'Timestamp when event was created';
COMMENT ON COLUMN event_outbox.published_at IS 'Timestamp when event was successfully published to Kafka';
