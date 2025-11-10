"""
Metrics Collector - Real-time Performance Metrics Aggregation
Collects and aggregates metrics from the event processing pipeline
"""

import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import defaultdict
import statistics


class MetricsCollector:
    """
    Collect and aggregate event processing metrics in real-time

    Features:
    - Track throughput (events/second)
    - Calculate latency statistics (min/max/avg/p50/p95/p99)
    - Monitor error rates
    - Event type breakdown
    - Export to JSON for analysis
    """

    def __init__(self, metrics_file: str = "demo_metrics.json"):
        self.metrics_file = Path(metrics_file)
        self.start_time = datetime.now(timezone.utc)

        # Metrics storage
        self.events: List[Dict[str, Any]] = []
        self.total_processed = 0
        self.total_errors = 0

        # Event type counters
        self.event_type_counts: Dict[str, int] = defaultdict(int)

        # Latency tracking
        self.latencies: List[float] = []

        # Recent events (for display)
        self.recent_events: List[Dict[str, Any]] = []
        self.max_recent = 10

    def record_event(self, metrics: Dict[str, Any]):
        """
        Record a single event's metrics

        Args:
            metrics: Dictionary containing event metrics
                Required keys: event_id, event_type, total_latency
                Optional keys: success, error_message, all timing info
        """
        self.events.append(metrics)
        self.total_processed += 1

        # Track by event type
        event_type = metrics.get("event_type", "Unknown")
        self.event_type_counts[event_type] += 1

        # Track latency
        if "total_latency" in metrics and metrics["total_latency"] is not None:
            self.latencies.append(metrics["total_latency"])

        # Track errors
        if not metrics.get("success", True):
            self.total_errors += 1

        # Keep recent events
        self.recent_events.append({
            "event_type": event_type,
            "event_id": str(metrics.get("event_id", ""))[:8],
            "latency_ms": metrics.get("total_latency"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": metrics.get("success", True)
        })

        # Keep only last N events
        if len(self.recent_events) > self.max_recent:
            self.recent_events.pop(0)

    def get_throughput(self) -> float:
        """Calculate current throughput in events/second"""
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        if elapsed == 0:
            return 0.0
        return self.total_processed / elapsed

    def get_latency_stats(self) -> Dict[str, float]:
        """
        Calculate latency statistics

        Returns:
            Dictionary with min, max, avg, p50, p95, p99 latencies in milliseconds
        """
        if not self.latencies:
            return {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "count": 0
            }

        sorted_latencies = sorted(self.latencies)
        count = len(sorted_latencies)

        return {
            "min": round(sorted_latencies[0], 2),
            "max": round(sorted_latencies[-1], 2),
            "avg": round(statistics.mean(sorted_latencies), 2),
            "p50": round(sorted_latencies[int(count * 0.50)], 2),
            "p95": round(sorted_latencies[int(count * 0.95)], 2) if count > 20 else round(sorted_latencies[-1], 2),
            "p99": round(sorted_latencies[int(count * 0.99)], 2) if count > 100 else round(sorted_latencies[-1], 2),
            "count": count
        }

    def get_error_rate(self) -> float:
        """Calculate error rate as percentage"""
        if self.total_processed == 0:
            return 0.0
        return (self.total_errors / self.total_processed) * 100

    def get_success_rate(self) -> float:
        """Calculate success rate as percentage"""
        return 100.0 - self.get_error_rate()

    def get_event_breakdown(self) -> Dict[str, int]:
        """Get event count by type"""
        return dict(self.event_type_counts)

    def get_recent_events(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get the N most recent events"""
        return self.recent_events[-count:]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get complete metrics summary

        Returns:
            Dictionary with all metrics
        """
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration": {
                "start_time": self.start_time.isoformat(),
                "elapsed_seconds": round(elapsed, 2),
                "elapsed_formatted": self._format_duration(elapsed)
            },
            "totals": {
                "events_processed": self.total_processed,
                "errors": self.total_errors,
                "success_rate": round(self.get_success_rate(), 2)
            },
            "throughput": {
                "events_per_second": round(self.get_throughput(), 2),
                "events_per_minute": round(self.get_throughput() * 60, 2)
            },
            "latency": self.get_latency_stats(),
            "event_breakdown": self.get_event_breakdown(),
            "recent_events": self.get_recent_events(10)
        }

    def export_to_json(self, include_raw_events: bool = False):
        """
        Export metrics to JSON file

        Args:
            include_raw_events: If True, includes all raw event data
        """
        summary = self.get_summary()

        if include_raw_events:
            summary["raw_events"] = self.events

        with open(self.metrics_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"✓ Metrics exported to {self.metrics_file}")

    def print_summary(self):
        """Print human-readable summary to console"""
        summary = self.get_summary()
        latency = summary["latency"]
        totals = summary["totals"]
        throughput = summary["throughput"]

        print("\n" + "=" * 70)
        print("METRICS SUMMARY")
        print("=" * 70)

        print(f"\nDuration: {summary['duration']['elapsed_formatted']}")
        print(f"Total Events: {totals['events_processed']}")
        print(f"Success Rate: {totals['success_rate']:.2f}%")
        print(f"Errors: {totals['errors']}")

        print(f"\nThroughput:")
        print(f"  {throughput['events_per_second']:.2f} events/second")
        print(f"  {throughput['events_per_minute']:.2f} events/minute")

        print(f"\nLatency Statistics ({latency['count']} samples):")
        print(f"  Min: {latency['min']:.2f}ms")
        print(f"  Avg: {latency['avg']:.2f}ms")
        print(f"  Max: {latency['max']:.2f}ms")
        print(f"  P50: {latency['p50']:.2f}ms")
        print(f"  P95: {latency['p95']:.2f}ms")
        print(f"  P99: {latency['p99']:.2f}ms")

        breakdown = summary["event_breakdown"]
        if breakdown:
            print(f"\nEvent Breakdown:")
            for event_type, count in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / totals['events_processed']) * 100
                print(f"  {event_type}: {count} ({percentage:.1f}%)")

        print("\n" + "=" * 70)

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def reset(self):
        """Reset all metrics (for new test run)"""
        self.events.clear()
        self.total_processed = 0
        self.total_errors = 0
        self.event_type_counts.clear()
        self.latencies.clear()
        self.recent_events.clear()
        self.start_time = datetime.now(timezone.utc)


def main():
    """Example usage"""
    import random

    collector = MetricsCollector("example_metrics.json")

    # Simulate some events
    print("Simulating 100 events...")
    for i in range(100):
        collector.record_event({
            "event_id": f"event-{i}",
            "event_type": random.choice(["UserCreated", "ActivityCreated", "ParticipantJoined"]),
            "total_latency": random.uniform(10, 100),
            "success": random.random() > 0.01  # 1% error rate
        })

    # Print summary
    collector.print_summary()

    # Export to JSON
    collector.export_to_json()


if __name__ == "__main__":
    main()
