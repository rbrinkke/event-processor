# Event Processor - CDC Architecture

High-performance event processing system using Debezium CDC, Kafka, and Python.

## Architecture

```
PostgreSQL WAL → Debezium → Kafka → Python Consumer → Handler Registry → MongoDB
                                                        ↓
                                            [UserCreatedHandler]
                                            [ActivityCreatedHandler]
                                            [ParticipantJoinedHandler]
                                            [... custom handlers]
```

## Performance

- **Latency**: <100ms end-to-end (PostgreSQL commit → MongoDB write)
- **Throughput**: 1000+ events/second per consumer
- **Scalability**: Horizontaal schaalbaar (multiple consumers)

## Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- PostgreSQL met event_outbox tabel
- MongoDB instance

### 2. Configuration

Create `.env` file:
```bash
cp .env .env.local
# Edit .env met jouw database credentials
```

### 3. Start Services

```bash
# Start alle services
docker-compose up -d

# Check logs
docker-compose logs -f event-processor
```

### 4. Configure Debezium Connector

```bash
# Wait for Debezium to be ready
docker-compose logs -f debezium

# Deploy PostgreSQL connector
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @debezium/postgres-connector.json
```

### 5. Verify

```bash
# Check Kafka topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Check Kafka UI (optional)
open http://localhost:8080
```

## Development

### Add New Event Handler

1. Create handler in `app/handlers/`:
```python
from app.handlers.base import BaseEventHandler
from app.models import OutboxEvent

class MyEventHandler(BaseEventHandler):
    @property
    def event_type(self) -> str:
        return "MyEventType"

    async def handle(self, event: OutboxEvent) -> None:
        # Your processing logic
        pass
```

2. Register in `app/registry.py`:
```python
from app.handlers.my_handler import MyEventHandler

def _initialize_handlers(self):
    # ... existing handlers
    self.register(MyEventHandler())
```

3. Restart service:
```bash
docker-compose restart event-processor
```

## Monitoring

### View Logs

```bash
# Application logs
docker-compose logs -f event-processor

# Kafka logs
docker-compose logs -f kafka

# Debezium logs
docker-compose logs -f debezium
```

### Check Consumer Stats

Logs include structured metrics:
- `total_processed`: Total events processed
- `total_errors`: Total processing errors
- `processing_time_ms`: Per-event processing time

## Testing

```bash
# Run tests
docker-compose exec event-processor pytest

# With coverage
docker-compose exec event-processor pytest --cov=app
```

## Troubleshooting

### Consumer not receiving events?

1. Check Debezium connector status:
```bash
curl http://localhost:8083/connectors/postgres-event-outbox-connector/status
```

2. Check Kafka topic:
```bash
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic postgres.activity.event_outbox \
  --from-beginning
```

3. Check PostgreSQL replication:
```sql
SELECT * FROM pg_replication_slots;
SELECT * FROM pg_publication;
```

### High latency?

- Check network between services
- Verify Kafka partition count
- Scale consumers horizontally
- Optimize handler performance

## Documentation

- [Debezium PostgreSQL Connector](https://debezium.io/documentation/reference/stable/connectors/postgresql.html)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Motor (MongoDB async)](https://motor.readthedocs.io/)

## Contributing

1. Create new handler
2. Add tests
3. Update registry
4. Submit PR

## License

MIT

---

## DEPLOYMENT INSTRUCTIES

### Stap 1: PostgreSQL Setup (WAL Configuration)

Voer deze SQL uit op je PostgreSQL database:

```sql
-- Enable logical replication
ALTER SYSTEM SET wal_level = 'logical';

-- Restart PostgreSQL (vereist)
-- sudo systemctl restart postgresql

-- Create publication voor Debezium
CREATE PUBLICATION debezium_publication FOR TABLE activity.event_outbox;

-- Verify
SELECT * FROM pg_publication;
```

### Stap 2: Build & Deploy

```bash
# Clone/copy project
cd event-processor

# Configure environment
nano .env  # Fill in your credentials

# Start services
docker-compose up -d

# Watch logs
docker-compose logs -f
```

### Stap 3: Deploy Debezium Connector

```bash
# Wait for Debezium to be ready (check logs)
docker-compose logs debezium | grep "Kafka Connect started"

# Update postgres-connector.json met jouw credentials
nano debezium/postgres-connector.json

# Deploy connector
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @debezium/postgres-connector.json

# Verify connector
curl http://localhost:8083/connectors/postgres-event-outbox-connector/status
```

### Stap 4: Test Event Flow

```sql
-- Insert test event in PostgreSQL
INSERT INTO activity.event_outbox (
    event_id,
    aggregate_id,
    aggregate_type,
    event_type,
    payload,
    status
) VALUES (
    gen_random_uuid(),
    gen_random_uuid(),
    'User',
    'UserCreated',
    '{"email": "test@example.com", "username": "testuser", "first_name": "Test", "last_name": "User"}'::jsonb,
    'pending'
);

-- Check event processor logs
-- docker-compose logs -f event-processor

-- Verify in MongoDB
-- db.users.findOne({email: "test@example.com"})
```

## Key Design Patterns

1. **Handler Registry Pattern**
   Meerdere handlers kunnen luisteren naar hetzelfde event type:
   - UserCreated → UserCreatedHandler + UserStatisticsHandler

2. **Flexible Event Processing**
   Nieuwe handlers toevoegen = 2 stappen:
   - Create handler class
   - Register in registry

3. **Error Isolation**
   Als één handler faalt, gaan andere handlers gewoon door.

4. **Horizontal Scalability**
   Run meerdere consumers:
   ```bash
   docker-compose up --scale event-processor=3
   ```
   Kafka's partitioning zorgt voor load balancing.

## Performance Optimizations

**Configured Defaults:**
- Batch size: 100 events per poll
- Auto-commit: Disabled (manual commit voor at-least-once)
- Heartbeat interval: 5 seconds
- MongoDB connection pool: Async motor client

**Tuning Options in .env:**
```bash
PROCESSING_BATCH_SIZE=100       # Higher = meer throughput, meer latency
KAFKA_MAX_POLL_RECORDS=100     # Kafka fetch batch size
```

## Security Considerations

- Network Isolation: Services in dedicated Docker network
- Credentials: Never hardcode, use .env
- MongoDB: Use connection string with auth
- PostgreSQL: Create dedicated replication user
- Kafka: Consider TLS in production

## Production Checklist

- [ ] PostgreSQL WAL level = 'logical'
- [ ] Debezium connector deployed & running
- [ ] MongoDB indexes created
- [ ] .env file configured
- [ ] Docker containers healthy
- [ ] Test event flow verified
- [ ] Monitoring/alerting setup
- [ ] Backup strategy voor Kafka offsets

---

Gemaakt met ❤️ voor high-performance event processing
