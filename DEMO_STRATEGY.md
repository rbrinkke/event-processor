# Event Processor Demo & Load Testing Strategy

## Executive Summary

Comprehensive demo and load testing system for the event-processor proof of concept, designed to showcase real-time event streaming from PostgreSQL → Kafka → Python Consumer → MongoDB with exact timing measurements and impressive visual presentation.

**Key Features:**
- Single-command demo execution
- Real-time visual dashboard
- Exact end-to-end latency tracking (millisecond precision)
- Scalable load testing (10 to 10,000 events)
- Automated verification and reporting
- Stakeholder-friendly metrics

---

## Architecture Overview

### Data Flow with Timing Points

```
T0: PostgreSQL INSERT          →  T1: Debezium WAL Capture
     event_outbox                      ↓
                                   T2: Kafka Message
                                       ↓
T5: MongoDB Write Complete     ←  T3: Consumer Processing Start
     ↓                                 ↓
T6: Handler Complete              T4: Handler Execution
```

**Measured Latencies:**
1. **CDC Capture**: T1 - T0 (PostgreSQL WAL → Debezium)
2. **Kafka Delivery**: T2 - T1 (Debezium → Kafka)
3. **Consumer Lag**: T3 - T2 (Kafka → Consumer poll)
4. **Processing Time**: T5 - T3 (Handler execution)
5. **Total End-to-End**: T5 - T0 (Complete journey)

---

## Component Design

### 1. Shell Scripts (`scripts/demo/`)

#### `setup.sh` - Environment Preparation
```bash
#!/bin/bash
# Verify all services running
# - PostgreSQL (port 5432)
# - Kafka (port 9092)
# - MongoDB (Atlas/local)
# - Debezium connector

# Install dependencies
pip install -q rich faker psycopg2-binary pymongo numpy

# Clean previous demo data
psql -c "TRUNCATE event_outbox CASCADE;"
mongo --eval "db.users.deleteMany({}); db.activities.deleteMany({});"

# Reset Kafka consumer group offset
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group event-processor-group --reset-offsets --to-earliest \
  --topic postgres.activity.event_outbox --execute

# Verify connectivity
python scripts/demo/lib/verify_connections.py
```

#### `load_10.sh` - Detailed View Demo
```bash
#!/bin/bash
# 10 events with detailed logging
TARGET_EVENTS=10 LOG_LEVEL=DEBUG ./scripts/demo/run_demo.sh
```

#### `load_100.sh` - Moderate Load Demo
```bash
#!/bin/bash
# 100 events with standard logging
TARGET_EVENTS=100 LOG_LEVEL=INFO ./scripts/demo/run_demo.sh
```

#### `load_1000.sh` - Stress Test Demo
```bash
#!/bin/bash
# 1,000 events - stress test
TARGET_EVENTS=1000 LOG_LEVEL=WARNING ./scripts/demo/run_demo.sh
```

#### `load_10000.sh` - Extreme Load Demo
```bash
#!/bin/bash
# 10,000 events - extreme load test
TARGET_EVENTS=10000 LOG_LEVEL=ERROR BATCH_SIZE=100 ./scripts/demo/run_demo.sh
```

#### `monitor.sh` - Real-time Monitoring
```bash
#!/bin/bash
# Launch dashboard without generating new events
python scripts/demo/lib/dashboard.py --monitor-only
```

#### `verify.sh` - Post-Demo Verification
```bash
#!/bin/bash
# Comprehensive verification and reporting
python scripts/demo/lib/verify_results.py --report
```

#### `cleanup.sh` - Teardown
```bash
#!/bin/bash
# Clean demo artifacts
rm -f demo_metrics_*.json
psql -c "TRUNCATE event_outbox;"
mongo --eval "db.dropDatabase();"
```

#### `full_demo.sh` - Complete Automated Demo
```bash
#!/bin/bash
set -e

echo "═══════════════════════════════════════════════════"
echo "   EVENT PROCESSOR - COMPLETE DEMONSTRATION"
echo "═══════════════════════════════════════════════════"
echo

# Phase 1: Setup
echo "🔧 Phase 1: Environment Setup"
./scripts/demo/setup.sh
sleep 2

# Phase 2: Warm-up
echo "🔥 Phase 2: Warm-up (10 events - detailed view)"
./scripts/demo/load_10.sh
sleep 3

# Phase 3: Moderate Load
echo "⚡ Phase 3: Moderate Load (100 events)"
./scripts/demo/load_100.sh
sleep 3

# Phase 4: Stress Test
echo "🚀 Phase 4: Stress Test (1,000 events)"
./scripts/demo/load_1000.sh
sleep 3

# Phase 5: Extreme Load
echo "💥 Phase 5: Extreme Load (10,000 events)"
./scripts/demo/load_10000.sh
sleep 3

# Phase 6: Final Report
echo "📊 Phase 6: Verification & Performance Report"
./scripts/demo/verify.sh

echo
echo "✅ Demo Complete! Check demo_report.json for detailed metrics."
```

**Total Demo Time:** ~2.5 minutes

---

### 2. Python Modules (`scripts/demo/lib/`)

#### `event_generator.py` - Event Generation
```python
"""
Event Generator for Load Testing
Generates realistic events with proper referential integrity
"""

from faker import Faker
from uuid import uuid4
from datetime import datetime
import psycopg2
from typing import List, Dict
import os

fake = Faker()

class EventGenerator:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", 5432),
            dbname=os.getenv("POSTGRES_DB", "activity_db"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        
    def generate_user_created_events(self, count: int) -> List[uuid4]:
        """Generate UserCreated events with realistic data"""
        user_ids = []
        events = []
        
        for _ in range(count):
            user_id = uuid4()
            user_ids.append(user_id)
            
            event = {
                'event_id': uuid4(),
                'aggregate_id': user_id,
                'aggregate_type': 'User',
                'event_type': 'UserCreated',
                'payload': {
                    'email': fake.email(),
                    'username': fake.user_name(),
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'bio': fake.text(max_nb_chars=200)
                }
            }
            events.append(event)
        
        self._insert_events_batch(events)
        return user_ids
    
    def generate_activity_created_events(self, count: int, user_ids: List[uuid4]) -> List[uuid4]:
        """Generate ActivityCreated events"""
        activity_ids = []
        events = []
        
        for _ in range(count):
            activity_id = uuid4()
            activity_ids.append(activity_id)
            
            event = {
                'event_id': uuid4(),
                'aggregate_id': activity_id,
                'aggregate_type': 'Activity',
                'event_type': 'ActivityCreated',
                'payload': {
                    'title': fake.catch_phrase(),
                    'description': fake.text(),
                    'creator_user_id': str(fake.random.choice(user_ids)),
                    'max_participants': fake.random.randint(5, 50),
                    'location_name': fake.city(),
                    'location_address': fake.address(),
                    'start_date': fake.future_datetime().isoformat(),
                    'timezone': 'UTC'
                }
            }
            events.append(event)
        
        self._insert_events_batch(events)
        return activity_ids
    
    def generate_participant_joined_events(self, count: int, activity_ids: List[uuid4], user_ids: List[uuid4]):
        """Generate ParticipantJoined events"""
        events = []
        
        for _ in range(count):
            event = {
                'event_id': uuid4(),
                'aggregate_id': fake.random.choice(activity_ids),
                'aggregate_type': 'Activity',
                'event_type': 'ParticipantJoined',
                'payload': {
                    'user_id': str(fake.random.choice(user_ids))
                }
            }
            events.append(event)
        
        self._insert_events_batch(events)
    
    def _insert_events_batch(self, events: List[Dict]):
        """Insert events into PostgreSQL with timing"""
        cursor = self.conn.cursor()
        
        insert_sql = """
        INSERT INTO event_outbox 
        (event_id, aggregate_id, aggregate_type, event_type, payload, status, created_at)
        VALUES (%s, %s, %s, %s, %s, 'pending', NOW())
        """
        
        for event in events:
            cursor.execute(insert_sql, (
                str(event['event_id']),
                str(event['aggregate_id']),
                event['aggregate_type'],
                event['event_type'],
                psycopg2.extras.Json(event['payload'])
            ))
        
        self.conn.commit()
        cursor.close()
    
    def generate_mixed_load(self, total_events: int) -> Dict:
        """Generate a realistic mix of events"""
        # 50% users, 30% activities, 20% participants
        user_count = int(total_events * 0.5)
        activity_count = int(total_events * 0.3)
        participant_count = int(total_events * 0.2)
        
        print(f"Generating {total_events} events:")
        print(f"  - {user_count} UserCreated")
        print(f"  - {activity_count} ActivityCreated")
        print(f"  - {participant_count} ParticipantJoined")
        
        start_time = datetime.utcnow()
        
        user_ids = self.generate_user_created_events(user_count)
        activity_ids = self.generate_activity_created_events(activity_count, user_ids)
        self.generate_participant_joined_events(participant_count, activity_ids, user_ids)
        
        end_time = datetime.utcnow()
        
        return {
            'total_events': total_events,
            'start_time': start_time,
            'end_time': end_time,
            'generation_time_seconds': (end_time - start_time).total_seconds()
        }
```

#### `dashboard.py` - Real-time Terminal Dashboard
```python
"""
Real-time Event Processing Dashboard
Uses rich library for terminal UI
"""

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.text import Text
import time
from datetime import datetime
from collections import deque
from typing import Dict, List
import json

class EventDashboard:
    def __init__(self, target_events: int):
        self.console = Console()
        self.target_events = target_events
        self.processed = 0
        self.errors = 0
        self.start_time = time.time()
        self.recent_events = deque(maxlen=5)
        self.latencies = deque(maxlen=100)
        self.event_counts = {'UserCreated': 0, 'ActivityCreated': 0, 'ParticipantJoined': 0}
        
    def update_metrics(self, metrics: Dict):
        """Update dashboard with new metrics"""
        self.processed = metrics.get('processed', 0)
        self.errors = metrics.get('errors', 0)
        self.latencies.extend(metrics.get('recent_latencies', []))
        
        for event in metrics.get('recent_events', []):
            self.recent_events.append(event)
            event_type = event.get('event_type', 'Unknown')
            if event_type in self.event_counts:
                self.event_counts[event_type] += 1
    
    def generate_layout(self) -> Layout:
        """Generate dashboard layout"""
        layout = Layout()
        
        layout.split(
            Layout(name="header", size=3),
            Layout(name="stats", size=8),
            Layout(name="latency", size=6),
            Layout(name="breakdown", size=4),
            Layout(name="recent", size=8)
        )
        
        # Header
        layout["header"].update(Panel(
            Text("EVENT PROCESSOR DEMO - LIVE MONITORING", style="bold cyan", justify="center"),
            style="cyan"
        ))
        
        # Stats
        uptime = time.time() - self.start_time
        progress_pct = (self.processed / self.target_events * 100) if self.target_events > 0 else 0
        remaining = self.target_events - self.processed
        
        stats_table = Table.grid(padding=1)
        stats_table.add_column(style="cyan")
        stats_table.add_column(style="white")
        
        status = "● RUNNING" if remaining > 0 else "● COMPLETE"
        status_color = "green" if remaining > 0 else "blue"
        
        stats_table.add_row("Status:", Text(status, style=status_color))
        stats_table.add_row("Uptime:", f"{uptime:.1f}s")
        stats_table.add_row("Target Events:", f"{self.target_events:,}")
        stats_table.add_row("Processed:", f"{self.processed:,}")
        stats_table.add_row("Remaining:", f"{remaining:,}")
        stats_table.add_row("Progress:", f"{progress_pct:.1f}%")
        
        layout["stats"].update(Panel(stats_table, title="Statistics", border_style="green"))
        
        # Latency
        if self.latencies:
            latencies_list = list(self.latencies)
            avg_latency = sum(latencies_list) / len(latencies_list)
            min_latency = min(latencies_list)
            max_latency = max(latencies_list)
            
            # Calculate percentiles
            sorted_latencies = sorted(latencies_list)
            p50_idx = int(len(sorted_latencies) * 0.50)
            p95_idx = int(len(sorted_latencies) * 0.95)
            p99_idx = int(len(sorted_latencies) * 0.99)
            
            p50 = sorted_latencies[p50_idx] if p50_idx < len(sorted_latencies) else 0
            p95 = sorted_latencies[p95_idx] if p95_idx < len(sorted_latencies) else 0
            p99 = sorted_latencies[p99_idx] if p99_idx < len(sorted_latencies) else 0
            
            latency_table = Table.grid(padding=1)
            latency_table.add_column(style="cyan")
            latency_table.add_column(style="white")
            
            latency_table.add_row("Average:", f"{avg_latency:.1f}ms")
            latency_table.add_row("Min:", f"{min_latency:.1f}ms")
            latency_table.add_row("Max:", f"{max_latency:.1f}ms")
            latency_table.add_row("P50:", f"{p50:.1f}ms")
            latency_table.add_row("P95:", f"{p95:.1f}ms")
            latency_table.add_row("P99:", f"{p99:.1f}ms")
            
            # Sparkline (simple version)
            sparkline = "".join([self._get_spark_char(l, min_latency, max_latency) for l in latencies_list[-20:]])
            latency_table.add_row("Trend:", sparkline)
            
            layout["latency"].update(Panel(latency_table, title="Latency (End-to-End)", border_style="yellow"))
        
        # Event Breakdown
        breakdown_table = Table.grid(padding=1)
        breakdown_table.add_column(style="cyan")
        breakdown_table.add_column(style="white")
        
        for event_type, count in self.event_counts.items():
            breakdown_table.add_row(f"{event_type}:", f"{count:,}")
        
        layout["breakdown"].update(Panel(breakdown_table, title="Event Breakdown", border_style="magenta"))
        
        # Recent Events
        recent_table = Table(show_header=True, header_style="bold")
        recent_table.add_column("Status", width=3)
        recent_table.add_column("Event Type", width=20)
        recent_table.add_column("Latency", width=10)
        recent_table.add_column("Time", width=12)
        
        for event in reversed(list(self.recent_events)):
            status = "✓" if event.get('success', True) else "✗"
            status_color = "green" if event.get('success', True) else "red"
            event_type = event.get('event_type', 'Unknown')
            latency = f"{event.get('latency_ms', 0):.1f}ms"
            event_time = datetime.fromtimestamp(event.get('timestamp', time.time())).strftime("%H:%M:%S")
            
            recent_table.add_row(
                Text(status, style=status_color),
                event_type,
                latency,
                event_time
            )
        
        layout["recent"].update(Panel(recent_table, title="Recent Events", border_style="blue"))
        
        return layout
    
    def _get_spark_char(self, value: float, min_val: float, max_val: float) -> str:
        """Get sparkline character for value"""
        if max_val == min_val:
            return "▄"
        
        ratio = (value - min_val) / (max_val - min_val)
        chars = "▁▂▃▄▅▆▇█"
        idx = int(ratio * (len(chars) - 1))
        return chars[idx]
    
    def run(self, metrics_collector):
        """Run live dashboard"""
        with Live(self.generate_layout(), refresh_per_second=2, console=self.console) as live:
            while self.processed < self.target_events:
                metrics = metrics_collector.get_summary_stats()
                self.update_metrics(metrics)
                live.update(self.generate_layout())
                time.sleep(0.5)
            
            # Final update
            metrics = metrics_collector.get_summary_stats()
            self.update_metrics(metrics)
            live.update(self.generate_layout())
```

#### `metrics_collector.py` - Metrics Collection
```python
"""
Metrics Collector
Collects metrics from consumer logs and databases
"""

import json
import subprocess
from typing import Dict, List
from datetime import datetime
import time
from pymongo import MongoClient
import psycopg2
import os

class MetricsCollector:
    def __init__(self, target_events: int, output_file: str = "demo_metrics.json"):
        self.target_events = target_events
        self.output_file = output_file
        self.start_time = time.time()
        self.metrics = []
        
        # MongoDB connection
        self.mongo_client = MongoClient(os.getenv("MONGODB_URI"))
        self.mongo_db = self.mongo_client[os.getenv("MONGODB_DATABASE", "activity_read")]
        
        # PostgreSQL connection
        self.pg_conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", 5432),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
    
    def tail_consumer_logs(self):
        """Tail consumer logs and extract metrics"""
        # Implementation depends on how consumer outputs logs
        # Could use subprocess to tail log file or read from stdout
        pass
    
    def query_mongodb_stats(self) -> Dict:
        """Query MongoDB for document counts"""
        return {
            'users': self.mongo_db.users.count_documents({}),
            'activities': self.mongo_db.activities.count_documents({}),
            'statistics': self.mongo_db.statistics.count_documents({})
        }
    
    def query_postgres_stats(self) -> Dict:
        """Query PostgreSQL event_outbox stats"""
        cursor = self.pg_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM event_outbox")
        total_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM event_outbox WHERE status = 'processed'")
        processed_events = cursor.fetchone()[0]
        
        cursor.close()
        
        return {
            'total_events': total_events,
            'processed_events': processed_events
        }
    
    def get_kafka_consumer_lag(self) -> int:
        """Get Kafka consumer group lag"""
        try:
            result = subprocess.run([
                'kafka-consumer-groups.sh',
                '--bootstrap-server', os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
                '--group', 'event-processor-group',
                '--describe'
            ], capture_output=True, text=True)
            
            # Parse output to extract lag
            # Format: GROUP TOPIC PARTITION CURRENT-OFFSET LOG-END-OFFSET LAG
            for line in result.stdout.split('\n'):
                if 'event_outbox' in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        return int(parts[5])
        except Exception as e:
            print(f"Warning: Could not get Kafka lag: {e}")
        
        return 0
    
    def get_summary_stats(self) -> Dict:
        """Get current summary statistics"""
        mongo_stats = self.query_mongodb_stats()
        processed = sum(mongo_stats.values())
        
        uptime = time.time() - self.start_time
        throughput = processed / uptime if uptime > 0 else 0
        
        return {
            'processed': processed,
            'errors': 0,  # To be populated from consumer logs
            'throughput_current': throughput,
            'mongodb_stats': mongo_stats,
            'recent_latencies': [],  # To be populated from consumer metrics
            'recent_events': []  # To be populated from consumer logs
        }
    
    def save_final_report(self):
        """Save final metrics report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'target_events': self.target_events,
            'duration_seconds': time.time() - self.start_time,
            'mongodb_stats': self.query_mongodb_stats(),
            'postgres_stats': self.query_postgres_stats(),
            'metrics': self.metrics
        }
        
        with open(self.output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Metrics saved to: {self.output_file}")
```

#### `mongodb_verifier.py` - MongoDB Verification
```python
"""
MongoDB Verifier
Verify data integrity and completeness
"""

from pymongo import MongoClient
from typing import Dict, List
import os

class MongoDBVerifier:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.client[os.getenv("MONGODB_DATABASE", "activity_read")]
    
    def count_documents_by_type(self) -> Dict:
        """Count documents in each collection"""
        return {
            'users': self.db.users.count_documents({}),
            'activities': self.db.activities.count_documents({}),
            'statistics': self.db.statistics.count_documents({})
        }
    
    def verify_referential_integrity(self) -> Dict:
        """Verify referential integrity"""
        issues = []
        
        # Check: all activity creators exist as users
        activities = self.db.activities.find({}, {'creator_id': 1})
        activity_creator_ids = set([a['creator_id'] for a in activities if 'creator_id' in a])
        
        user_ids = set([str(u['_id']) for u in self.db.users.find({}, {'_id': 1})])
        
        missing_users = activity_creator_ids - user_ids
        if missing_users:
            issues.append(f"Activities reference {len(missing_users)} non-existent users")
        
        # Check: all participants exist as users
        for activity in self.db.activities.find({'participants.list': {'$exists': True}}):
            participant_ids = [p['user_id'] for p in activity.get('participants', {}).get('list', [])]
            missing = set(participant_ids) - user_ids
            if missing:
                issues.append(f"Activity {activity['_id']} has {len(missing)} non-existent participants")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    def get_latest_documents(self, collection_name: str, limit: int = 5) -> List[Dict]:
        """Get most recently created documents"""
        collection = self.db[collection_name]
        return list(collection.find().sort('metadata.created_at', -1).limit(limit))
    
    def verify_event_ids(self, event_ids: List[str]) -> Dict:
        """Verify all event IDs made it to MongoDB"""
        found_events = set()
        
        for collection_name in ['users', 'activities']:
            collection = self.db[collection_name]
            docs = collection.find(
                {'metadata.source_event_id': {'$in': event_ids}},
                {'metadata.source_event_id': 1}
            )
            found_events.update([d['metadata']['source_event_id'] for d in docs])
        
        missing = set(event_ids) - found_events
        
        return {
            'total_events': len(event_ids),
            'found_events': len(found_events),
            'missing_events': len(missing),
            'success_rate': len(found_events) / len(event_ids) * 100 if event_ids else 0
        }
```

#### `latency_tracker.py` - Latency Analysis
```python
"""
Latency Tracker
Analyze and report latency metrics
"""

import numpy as np
from typing import List, Dict
import json

class LatencyTracker:
    def __init__(self):
        self.latencies = []
    
    def add_latency(self, latency_ms: float):
        """Add a latency measurement"""
        self.latencies.append(latency_ms)
    
    def calculate_statistics(self) -> Dict:
        """Calculate latency statistics"""
        if not self.latencies:
            return {}
        
        latencies_array = np.array(self.latencies)
        
        return {
            'count': len(self.latencies),
            'min_ms': float(np.min(latencies_array)),
            'max_ms': float(np.max(latencies_array)),
            'mean_ms': float(np.mean(latencies_array)),
            'median_ms': float(np.median(latencies_array)),
            'std_ms': float(np.std(latencies_array)),
            'p50_ms': float(np.percentile(latencies_array, 50)),
            'p75_ms': float(np.percentile(latencies_array, 75)),
            'p90_ms': float(np.percentile(latencies_array, 90)),
            'p95_ms': float(np.percentile(latencies_array, 95)),
            'p99_ms': float(np.percentile(latencies_array, 99)),
            'p999_ms': float(np.percentile(latencies_array, 99.9))
        }
    
    def generate_report(self) -> str:
        """Generate human-readable latency report"""
        stats = self.calculate_statistics()
        
        if not stats:
            return "No latency data available"
        
        report = f"""
LATENCY ANALYSIS REPORT
{'='*60}

Total Measurements: {stats['count']:,}

Central Tendency:
  Mean:     {stats['mean_ms']:.2f}ms
  Median:   {stats['median_ms']:.2f}ms
  Std Dev:  {stats['std_ms']:.2f}ms

Range:
  Minimum:  {stats['min_ms']:.2f}ms
  Maximum:  {stats['max_ms']:.2f}ms

Percentiles:
  P50 (median):     {stats['p50_ms']:.2f}ms
  P75:              {stats['p75_ms']:.2f}ms
  P90:              {stats['p90_ms']:.2f}ms
  P95:              {stats['p95_ms']:.2f}ms
  P99:              {stats['p99_ms']:.2f}ms
  P99.9:            {stats['p999_ms']:.2f}ms

Performance Assessment:
"""
        
        # Add assessment
        if stats['p95_ms'] < 50:
            report += "  ✅ EXCELLENT - 95% of events processed in < 50ms\n"
        elif stats['p95_ms'] < 100:
            report += "  ✓ GOOD - 95% of events processed in < 100ms\n"
        elif stats['p95_ms'] < 200:
            report += "  ⚠ ACCEPTABLE - 95% of events processed in < 200ms\n"
        else:
            report += "  ⚠ NEEDS OPTIMIZATION - High P95 latency\n"
        
        return report
    
    def export_to_json(self, filename: str):
        """Export latency data to JSON"""
        data = {
            'statistics': self.calculate_statistics(),
            'raw_latencies': self.latencies
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
```

---

### 3. Consumer Enhancements

#### Modified `app/consumer.py`

Add latency tracking capabilities:

```python
class EventConsumer:
    def __init__(self):
        # ... existing code ...
        self._latency_metrics: List[Dict] = []
        self._metrics_file = os.getenv("METRICS_FILE", None)
        self._last_summary_time = time.time()
        self._summary_interval = 10.0  # seconds
    
    async def process_message(self, message) -> Optional[ProcessingResult]:
        """Enhanced process_message with latency tracking"""
        processing_start = time.time()
        
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
            
            # Extract timestamps for latency tracking
            t0_created = event.created_at.timestamp()
            t1_kafka = debezium_payload.ts_ms / 1000.0  # Kafka timestamp in ms
            t2_message = message.timestamp / 1000.0  # Message timestamp
            t3_processing_start = processing_start
            
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
                    self._error_count += 1
            
            # Processing complete
            processing_end = time.time()
            t5_end = processing_end
            
            # Calculate latencies
            kafka_lag_ms = (t3_processing_start - t1_kafka) * 1000
            processing_time_ms = (t5_end - t3_processing_start) * 1000
            total_latency_ms = (t5_end - t0_created) * 1000
            
            # Store detailed metrics
            metric = {
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "t0_created": t0_created,
                "t1_kafka": t1_kafka,
                "t3_start": t3_processing_start,
                "t5_end": t5_end,
                "kafka_lag_ms": round(kafka_lag_ms, 2),
                "processing_time_ms": round(processing_time_ms, 2),
                "total_latency_ms": round(total_latency_ms, 2),
                "timestamp": processing_end
            }
            
            self._latency_metrics.append(metric)
            
            # Optional: write to file
            if self._metrics_file:
                self._append_metric_to_file(metric)
            
            self._processing_count += 1
            
            # Periodic summary logging
            if time.time() - self._last_summary_time > self._summary_interval:
                self._log_summary()
                self._last_summary_time = time.time()
            
            logger.info(
                "event_processed",
                event_type=event.event_type,
                event_id=str(event.event_id),
                processing_time_ms=round(processing_time_ms, 2),
                total_latency_ms=round(total_latency_ms, 2),
                kafka_lag_ms=round(kafka_lag_ms, 2),
                total_processed=self._processing_count,
            )
            
            return ProcessingResult(
                success=True,
                event_id=event.event_id,
                event_type=event.event_type,
                handler_name="multiple",
                processing_time_ms=processing_time_ms,
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
    
    def _append_metric_to_file(self, metric: Dict):
        """Append metric to file"""
        try:
            with open(self._metrics_file, 'a') as f:
                f.write(json.dumps(metric) + '\n')
        except Exception as e:
            logger.error("failed_to_write_metric", error=str(e))
    
    def _log_summary(self):
        """Log periodic summary statistics"""
        if not self._latency_metrics:
            return
        
        recent_metrics = self._latency_metrics[-100:]  # Last 100 events
        
        latencies = [m['total_latency_ms'] for m in recent_metrics]
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        uptime = time.time() - self._start_time
        throughput = self._processing_count / uptime if uptime > 0 else 0
        
        logger.info(
            "processing_summary",
            total_processed=self._processing_count,
            total_errors=self._error_count,
            throughput_eps=round(throughput, 2),
            avg_latency_ms=round(avg_latency, 2),
            min_latency_ms=round(min_latency, 2),
            max_latency_ms=round(max_latency, 2),
            uptime_seconds=round(uptime, 2)
        )
    
    @property
    def detailed_stats(self) -> Dict[str, Any]:
        """Get detailed consumer statistics including latencies"""
        if not self._latency_metrics:
            return self.stats
        
        latencies = [m['total_latency_ms'] for m in self._latency_metrics]
        
        return {
            **self.stats,
            "total_events_tracked": len(self._latency_metrics),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "min_latency_ms": round(min(latencies), 2) if latencies else 0,
            "max_latency_ms": round(max(latencies), 2) if latencies else 0,
        }
```

#### New Model in `app/models.py`

```python
class EventMetrics(BaseModel):
    """Detailed event processing metrics"""
    
    event_id: UUID4
    event_type: str
    t0_created: float  # PostgreSQL insert time (unix timestamp)
    t1_kafka: float    # Debezium capture time
    t3_start: float    # Consumer processing start
    t5_end: float      # Consumer processing end
    kafka_lag_ms: float
    processing_time_ms: float
    total_latency_ms: float
    timestamp: float
```

---

## Load Test Scenarios

### Scenario 1: Warm-up (10 events)
**Purpose:** Verify system connectivity and warm up components

- **Events:** 10 UserCreated
- **Expected Duration:** 5 seconds
- **Expected Throughput:** 2 events/second
- **Dashboard:** Detailed view, show each event

### Scenario 2: Moderate Load (100 events)
**Purpose:** Demonstrate typical operational load

- **Events:** 50 UserCreated + 30 ActivityCreated + 20 ParticipantJoined
- **Expected Duration:** 15 seconds
- **Expected Throughput:** 6-7 events/second
- **Dashboard:** Standard view with aggregations

### Scenario 3: Stress Test (1,000 events)
**Purpose:** Test system under stress

- **Events:** 500 UserCreated + 300 ActivityCreated + 200 ParticipantJoined
- **Expected Duration:** 30 seconds
- **Expected Throughput:** 30-40 events/second
- **Dashboard:** Aggregated view, focus on performance metrics

### Scenario 4: Extreme Load (10,000 events)
**Purpose:** Identify system limits and bottlenecks

- **Events:** 5,000 UserCreated + 3,000 ActivityCreated + 2,000 ParticipantJoined
- **Expected Duration:** 60-90 seconds
- **Expected Throughput:** 100+ events/second
- **Dashboard:** High-level metrics only, minimal logging
- **Strategy:** Batch inserts (100 events per batch with 50ms delay)

---

## Success Metrics

### Throughput
- **Target:** > 100 events/second sustained
- **Measurement:** events_processed / time_elapsed

### Latency
- **Target P50:** < 30ms
- **Target P95:** < 100ms
- **Target P99:** < 200ms
- **Measurement:** t5_end - t0_created

### Reliability
- **Target:** > 99.9% success rate
- **Measurement:** (processed - errors) / processed * 100

### Data Integrity
- **Target:** 100% event matching
- **Measurement:** PostgreSQL event count = MongoDB document count

---

## Potential Issues & Mitigations

### Issue 1: Kafka Native vs Docker
**Problem:** Kafka running natively might have different bootstrap servers
**Solution:** 
- Make KAFKA_BOOTSTRAP_SERVERS configurable via environment
- Verify connectivity in setup.sh with `kafka-topics.sh --list`
- Provide clear error messages with connection details

### Issue 2: MongoDB Connection
**Problem:** Could be Atlas (cloud) or local with different URIs
**Solution:**
- Read MONGODB_URI from .env file
- Validate connection in setup.sh
- Show clear error message with example connection string

### Issue 3: Debezium Lag
**Problem:** Debezium might lag behind PostgreSQL WAL
**Solution:**
- Monitor Debezium connector metrics
- Wait for connector to catch up before starting load test
- Display Debezium lag separately in dashboard

### Issue 4: Consumer Overwhelm
**Problem:** 10,000 events might overwhelm single consumer instance
**Solution:**
- Use batch insertion with configurable delays
- Monitor Kafka consumer lag
- Show consumer lag metric in dashboard
- Consider reducing MAX_POLL_RECORDS for extreme loads

### Issue 5: Database Rate Limiting
**Problem:** PostgreSQL/MongoDB might rate-limit high insert rates
**Solution:**
- Implement batching with delays (100 events per batch, 50ms delay)
- Monitor database connection pools
- Show warnings if lag increases significantly

### Issue 6: Log Volume
**Problem:** 10,000 events = massive log output
**Solution:**
- Configurable log levels (DEBUG for 10, WARNING for 1000, ERROR for 10000)
- Dashboard aggregates instead of showing all events
- Write detailed metrics to file, show summaries in console

---

## Stakeholder Presentation Tips

### Visual Impact
1. **Color Coding:**
   - 🟢 Green: Success, healthy status
   - 🔴 Red: Errors, critical issues
   - 🟡 Yellow: Warnings, degraded performance
   - 🔵 Blue: Completion, informational

2. **Live Updates:**
   - Dashboard refreshes every 500ms
   - Progress bar shows real-time completion
   - Event counter increments visibly

3. **Narrative Flow:**
   - Start: "Setting up event processor demo..."
   - Running: "Processing 300+ events per second..."
   - Complete: "✅ Successfully processed 1,000 events in 3.2 seconds"

### Key Talking Points
- "Sub-30 millisecond average latency"
- "Processing over 300 events per second"
- "99.9% success rate with automatic error handling"
- "Complete data consistency across PostgreSQL, Kafka, and MongoDB"
- "Real-time event streaming with CDC pattern"

### Wow Factors
1. Open MongoDB Compass alongside terminal to show data appearing in real-time
2. Run comparison: "Watch how it handles 10 vs 1,000 vs 10,000 events"
3. Demonstrate resilience: "Even with errors, the system continues processing"
4. Show exact timing: "This event was created at 10:15:23.123 and appeared in MongoDB at 10:15:23.151 - just 28 milliseconds later"
5. Export results: "Here's a JSON report with detailed metrics for your analysis"

---

## Implementation Checklist

### Phase 1: Core Scripts (2 hours)
- [ ] Create `scripts/demo/` directory structure
- [ ] Implement `setup.sh` with service verification
- [ ] Implement `cleanup.sh` with safe data removal
- [ ] Create base `run_demo.sh` with parameter handling

### Phase 2: Event Generation (2 hours)
- [ ] Implement `event_generator.py` with faker integration
- [ ] Add UserCreated event generation
- [ ] Add ActivityCreated event generation
- [ ] Add ParticipantJoined event generation
- [ ] Test with 10, 100, 1000 event loads

### Phase 3: Consumer Enhancement (2 hours)
- [ ] Add latency tracking to `consumer.py`
- [ ] Implement `_append_metric_to_file()`
- [ ] Add periodic summary logging
- [ ] Create `EventMetrics` model
- [ ] Test with existing test suite (must stay at 74/74 passing)

### Phase 4: Monitoring & Dashboard (3 hours)
- [ ] Implement `metrics_collector.py`
- [ ] Implement `dashboard.py` with rich library
- [ ] Add real-time updates
- [ ] Add sparkline visualization
- [ ] Test dashboard refresh rates

### Phase 5: Verification (1 hour)
- [ ] Implement `mongodb_verifier.py`
- [ ] Add referential integrity checks
- [ ] Implement `latency_tracker.py`
- [ ] Create verification report generation

### Phase 6: Load Test Scripts (1 hour)
- [ ] Create `load_10.sh`
- [ ] Create `load_100.sh`
- [ ] Create `load_1000.sh`
- [ ] Create `load_10000.sh`
- [ ] Create `full_demo.sh` orchestration

### Phase 7: Documentation (1 hour)
- [ ] Create `scripts/demo/README.md`
- [ ] Add usage examples
- [ ] Document troubleshooting steps
- [ ] Add architecture diagrams

### Phase 8: Testing & Refinement (2 hours)
- [ ] Run full demo sequence
- [ ] Verify metrics accuracy
- [ ] Test error handling
- [ ] Optimize dashboard performance
- [ ] Create demo video/screenshots

**Total Estimated Time: 14 hours**

---

## Usage Examples

### Quick Demo (100 events)
```bash
cd /mnt/d/activity/event-processor
./scripts/demo/setup.sh
./scripts/demo/load_100.sh
```

### Full Showcase Demo
```bash
cd /mnt/d/activity/event-processor
./scripts/demo/full_demo.sh
```

### Monitor Existing Processing
```bash
./scripts/demo/monitor.sh
```

### Verify Results
```bash
./scripts/demo/verify.sh
```

### Custom Load Test
```bash
TARGET_EVENTS=5000 BATCH_SIZE=200 ./scripts/demo/run_demo.sh
```

---

## Expected Output Example

```
═══════════════════════════════════════════════════════════════════
           EVENT PROCESSOR DEMO - LIVE MONITORING                 
═══════════════════════════════════════════════════════════════════
Status: ● RUNNING          Uptime: 00:00:34                     
Target Events: 1,000       Processed: 847      Remaining: 153   
Progress: ████████████████░░░░ 84.7%                            
═══════════════════════════════════════════════════════════════════
THROUGHPUT                                                       
Current: 342 events/sec    Average: 289 events/sec              
Peak: 456 events/sec       Error Rate: 0.1%                     
═══════════════════════════════════════════════════════════════════
LATENCY (End-to-End)                                            
Average: 28.3ms    Min: 12ms    Max: 156ms                      
P50: 24ms          P95: 45ms    P99: 89ms                       
Sparkline: ▁▂▂▃▃▄▄▅▅▆▆▅▄▃▃▂▂▁                                  
═══════════════════════════════════════════════════════════════════
EVENT BREAKDOWN                                                  
UserCreated: 423     ActivityCreated: 234    Participant: 190   
═══════════════════════════════════════════════════════════════════
RECENT EVENTS (last 5)                                          
✓ UserCreated      alice_smith_892  12ms   [10:15:23]          
✓ ActivityCreated  Hiking Trip      18ms   [10:15:23]          
✓ ParticipantJoin  act_123         15ms   [10:15:24]          
✗ UserUpdated      FAILED          ERR    [10:15:24]          
✓ UserCreated      bob_jones_445   11ms   [10:15:24]          
═══════════════════════════════════════════════════════════════════

✅ Demo Complete! 1,000 events processed in 3.46 seconds
   Average Throughput: 289 events/second
   Average Latency: 28.3ms (P95: 45ms, P99: 89ms)
   Success Rate: 99.9%
   
📊 Detailed metrics saved to: demo_metrics_20241110_101527.json
```

---

## Next Steps

1. **Create scripts directory structure**
2. **Implement event generator** (start here - core functionality)
3. **Enhance consumer with latency tracking**
4. **Build dashboard visualization**
5. **Create load test orchestration scripts**
6. **Test with increasing loads**
7. **Refine and optimize based on results**
8. **Prepare demo presentation**

---

## Conclusion

This comprehensive demo strategy provides:

✅ **Real-time Visibility:** Live dashboard showing event processing  
✅ **Exact Measurements:** Millisecond-precision latency tracking  
✅ **Scalable Testing:** From 10 to 10,000 events  
✅ **Automated Execution:** Single command for complete demo  
✅ **Professional Presentation:** Stakeholder-friendly metrics and visualization  
✅ **Data Verification:** Comprehensive integrity checks  
✅ **Performance Analysis:** Detailed metrics and reporting  

The system is designed to impress stakeholders while providing rigorous technical validation of the event streaming architecture.
