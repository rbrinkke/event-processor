# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Event Processor** - High-performance CDC-based event processing system using Debezium, Kafka, and Python. Built for the Activity App, this system streams changes from PostgreSQL's event_outbox table through Kafka to MongoDB read models.

**Architecture Pattern:** PostgreSQL WAL → Debezium → Kafka → Python Consumer → Handler Registry → MongoDB

**Status:** ✅ Proof of Concept Successful (100% test passing, verified end-to-end)

## Common Commands

### Development

```bash
# Start all services (Zookeeper, Kafka, Debezium, Event Processor, Kafka UI)
docker-compose up -d

# Rebuild event-processor after code changes
docker-compose build event-processor
docker-compose restart event-processor

# View logs
docker-compose logs -f event-processor
docker-compose logs -f debezium
docker-compose logs -f kafka

# Deploy Debezium connector (after services are up)
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @debezium/postgres-connector.json

# Check connector status
curl http://localhost:8083/connectors/postgres-event-outbox-connector/status
```

### Testing

```bash
# Run all tests (use Docker exec or local environment)
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_handlers.py

# Run specific test
pytest tests/test_handlers.py::TestUserCreatedHandler::test_handle_user_created

# Run integration tests (requires PostgreSQL/MongoDB)
pytest tests/test_postgres_integration.py
pytest tests/test_e2e_flows.py
```

### Demo & Load Testing

```bash
# Complete demo sequence (generates events, processes, verifies)
./scripts/demo/full_demo.sh

# Run specific load tests
./scripts/demo/load_10.sh      # 10 events (warm-up)
./scripts/demo/load_100.sh     # 100 events (moderate)
./scripts/demo/load_1000.sh    # 1,000 events (stress)
./scripts/demo/load_10000.sh   # 10,000 events (extreme)

# Verify MongoDB data integrity
./scripts/demo/verify_mongodb.sh

# Setup/verify environment before demo
./scripts/demo/setup.sh
```

### Kafka Operations

```bash
# List Kafka topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Consume messages from topic (debugging)
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic postgres.activity.event_outbox \
  --from-beginning

# Check consumer group status
docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group event-processor-group \
  --describe

# Access Kafka UI
open http://localhost:8080
```

### PostgreSQL Operations

```bash
# Check PostgreSQL replication status
docker exec -it auth-postgres psql -U activity_user -d activity_db -c "SELECT * FROM pg_replication_slots;"

# Check publication status
docker exec -it auth-postgres psql -U activity_user -d activity_db -c "SELECT * FROM pg_publication;"

# Insert test event
docker exec -it auth-postgres psql -U activity_user -d activity_db -c "
INSERT INTO activity.event_outbox (
    event_id, aggregate_id, aggregate_type, event_type, payload, status
) VALUES (
    gen_random_uuid(), gen_random_uuid(), 'User', 'UserCreated',
    '{\"email\": \"test@example.com\", \"username\": \"testuser\"}'::jsonb,
    'pending'
);"
```

### Code Quality

```bash
# Format code
black app/ tests/
black scripts/demo/lib/

# Lint
ruff app/ tests/

# Type checking
mypy app/
```

## Architecture Overview

### Core Components

```
app/
├── main.py              # Application entry point, orchestration, signal handling
├── consumer.py          # Kafka consumer with batch processing and stats tracking
├── registry.py          # Handler registry - CENTRAL PLACE TO REGISTER NEW HANDLERS
├── config.py            # Environment configuration via pydantic-settings
├── models.py            # Pydantic models: OutboxEvent, DebeziumPayload, EventMetrics
├── handlers/            # Event handlers (business logic)
│   ├── base.py          # BaseEventHandler abstract class
│   ├── user_handlers.py # UserCreated, UserUpdated, UserStatistics handlers
│   └── activity_handlers.py # ActivityCreated, ActivityUpdated, ParticipantJoined
└── database/
    └── mongodb.py       # MongoDB async client with connection pooling
```

### Key Design Patterns

**1. Handler Registry Pattern**
- Multiple handlers can listen to the same event type
- Example: `UserCreated` → [UserCreatedHandler, UserStatisticsHandler]
- Add new handlers in `registry.py::_initialize_handlers()`
- Handlers execute independently; if one fails, others continue

**2. Debezium CDC Integration**
- Debezium captures PostgreSQL WAL changes from `event_outbox` table
- Messages flow through Kafka topic: `postgres.activity.event_outbox`
- Consumer deserializes Debezium envelope format to `OutboxEvent`
- Operations: 'c' (create), 'u' (update), 'd' (delete), 'r' (read/snapshot)
- Consumer skips deletes and snapshots, processes creates/updates only

**3. Async Processing**
- Entire stack is async: aiokafka, motor (MongoDB), asyncio
- Batch processing with configurable `KAFKA_MAX_POLL_RECORDS`
- Manual offset commits for at-least-once delivery guarantee
- Graceful shutdown with signal handlers (SIGINT/SIGTERM)

**4. Error Isolation**
- Handler failures don't stop message processing
- Each handler wrapped in try/catch
- Errors logged with structured logging (structlog)
- Consumer tracks statistics: `_processing_count`, `_error_count`

## Event Flow

### End-to-End Processing

1. **PostgreSQL Trigger**: INSERT into `event_outbox` table
2. **Debezium CDC**: Captures WAL change, creates Kafka message
3. **Kafka Topic**: Message published to `postgres.activity.event_outbox`
4. **Consumer Poll**: `EventConsumer.consume()` fetches batch of messages
5. **Deserialization**: JSON → `DebeziumPayload` → `OutboxEvent`
6. **Handler Routing**: `handler_registry.get_handlers(event_type)`
7. **Handler Execution**: Each handler processes event independently
8. **MongoDB Write**: Handlers persist to MongoDB collections
9. **Offset Commit**: Consumer commits Kafka offset after successful processing

### Latency Targets

- **End-to-end**: <100ms (PostgreSQL commit → MongoDB write)
- **CDC latency**: <30ms (WAL capture)
- **Kafka latency**: <20ms (message delivery)
- **Processing time**: <50ms (handler execution)

## Adding a New Event Handler

**Example: Add `UserDeletedHandler`**

1. **Create handler class** in `app/handlers/user_handlers.py`:
```python
class UserDeletedHandler(BaseEventHandler):
    @property
    def event_type(self) -> str:
        return "UserDeleted"

    async def handle(self, event: OutboxEvent) -> None:
        user_id = event.payload.get("user_id")

        # Your business logic
        await mongodb.db.users.delete_one({"user_id": user_id})

        self.log_event(event, "user_deleted", user_id=user_id)
```

2. **Register handler** in `app/registry.py::_initialize_handlers()`:
```python
self.register(UserDeletedHandler())
```

3. **Restart service**:
```bash
docker-compose restart event-processor
```

4. **Verify registration** in logs:
```bash
docker-compose logs event-processor | grep "UserDeleted"
```

## Configuration

### Environment Variables (.env)

Critical settings for local development:

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:29092        # Internal Docker network
KAFKA_TOPIC=postgres.activity.event_outbox
KAFKA_GROUP_ID=event-processor-group
KAFKA_AUTO_OFFSET_RESET=earliest           # Start from beginning on new consumer
KAFKA_MAX_POLL_RECORDS=100                 # Batch size

# MongoDB
MONGODB_URI=mongodb://localhost:27025      # MongoDB Atlas or local
MONGODB_DATABASE=activity_read

# PostgreSQL (for future status updates)
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5432
POSTGRES_DB=activity_db
POSTGRES_USER=activity_user
POSTGRES_PASSWORD=your_password

# Application
LOG_LEVEL=INFO
PROCESSING_BATCH_SIZE=100
MAX_RETRIES=3
```

### Docker Network Configuration

**Important:** The project uses an **external Docker network** called `activity-network`:

```bash
# Create network if it doesn't exist
docker network create activity-network

# Verify network exists
docker network ls | grep activity-network
```

All services (Kafka, Debezium, event-processor) must be on this network to communicate.

## Testing Strategy

### Test Organization

```
tests/
├── test_config.py           # Configuration loading
├── test_models.py           # Pydantic model validation
├── test_registry.py         # Handler registration
├── test_handlers.py         # Individual handler logic (mocked MongoDB)
├── test_consumer.py         # Consumer message processing (mocked Kafka)
├── test_postgres_integration.py  # Real PostgreSQL insertion
└── test_e2e_flows.py       # Complete end-to-end flows
```

### Test Coverage

- **62/62 tests passing** (100% success rate)
- Unit tests use mocks for external dependencies
- Integration tests require real PostgreSQL/MongoDB
- E2E tests verify complete flow from event generation to MongoDB

## Troubleshooting

### Consumer Not Receiving Events

**Check Debezium connector:**
```bash
curl http://localhost:8083/connectors/postgres-event-outbox-connector/status
```

**Verify Kafka topic exists:**
```bash
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092 | grep event_outbox
```

**Check PostgreSQL replication:**
```bash
# Must show: wal_level = 'logical'
docker exec auth-postgres psql -U activity_user -d activity_db -c "SHOW wal_level;"

# Must show publication for event_outbox
docker exec auth-postgres psql -U activity_user -d activity_db -c "SELECT * FROM pg_publication;"
```

### Handler Failures

**Check handler error logs:**
```bash
docker-compose logs event-processor | grep "handler_failed"
```

**Common issues:**
- MongoDB connection timeout: Check `MONGODB_URI` is accessible from container
- Invalid payload format: Verify event payload matches expected schema
- Missing required fields: Check Pydantic validation in handler

### High Latency

**Verify service health:**
- Kafka health: `docker-compose ps kafka` (should show "healthy")
- Debezium health: `curl http://localhost:8083/` (should return 200)
- Consumer lag: Check `docker-compose logs event-processor` for processing times

**Performance tuning:**
- Increase `KAFKA_MAX_POLL_RECORDS` for higher throughput
- Scale consumers: `docker-compose up --scale event-processor=3`
- Check MongoDB indexes for read models
- Monitor network latency between services

### Container Startup Issues

**Network not found:**
```bash
docker network create activity-network
```

**Kafka not ready:**
Wait for Kafka healthcheck to pass before deploying Debezium connector. Check:
```bash
docker-compose ps kafka
```

**Debezium connector deployment fails:**
Ensure PostgreSQL has:
- `wal_level = 'logical'` (requires PostgreSQL restart)
- Publication created: `CREATE PUBLICATION debezium_publication FOR TABLE activity.event_outbox;`
- Debezium can reach PostgreSQL (update `database.hostname` in connector config)

## Demo System

The project includes a comprehensive demo and load testing system for proof-of-concept validation.

### Demo Components

**Event Generation** (`scripts/demo/lib/event_generator.py`):
- Uses Faker library for realistic test data
- Generates Users, Activities, Participants with referential integrity
- Configurable event distribution (40% Users, 30% Activities, 30% Participants)

**Load Testing** (`scripts/demo/*.sh`):
- Warm-up: 10 events
- Moderate: 100 events
- Stress: 1,000 events
- Extreme: 10,000 events

**Verification** (`scripts/demo/lib/mongodb_verifier.py`):
- Document count validation
- Data integrity checks
- Referential integrity verification
- Field completeness analysis

### Metrics Tracked

- **Throughput**: Events/second (current, average, peak)
- **Latency**: Min, Max, Avg, P50, P95, P99 (milliseconds)
- **Success Rate**: Percentage of successfully processed events
- **Event Distribution**: Count and percentage per event type

## Important Implementation Details

### Why Handler Registry Pattern?

- **Flexibility**: Multiple handlers per event type enables CQRS read model projections
- **Decoupling**: Add/remove handlers without changing consumer or Kafka setup
- **Resilience**: Handler failures isolated; don't cascade to other handlers
- **Scalability**: Easy to add specialized handlers (statistics, notifications, etc.)

### Why Debezium CDC?

- **Change Data Capture**: Zero application impact; captures WAL changes
- **Exactly-once in PostgreSQL**: Outbox pattern ensures transactional consistency
- **At-least-once delivery**: Combined with idempotent handlers = reliable processing
- **No polling**: Event-driven; no database query overhead

### Why MongoDB for Read Models?

- **Document model**: Natural fit for denormalized read models
- **Flexible schema**: Easy to evolve read models without migrations
- **High read throughput**: Optimized for query workloads
- **Horizontal scaling**: Sharding for large-scale deployments

## Performance Characteristics

**Proven Metrics (POC Testing):**
- Processing: 9 events < 1 second
- Error rate: 0% (all events successful)
- Data integrity: 100% (verified in MongoDB)
- Test coverage: 100% (62/62 tests passing)

**Production Targets:**
- Throughput: >1000 events/second per consumer
- Latency: <100ms end-to-end
- Success rate: >99.9%
- Horizontal scaling: 3-5 consumers via Kafka partitioning

## Documentation Files

- `README.md`: Quick start, deployment instructions, troubleshooting
- `PROOF_OF_CONCEPT_SUCCESS.md`: POC validation and demo instructions
- `DEMO_QUICKSTART.md`: Demo system usage guide
- `DEMO_STRATEGY.md`: Detailed demo architecture and strategy
- `docs/DEMO_ARCHITECTURE.md`: Visual architecture diagrams
- `scripts/demo/README.md`: Demo script usage guide

## Key Dependencies

- **aiokafka 0.10.0**: Async Kafka client for high-performance consumption
- **motor 3.3.2**: Async MongoDB driver (built on pymongo)
- **pydantic 2.5.0**: Data validation and settings management
- **structlog 23.2.0**: Structured logging with JSON output
- **asyncpg 0.29.0**: Async PostgreSQL driver (optional status updates)
- **pytest-asyncio**: Testing async code

## Production Checklist

Before deploying to production:

- [ ] PostgreSQL `wal_level = 'logical'` configured
- [ ] Debezium publication created for `event_outbox` table
- [ ] Kafka cluster configured with appropriate replication factor
- [ ] MongoDB indexes created for read model queries
- [ ] `activity-network` Docker network created
- [ ] Environment variables configured in `.env`
- [ ] Debezium connector deployed and verified
- [ ] Load testing completed successfully
- [ ] Monitoring/alerting configured (structured logs to observability platform)
- [ ] Consumer group ID unique per environment
- [ ] Backup strategy for Kafka offsets
