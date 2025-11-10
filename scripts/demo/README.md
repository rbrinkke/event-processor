# Event Processor Demo Scripts

Complete demo and load testing system for the event-processor proof of concept.

## Quick Start

```bash
# Run complete automated demo
./scripts/demo/full_demo.sh

# Or run individual tests
./scripts/demo/setup.sh         # Setup and verify environment
./scripts/demo/load_100.sh      # Run 100 event test
./scripts/demo/verify.sh         # Verify results
```

## Scripts Overview

### Setup & Configuration

**`setup.sh`** - Environment Setup
- Verifies PostgreSQL, Kafka, MongoDB connectivity
- Checks event_outbox table exists
- Installs Python dependencies
- Optional: Cleans previous demo data

```bash
./scripts/demo/setup.sh
```

### Load Tests

**`load_10.sh`** - Warm-up Test (10 events)
- Purpose: Verify pipeline functionality
- Duration: ~5 seconds
- Use case: Quick smoke test

**`load_100.sh`** - Moderate Load (100 events)
- Purpose: Typical operation simulation
- Duration: ~15 seconds
- Use case: Standard performance baseline

**`load_1000.sh`** - Stress Test (1,000 events)
- Purpose: System under load
- Duration: ~30 seconds
- Use case: Performance testing

**`load_10000.sh`** - Extreme Load (10,000 events)
- Purpose: Find system limits
- Duration: ~60 seconds
- Use case: Capacity planning

```bash
./scripts/demo/load_100.sh
```

### Verification

**`verify.sh`** - Data Integrity Verification
- Checks document counts
- Verifies field completeness
- Tests referential integrity
- Detects duplicates
- Exports results to JSON

```bash
./scripts/demo/verify.sh
```

### Complete Demo

**`full_demo.sh`** - Automated Full Demo Sequence
- Runs all tests in sequence
- Includes setup and verification
- Total time: ~2.5 minutes
- Total events: 11,110

```bash
./scripts/demo/full_demo.sh
```

## Python Modules (lib/)

### `event_generator.py`
Generates realistic test data using Faker library.

**Features:**
- Realistic user data (names, emails, addresses)
- Realistic activity data (titles, locations)
- Referential integrity
- Configurable event distribution

**Usage:**
```python
from event_generator import EventGenerator

generator = EventGenerator()
events = generator.generate_batch(
    count=100,
    distribution={
        "UserCreated": 0.4,
        "ActivityCreated": 0.3,
        "ParticipantJoined": 0.3
    }
)
```

### `postgres_inserter.py`
Inserts events into PostgreSQL event_outbox table.

**Features:**
- Batch inserts for performance
- Timestamp tracking (T0)
- Error handling
- Statistics reporting

**Usage:**
```python
from postgres_inserter import PostgresInserter

inserter = PostgresInserter()
inserter.connect()
stats = inserter.insert_events_batch(events, batch_size=100)
inserter.disconnect()
```

### `metrics_collector.py`
Collects and aggregates performance metrics.

**Features:**
- Real-time throughput tracking
- Latency statistics (min/max/avg/p50/p95/p99)
- Event type breakdown
- Error rate monitoring
- JSON export

**Usage:**
```python
from metrics_collector import MetricsCollector

collector = MetricsCollector("metrics.json")
collector.record_event({
    "event_id": "...",
    "event_type": "UserCreated",
    "total_latency": 28.5,
    "success": True
})
collector.print_summary()
collector.export_to_json()
```

### `dashboard.py`
Real-time terminal dashboard using Rich library.

**Features:**
- Live updating display
- Throughput metrics
- Latency sparklines
- Event breakdown
- Recent events log
- Progress tracking

**Usage:**
```python
from dashboard import Dashboard

dashboard = Dashboard(target_events=1000)
dashboard.update("UserCreated", latency_ms=25.3, success=True)
dashboard.render_once()
```

### `mongodb_verifier.py`
Verifies data integrity in MongoDB.

**Features:**
- Document count verification
- Field completeness checks
- Referential integrity validation
- Duplicate detection
- Comprehensive reporting

**Usage:**
```python
from mongodb_verifier import MongoDBVerifier

verifier = MongoDBVerifier()
results = verifier.run_full_verification(
    expected_users=100,
    expected_activities=50
)
verifier.print_verification_report(results)
```

## Environment Variables

Required environment variables:

```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=activity
POSTGRES_USER=postgres
POSTGRES_PASSWORD=

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=postgres.activity.event_outbox
KAFKA_GROUP_ID=event-processor-group

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=activity_read

# Optional
METRICS_FILE=demo_metrics.json
LOG_LEVEL=INFO
```

## Success Metrics

Target performance benchmarks:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Throughput | >100 events/sec | Average sustained rate |
| P50 Latency | <30ms | Median end-to-end latency |
| P95 Latency | <100ms | 95th percentile latency |
| P99 Latency | <200ms | 99th percentile latency |
| Success Rate | >99.9% | (processed - errors) / processed |
| Data Integrity | 100% | All verification checks pass |

## Troubleshooting

### PostgreSQL Connection Failed
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Verify credentials
psql -h localhost -U postgres -d activity
```

### Kafka Not Accessible
```bash
# Check Kafka is running
nc -zv localhost 9092

# List topics
/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

### MongoDB Connection Issues
```bash
# Check MongoDB is running
mongosh --eval "db.runCommand({ping: 1})"

# Or with pymongo
python3 -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017'); client.admin.command('ping')"
```

### event_outbox Table Missing
```bash
# Create table using schema
psql -h localhost -U postgres -d activity < database/schema.sql
```

### Python Dependencies Missing
```bash
# Install required packages
pip install --break-system-packages rich faker psycopg2-binary pymongo numpy
```

## Demo Tips

### For Best Results
1. Start with `./scripts/demo/setup.sh` to verify environment
2. Run warm-up test first (`load_10.sh`)
3. Always wait for processing to complete before verification
4. Monitor event processor logs during demo
5. Open MongoDB Compass to see data appearing live

### For Live Presentations
- Run `full_demo.sh` for automated sequence
- Keep terminal window visible for live metrics
- Have MongoDB Compass open showing collections
- Explain each stage as it runs
- Highlight the exact latency measurements

### Wait Times After Load Tests
- 10 events: Wait 10 seconds
- 100 events: Wait 15 seconds
- 1,000 events: Wait 30 seconds
- 10,000 events: Wait 60 seconds

## Files Generated

After running demos:

- `demo_verification.json` - Verification results
- `demo_metrics.json` - Performance metrics (if exported)
- Event processor logs - Check Docker logs or console output

## Next Steps

After successful demo:

1. Review verification results
2. Analyze performance metrics
3. Export reports for stakeholders
4. Document any findings
5. Plan production deployment

## Support

For issues or questions:
- Check troubleshooting section above
- Review main project documentation
- Verify environment variables are set
- Ensure all services are running

---

**Created by:** Claude Code
**Last Updated:** 2025-11-10
**Status:** Production Ready
