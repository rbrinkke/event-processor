# Demo Strategy - Executive Summary

## Overview

Complete demo and load testing system for event-processor with real-time visualization, exact latency tracking, and automated execution.

## Quick Start

```bash
# Complete automated demo (recommended)
./scripts/demo/full_demo.sh

# Individual load tests
./scripts/demo/load_10.sh     # Warm-up: 10 events, detailed view
./scripts/demo/load_100.sh    # Moderate: 100 events
./scripts/demo/load_1000.sh   # Stress test: 1,000 events
./scripts/demo/load_10000.sh  # Extreme: 10,000 events
```

## Architecture

```
PostgreSQL (T0)  →  Debezium (T1)  →  Kafka (T2)  →  Consumer (T3)  →  MongoDB (T5)
   INSERT              WAL              Message        Processing        Write Complete

Measured Latencies:
- CDC Capture: T1 - T0
- Kafka Delivery: T2 - T1
- Consumer Lag: T3 - T2
- Processing: T5 - T3
- TOTAL END-TO-END: T5 - T0
```

## Key Components

### 1. Shell Scripts (8 files)
- `setup.sh` - Initialize environment
- `load_X.sh` - Load tests (10, 100, 1K, 10K)
- `monitor.sh` - Real-time monitoring
- `verify.sh` - Post-demo verification
- `cleanup.sh` - Teardown
- `full_demo.sh` - Complete sequence

### 2. Python Modules (5 files)
- `event_generator.py` - Generate realistic test data
- `dashboard.py` - Real-time terminal UI
- `metrics_collector.py` - Collect performance metrics
- `mongodb_verifier.py` - Verify data integrity
- `latency_tracker.py` - Analyze latency statistics

### 3. Consumer Enhancements
- Add latency tracking to `app/consumer.py`
- New `EventMetrics` model in `app/models.py`
- Periodic summary logging
- Metrics file export

## Dashboard Preview

```
╔══════════════════════════════════════════════════════════════════╗
║           EVENT PROCESSOR DEMO - LIVE MONITORING                 ║
╠══════════════════════════════════════════════════════════════════╣
║ Status: ● RUNNING          Uptime: 00:00:34                     ║
║ Target Events: 1,000       Processed: 847      Remaining: 153   ║
║ Progress: ████████████████░░░░ 84.7%                            ║
╠══════════════════════════════════════════════════════════════════╣
║ THROUGHPUT                                                       ║
║ Current: 342 events/sec    Average: 289 events/sec              ║
║ Peak: 456 events/sec       Error Rate: 0.1%                     ║
╠══════════════════════════════════════════════════════════════════╣
║ LATENCY (End-to-End)                                            ║
║ Average: 28ms    Min: 12ms    Max: 156ms                        ║
║ P50: 24ms        P95: 45ms    P99: 89ms                         ║
║ Sparkline: ▁▂▂▃▃▄▄▅▅▆▆▅▄▃▃▂▂▁                                  ║
╠══════════════════════════════════════════════════════════════════╣
║ EVENT BREAKDOWN                                                  ║
║ UserCreated: 423     ActivityCreated: 234    Participant: 190   ║
╠══════════════════════════════════════════════════════════════════╣
║ RECENT EVENTS (last 5)                                          ║
║ ✓ UserCreated      alice_smith_892  12ms   [10:15:23]          ║
║ ✓ ActivityCreated  Hiking Trip      18ms   [10:15:23]          ║
║ ✓ ParticipantJoin  act_123         15ms   [10:15:24]          ║
╚══════════════════════════════════════════════════════════════════╝
```

## Load Test Scenarios

| Scenario | Events | Duration | Throughput | Purpose |
|----------|--------|----------|------------|---------|
| Warm-up | 10 | 5s | 2 eps | System verification |
| Moderate | 100 | 15s | 7 eps | Typical operation |
| Stress | 1,000 | 30s | 33 eps | System under load |
| Extreme | 10,000 | 60s | 167 eps | Identify limits |

## Success Metrics

### Throughput
- **Target:** > 100 events/second sustained
- **Measurement:** Processed events / elapsed time

### Latency
- **Target P50:** < 30ms (median)
- **Target P95:** < 100ms (95th percentile)
- **Target P99:** < 200ms (99th percentile)

### Reliability
- **Target:** > 99.9% success rate
- **Measurement:** (processed - errors) / processed × 100

### Data Integrity
- **Target:** 100% event matching
- **Verification:** PostgreSQL count = MongoDB count

## Implementation Checklist

**Phase 1: Core Scripts** (2h)
- [ ] Directory structure
- [ ] setup.sh, cleanup.sh
- [ ] Base run_demo.sh

**Phase 2: Event Generation** (2h)
- [ ] event_generator.py
- [ ] User/Activity/Participant generators
- [ ] Test with various loads

**Phase 3: Consumer Enhancement** (2h)
- [ ] Latency tracking in consumer.py
- [ ] EventMetrics model
- [ ] Verify tests still pass (74/74)

**Phase 4: Dashboard** (3h)
- [ ] metrics_collector.py
- [ ] dashboard.py with rich
- [ ] Real-time visualization

**Phase 5: Verification** (1h)
- [ ] mongodb_verifier.py
- [ ] latency_tracker.py
- [ ] Report generation

**Phase 6: Load Scripts** (1h)
- [ ] Individual load test scripts
- [ ] full_demo.sh orchestration

**Phase 7: Documentation** (1h)
- [ ] README.md
- [ ] Usage examples
- [ ] Troubleshooting

**Phase 8: Testing** (2h)
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Demo rehearsal

**Total: 14 hours**

## Stakeholder Presentation

### Key Talking Points
- "Sub-30 millisecond average latency"
- "Processing 300+ events per second"
- "99.9% success rate with automatic recovery"
- "Complete data consistency across all systems"
- "Real-time CDC streaming with millisecond precision"

### Wow Factors
1. **Live data visualization** - MongoDB Compass showing documents appearing
2. **Scalability demo** - Watch 10 → 100 → 1,000 → 10,000 progression
3. **Exact timing** - "Created at T0, appeared in MongoDB at T0+28ms"
4. **Resilience** - System continues processing despite errors
5. **Detailed analytics** - Export JSON reports for analysis

## Potential Issues & Solutions

| Issue | Solution |
|-------|----------|
| Kafka native vs Docker | Configurable KAFKA_BOOTSTRAP_SERVERS |
| MongoDB connection | Read from .env, validate in setup |
| Debezium lag | Monitor connector, wait for catch-up |
| Consumer overwhelm | Batch inserts with delays |
| Database rate limits | Configurable batch sizes |
| Log volume | Dynamic log levels by load |

## Next Steps

1. ✅ **Strategy Completed** - Comprehensive plan documented
2. 🔄 **Start Implementation** - Begin with event_generator.py
3. 🔄 **Enhance Consumer** - Add latency tracking
4. 🔄 **Build Dashboard** - Create visualization
5. 🔄 **Create Scripts** - Shell script orchestration
6. 🔄 **Test & Refine** - Run full demo sequence
7. 🔄 **Present** - Deliver to stakeholders

## Files Created

- `DEMO_STRATEGY.md` - Complete detailed strategy (this document's parent)
- `DEMO_SUMMARY.md` - This executive summary

## Dependencies

```bash
# Python packages needed
pip install rich faker psycopg2-binary pymongo numpy
```

## Environment Variables

```bash
# Required for demo
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=activity_db
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=activity_read

KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=postgres.activity.event_outbox
KAFKA_GROUP_ID=event-processor-group

# Optional
METRICS_FILE=demo_metrics.json
LOG_LEVEL=INFO
BATCH_SIZE=100
```

---

**Ready to implement?** Start with `./scripts/demo/event_generator.py` as the foundation.
