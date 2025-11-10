# Demo Implementation Roadmap

## Overview

Step-by-step implementation plan for the event-processor demo and load testing system.

**Total Estimated Time:** 14 hours  
**Status:** Design Complete ✅ | Implementation Ready 🔄

---

## Phase 1: Core Infrastructure (2 hours)

### Directory Structure
```bash
scripts/demo/
├── lib/
│   ├── __init__.py
│   ├── event_generator.py
│   ├── dashboard.py
│   ├── metrics_collector.py
│   ├── mongodb_verifier.py
│   └── latency_tracker.py
├── setup.sh
├── cleanup.sh
├── run_demo.sh
├── load_10.sh
├── load_100.sh
├── load_1000.sh
├── load_10000.sh
├── monitor.sh
├── verify.sh
├── full_demo.sh
└── README.md
```

### Tasks
- [ ] Create directory structure
- [ ] Add `__init__.py` to make lib a Python package
- [ ] Install dependencies: `pip install rich faker psycopg2-binary pymongo numpy`
- [ ] Create basic `setup.sh` with service verification
- [ ] Create basic `cleanup.sh` with safe data removal

### Verification
```bash
cd /mnt/d/activity/event-processor
mkdir -p scripts/demo/lib
touch scripts/demo/lib/__init__.py
pip install rich faker psycopg2-binary pymongo numpy
```

---

## Phase 2: Event Generator (2 hours)

### File: `scripts/demo/lib/event_generator.py`

### Implementation Steps
1. **Create EventGenerator class**
   - PostgreSQL connection management
   - Faker initialization

2. **Implement UserCreated generation**
   ```python
   def generate_user_created_events(self, count: int) -> List[uuid4]
   ```
   - Use Faker for realistic data
   - Return user_ids for referencing

3. **Implement ActivityCreated generation**
   ```python
   def generate_activity_created_events(self, count: int, user_ids: List[uuid4]) -> List[uuid4]
   ```
   - Reference existing user_ids
   - Return activity_ids for referencing

4. **Implement ParticipantJoined generation**
   ```python
   def generate_participant_joined_events(self, count: int, activity_ids: List, user_ids: List)
   ```
   - Reference existing activity_ids and user_ids

5. **Implement batch insert method**
   ```python
   def _insert_events_batch(self, events: List[Dict])
   ```
   - Use psycopg2 cursor
   - Batch commit for performance

6. **Implement mixed load generation**
   ```python
   def generate_mixed_load(self, total_events: int) -> Dict
   ```
   - 50/30/20 split (User/Activity/Participant)
   - Return timing metadata

### Testing
```bash
cd /mnt/d/activity/event-processor
python -c "
from scripts.demo.lib.event_generator import EventGenerator
gen = EventGenerator()
result = gen.generate_mixed_load(10)
print(result)
"
```

### Success Criteria
- [ ] Generates 10 events successfully
- [ ] PostgreSQL event_outbox contains events
- [ ] Referential integrity maintained
- [ ] Returns timing metadata

---

## Phase 3: Consumer Enhancement (2 hours)

### File: `app/consumer.py`

### Implementation Steps
1. **Add latency tracking attributes**
   ```python
   self._latency_metrics: List[Dict] = []
   self._metrics_file = os.getenv("METRICS_FILE", None)
   self._last_summary_time = time.time()
   ```

2. **Enhance process_message() method**
   - Extract T0 from event.created_at
   - Extract T1 from debezium_payload.ts_ms
   - Extract T2 from message.timestamp
   - Record T3 (processing start)
   - Record T5 (processing end)
   - Calculate latencies
   - Store metrics

3. **Add metrics file writer**
   ```python
   def _append_metric_to_file(self, metric: Dict)
   ```

4. **Add periodic summary logger**
   ```python
   def _log_summary(self)
   ```
   - Log every 10 seconds
   - Show throughput, latencies, error rate

5. **Add detailed stats property**
   ```python
   @property
   def detailed_stats(self) -> Dict[str, Any]
   ```

### File: `app/models.py`

6. **Add EventMetrics model**
   ```python
   class EventMetrics(BaseModel):
       event_id: UUID4
       event_type: str
       t0_created: float
       t1_kafka: float
       t3_start: float
       t5_end: float
       kafka_lag_ms: float
       processing_time_ms: float
       total_latency_ms: float
       timestamp: float
   ```

### Testing
```bash
# Run existing test suite - MUST still pass all 74 tests
pytest tests/ -v
```

### Success Criteria
- [ ] All 74 tests still passing
- [ ] Metrics collected without errors
- [ ] Latency calculations correct
- [ ] No performance degradation

---

## Phase 4: Metrics Collector (1.5 hours)

### File: `scripts/demo/lib/metrics_collector.py`

### Implementation Steps
1. **Create MetricsCollector class**
   - Initialize connections (MongoDB, PostgreSQL)
   - Set target_events and output_file

2. **Implement MongoDB stats query**
   ```python
   def query_mongodb_stats(self) -> Dict
   ```

3. **Implement PostgreSQL stats query**
   ```python
   def query_postgres_stats(self) -> Dict
   ```

4. **Implement Kafka consumer lag check**
   ```python
   def get_kafka_consumer_lag(self) -> int
   ```

5. **Implement summary stats aggregation**
   ```python
   def get_summary_stats(self) -> Dict
   ```

6. **Implement final report saver**
   ```python
   def save_final_report(self)
   ```

### Testing
```bash
python -c "
from scripts.demo.lib.metrics_collector import MetricsCollector
collector = MetricsCollector(target_events=10)
stats = collector.get_summary_stats()
print(stats)
"
```

### Success Criteria
- [ ] Connects to all databases successfully
- [ ] Queries return valid data
- [ ] Stats calculated correctly
- [ ] JSON report generated

---

## Phase 5: Dashboard Visualization (3 hours)

### File: `scripts/demo/lib/dashboard.py`

### Implementation Steps
1. **Create EventDashboard class**
   - Initialize with rich Console
   - Set target_events
   - Initialize data structures (deques for recent data)

2. **Implement metrics update method**
   ```python
   def update_metrics(self, metrics: Dict)
   ```

3. **Implement layout generator**
   ```python
   def generate_layout(self) -> Layout
   ```
   - Create header panel
   - Create stats panel
   - Create latency panel (with sparkline)
   - Create breakdown panel
   - Create recent events panel

4. **Implement sparkline helper**
   ```python
   def _get_spark_char(self, value: float, min_val: float, max_val: float) -> str
   ```

5. **Implement main run loop**
   ```python
   def run(self, metrics_collector)
   ```
   - Use rich.live.Live context
   - Update every 500ms
   - Stop when target reached

### Testing
```bash
python -c "
from scripts.demo.lib.dashboard import EventDashboard
from scripts.demo.lib.metrics_collector import MetricsCollector

dashboard = EventDashboard(target_events=10)
collector = MetricsCollector(target_events=10)
# Manual test: run dashboard.run(collector) and verify display
"
```

### Success Criteria
- [ ] Dashboard renders correctly
- [ ] Updates in real-time
- [ ] All panels show accurate data
- [ ] Sparkline displays correctly
- [ ] Colors and formatting look good

---

## Phase 6: Verification Tools (1 hour)

### File: `scripts/demo/lib/mongodb_verifier.py`

### Implementation Steps
1. **Create MongoDBVerifier class**
   - Connect to MongoDB

2. **Implement document counter**
   ```python
   def count_documents_by_type(self) -> Dict
   ```

3. **Implement referential integrity checker**
   ```python
   def verify_referential_integrity(self) -> Dict
   ```

4. **Implement event ID verifier**
   ```python
   def verify_event_ids(self, event_ids: List[str]) -> Dict
   ```

5. **Implement latest documents getter**
   ```python
   def get_latest_documents(self, collection_name: str, limit: int = 5) -> List[Dict]
   ```

### File: `scripts/demo/lib/latency_tracker.py`

6. **Create LatencyTracker class**

7. **Implement statistics calculator**
   ```python
   def calculate_statistics(self) -> Dict
   ```
   - Using numpy for percentiles

8. **Implement report generator**
   ```python
   def generate_report(self) -> str
   ```

9. **Implement JSON exporter**
   ```python
   def export_to_json(self, filename: str)
   ```

### Testing
```bash
python -c "
from scripts.demo.lib.mongodb_verifier import MongoDBVerifier
verifier = MongoDBVerifier()
counts = verifier.count_documents_by_type()
print(counts)
"
```

### Success Criteria
- [ ] Counts match expected values
- [ ] Integrity checks work correctly
- [ ] Latency statistics accurate
- [ ] Report formatting readable

---

## Phase 7: Shell Scripts (1.5 hours)

### `setup.sh`
```bash
#!/bin/bash
set -e

echo "🔧 Setting up demo environment..."

# Check PostgreSQL
psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1" > /dev/null
echo "✓ PostgreSQL connected"

# Check Kafka
kafka-topics.sh --bootstrap-server localhost:9092 --list > /dev/null
echo "✓ Kafka connected"

# Check MongoDB
mongosh "$MONGODB_URI" --quiet --eval "db.runCommand({ ping: 1 })" > /dev/null
echo "✓ MongoDB connected"

# Clean data
psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -c "TRUNCATE event_outbox CASCADE;" > /dev/null
mongosh "$MONGODB_URI" --quiet --eval "db.users.deleteMany({}); db.activities.deleteMany({}); db.statistics.deleteMany({});" > /dev/null
echo "✓ Data cleaned"

# Reset Kafka offsets
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group event-processor-group --reset-offsets --to-earliest \
  --topic postgres.activity.event_outbox --execute > /dev/null 2>&1
echo "✓ Kafka offsets reset"

echo "✅ Setup complete!"
```

### `run_demo.sh`
```bash
#!/bin/bash
set -e

TARGET_EVENTS=${TARGET_EVENTS:-100}
LOG_LEVEL=${LOG_LEVEL:-INFO}
BATCH_SIZE=${BATCH_SIZE:-100}

echo "Starting demo with $TARGET_EVENTS events..."

# Start consumer in background with metrics
export METRICS_FILE="demo_metrics_$(date +%Y%m%d_%H%M%S).json"
export LOG_LEVEL=$LOG_LEVEL
python -m app.main &
CONSUMER_PID=$!

# Wait for consumer to start
sleep 3

# Generate events
python -c "
from scripts.demo.lib.event_generator import EventGenerator
gen = EventGenerator()
result = gen.generate_mixed_load($TARGET_EVENTS)
print(f'Generated {result[\"total_events\"]} events')
"

# Run dashboard
python -c "
from scripts.demo.lib.dashboard import EventDashboard
from scripts.demo.lib.metrics_collector import MetricsCollector

dashboard = EventDashboard($TARGET_EVENTS)
collector = MetricsCollector($TARGET_EVENTS)
dashboard.run(collector)
"

# Stop consumer
kill $CONSUMER_PID

echo "Demo complete!"
```

### Individual Load Scripts
```bash
# load_10.sh
#!/bin/bash
TARGET_EVENTS=10 LOG_LEVEL=DEBUG ./scripts/demo/run_demo.sh

# load_100.sh
#!/bin/bash
TARGET_EVENTS=100 LOG_LEVEL=INFO ./scripts/demo/run_demo.sh

# load_1000.sh
#!/bin/bash
TARGET_EVENTS=1000 LOG_LEVEL=WARNING ./scripts/demo/run_demo.sh

# load_10000.sh
#!/bin/bash
TARGET_EVENTS=10000 LOG_LEVEL=ERROR BATCH_SIZE=100 ./scripts/demo/run_demo.sh
```

### `verify.sh`
```bash
#!/bin/bash

echo "📊 Verification Report"
echo "====================="

python -c "
from scripts.demo.lib.mongodb_verifier import MongoDBVerifier
from scripts.demo.lib.latency_tracker import LatencyTracker
import json

verifier = MongoDBVerifier()
counts = verifier.count_documents_by_type()
integrity = verifier.verify_referential_integrity()

print(f\"MongoDB Documents:\")
print(f\"  Users: {counts['users']}\")
print(f\"  Activities: {counts['activities']}\")
print(f\"  Statistics: {counts['statistics']}\")
print(f\"\nIntegrity Check: {'✅ PASS' if integrity['valid'] else '❌ FAIL'}\")

# Load and analyze latency metrics
# (Implementation depends on metrics file format)
"
```

### `full_demo.sh`
```bash
#!/bin/bash
set -e

echo "═══════════════════════════════════════════════════"
echo "   EVENT PROCESSOR - COMPLETE DEMONSTRATION"
echo "═══════════════════════════════════════════════════"

./scripts/demo/setup.sh
echo ""

echo "🔥 Phase 1: Warm-up (10 events)"
./scripts/demo/load_10.sh
sleep 2

echo ""
echo "⚡ Phase 2: Moderate Load (100 events)"
./scripts/demo/load_100.sh
sleep 2

echo ""
echo "🚀 Phase 3: Stress Test (1,000 events)"
./scripts/demo/load_1000.sh
sleep 2

echo ""
echo "💥 Phase 4: Extreme Load (10,000 events)"
./scripts/demo/load_10000.sh
sleep 2

echo ""
echo "📊 Phase 5: Verification & Report"
./scripts/demo/verify.sh

echo ""
echo "✅ Complete demo finished!"
```

### Tasks
- [ ] Create all shell scripts
- [ ] Make executable: `chmod +x scripts/demo/*.sh`
- [ ] Test each script individually
- [ ] Test full_demo.sh sequence

### Success Criteria
- [ ] setup.sh completes without errors
- [ ] Individual load tests run successfully
- [ ] full_demo.sh completes entire sequence
- [ ] verify.sh generates accurate report

---

## Phase 8: Documentation (1 hour)

### File: `scripts/demo/README.md`

### Contents
1. **Quick Start**
   - Installation requirements
   - Environment variables
   - Basic usage examples

2. **Architecture Overview**
   - System components
   - Data flow diagram
   - Timing measurement points

3. **Usage Guide**
   - Individual scripts
   - Load test scenarios
   - Dashboard interpretation

4. **Troubleshooting**
   - Common issues
   - Service verification
   - Debug tips

5. **Advanced Usage**
   - Custom load patterns
   - Metrics analysis
   - Performance tuning

### Tasks
- [ ] Write README.md
- [ ] Add usage examples
- [ ] Document environment variables
- [ ] Add troubleshooting guide

---

## Phase 9: Testing & Refinement (2 hours)

### End-to-End Testing
1. **Test with 10 events**
   ```bash
   ./scripts/demo/setup.sh
   ./scripts/demo/load_10.sh
   ./scripts/demo/verify.sh
   ```
   - Verify each event appears in dashboard
   - Check MongoDB documents created
   - Validate latency measurements

2. **Test with 100 events**
   ```bash
   ./scripts/demo/load_100.sh
   ```
   - Verify throughput calculations
   - Check dashboard updates smoothly
   - Validate metrics accuracy

3. **Test with 1,000 events**
   ```bash
   ./scripts/demo/load_1000.sh
   ```
   - Monitor system performance
   - Check for any bottlenecks
   - Verify error handling

4. **Test with 10,000 events**
   ```bash
   ./scripts/demo/load_10000.sh
   ```
   - Identify system limits
   - Check memory usage
   - Verify batch processing

5. **Test full sequence**
   ```bash
   ./scripts/demo/full_demo.sh
   ```
   - Run complete demo
   - Time total execution
   - Verify final report

### Performance Optimization
- [ ] Profile consumer latency tracking overhead
- [ ] Optimize dashboard refresh rate
- [ ] Tune batch insert sizes
- [ ] Optimize database queries

### Bug Fixes
- [ ] Handle edge cases
- [ ] Improve error messages
- [ ] Add graceful degradation
- [ ] Fix any race conditions

### Tasks
- [ ] Complete end-to-end tests
- [ ] Fix identified issues
- [ ] Optimize performance
- [ ] Validate all success criteria

---

## Success Criteria Summary

### Functional Requirements
✅ Generate realistic events with Faker  
✅ Track end-to-end latency (T0 to T5)  
✅ Real-time dashboard visualization  
✅ Support 10 to 10,000 event loads  
✅ Automated verification and reporting  
✅ Single-command execution  

### Performance Targets
✅ Throughput: > 100 events/second  
✅ P50 Latency: < 30ms  
✅ P95 Latency: < 100ms  
✅ P99 Latency: < 200ms  
✅ Success Rate: > 99.9%  

### Quality Requirements
✅ All existing tests pass (74/74)  
✅ No breaking changes to consumer  
✅ Clean, documented code  
✅ Error handling in all scripts  
✅ Comprehensive documentation  

---

## Next Steps

1. **Start with Phase 1**: Create directory structure and install dependencies
2. **Build incrementally**: Complete each phase before moving to next
3. **Test continuously**: Verify each component works before integration
4. **Document as you go**: Keep README.md updated with changes
5. **Iterate based on feedback**: Refine based on testing results

---

## Quick Reference

### Start Implementation
```bash
cd /mnt/d/activity/event-processor
mkdir -p scripts/demo/lib
touch scripts/demo/lib/__init__.py
pip install rich faker psycopg2-binary pymongo numpy
```

### Run Demo (After Implementation)
```bash
./scripts/demo/full_demo.sh
```

### Verify Tests Still Pass
```bash
pytest tests/ -v
# Should show: 74 passed
```

---

## Files to Create

**Python Modules (5 files):**
- `scripts/demo/lib/event_generator.py` (~200 lines)
- `scripts/demo/lib/dashboard.py` (~300 lines)
- `scripts/demo/lib/metrics_collector.py` (~150 lines)
- `scripts/demo/lib/mongodb_verifier.py` (~100 lines)
- `scripts/demo/lib/latency_tracker.py` (~80 lines)

**Shell Scripts (9 files):**
- `scripts/demo/setup.sh` (~50 lines)
- `scripts/demo/cleanup.sh` (~20 lines)
- `scripts/demo/run_demo.sh` (~60 lines)
- `scripts/demo/load_10.sh` (~3 lines)
- `scripts/demo/load_100.sh` (~3 lines)
- `scripts/demo/load_1000.sh` (~3 lines)
- `scripts/demo/load_10000.sh` (~3 lines)
- `scripts/demo/monitor.sh` (~10 lines)
- `scripts/demo/verify.sh` (~30 lines)
- `scripts/demo/full_demo.sh` (~40 lines)

**Documentation (2 files):**
- `scripts/demo/README.md` (~400 lines)
- Update existing README.md with demo instructions

**Code Modifications (2 files):**
- `app/consumer.py` (+80 lines)
- `app/models.py` (+15 lines)

**Total: ~18 new files, 2 modified files, ~1500 lines of code**

---

Ready to start implementation? Begin with Phase 1!
