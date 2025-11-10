"""
Terminal Dashboard - Real-time Event Processing Visualization
Beautiful terminal UI using Rich library for live demo monitoring
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text
from rich import box


class Dashboard:
    """
    Real-time terminal dashboard for event processing demo

    Features:
    - Live updating status display
    - Throughput metrics
    - Latency statistics with sparklines
    - Event breakdown by type
    - Recent events log
    - Progress tracking
    """

    def __init__(self, target_events: int):
        self.console = Console()
        self.target_events = target_events
        self.start_time = time.time()

        # Metrics
        self.processed = 0
        self.errors = 0
        self.event_types: Dict[str, int] = {}
        self.latencies: List[float] = []
        self.recent_events: List[Dict[str, Any]] = []
        self.max_recent = 5

        # Throughput tracking
        self.throughput_samples: List[float] = []
        self.peak_throughput = 0.0
        self.last_update = time.time()
        self.last_processed = 0

    def update(
        self,
        event_type: str,
        latency_ms: float,
        success: bool = True,
        event_details: Optional[str] = None
    ):
        """Update dashboard with new event"""
        self.processed += 1

        if not success:
            self.errors += 1

        # Track event types
        self.event_types[event_type] = self.event_types.get(event_type, 0) + 1

        # Track latency
        if latency_ms is not None:
            self.latencies.append(latency_ms)

        # Track recent events
        self.recent_events.append({
            "type": event_type,
            "latency": latency_ms,
            "success": success,
            "details": event_details or "",
            "time": datetime.now().strftime("%H:%M:%S")
        })

        # Keep only recent N
        if len(self.recent_events) > self.max_recent:
            self.recent_events.pop(0)

        # Update throughput
        now = time.time()
        if now - self.last_update >= 1.0:  # Update every second
            events_delta = self.processed - self.last_processed
            time_delta = now - self.last_update
            current_throughput = events_delta / time_delta

            self.throughput_samples.append(current_throughput)
            if len(self.throughput_samples) > 60:  # Keep last 60 seconds
                self.throughput_samples.pop(0)

            self.peak_throughput = max(self.peak_throughput, current_throughput)
            self.last_update = now
            self.last_processed = self.processed

    def _get_status_text(self) -> str:
        """Get status indicator"""
        if self.processed >= self.target_events:
            return "[bold green]● COMPLETE[/]"
        elif self.processed > 0:
            return "[bold yellow]● RUNNING[/]"
        else:
            return "[bold blue]● STARTING[/]"

    def _get_uptime(self) -> str:
        """Get formatted uptime"""
        elapsed = time.time() - self.start_time
        return str(timedelta(seconds=int(elapsed)))

    def _get_progress_percentage(self) -> float:
        """Get progress as percentage"""
        if self.target_events == 0:
            return 0.0
        return (self.processed / self.target_events) * 100

    def _make_progress_bar(self, percentage: float, width: int = 40) -> str:
        """Create ASCII progress bar"""
        filled = int((percentage / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"{bar} {percentage:.1f}%"

    def _get_current_throughput(self) -> float:
        """Get current throughput (events/sec)"""
        if not self.throughput_samples:
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                return self.processed / elapsed
            return 0.0
        return self.throughput_samples[-1] if self.throughput_samples else 0.0

    def _get_average_throughput(self) -> float:
        """Get average throughput (events/sec)"""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            return self.processed / elapsed
        return 0.0

    def _get_latency_stats(self) -> Dict[str, float]:
        """Calculate latency statistics"""
        if not self.latencies:
            return {"avg": 0, "min": 0, "max": 0, "p50": 0, "p95": 0, "p99": 0}

        sorted_lat = sorted(self.latencies)
        count = len(sorted_lat)

        return {
            "avg": sum(sorted_lat) / count,
            "min": sorted_lat[0],
            "max": sorted_lat[-1],
            "p50": sorted_lat[int(count * 0.50)],
            "p95": sorted_lat[int(count * 0.95)] if count > 20 else sorted_lat[-1],
            "p99": sorted_lat[int(count * 0.99)] if count > 100 else sorted_lat[-1]
        }

    def _make_sparkline(self, values: List[float], width: int = 20) -> str:
        """Create ASCII sparkline from values"""
        if not values:
            return "▁" * width

        # Take last N values
        values = values[-width:]

        if len(values) < width:
            values = [0] * (width - len(values)) + values

        min_val = min(values) if values else 0
        max_val = max(values) if values else 1
        range_val = max_val - min_val if max_val > min_val else 1

        chars = "▁▂▃▄▅▆▇█"
        sparkline = ""

        for val in values:
            normalized = (val - min_val) / range_val
            index = min(int(normalized * len(chars)), len(chars) - 1)
            sparkline += chars[index]

        return sparkline

    def _create_header_panel(self) -> Panel:
        """Create header panel with status and progress"""
        remaining = self.target_events - self.processed
        progress_pct = self._get_progress_percentage()

        header = Table.grid(padding=1)
        header.add_column(justify="left")
        header.add_column(justify="right")

        header.add_row(
            f"Status: {self._get_status_text()}",
            f"Uptime: [cyan]{self._get_uptime()}[/]"
        )
        header.add_row(
            f"Target Events: [bold]{self.target_events:,}[/]",
            f"Processed: [bold green]{self.processed:,}[/]"
        )
        header.add_row(
            f"Progress: {self._make_progress_bar(progress_pct)}",
            f"Remaining: [yellow]{remaining:,}[/]"
        )

        return Panel(header, title="[bold]EVENT PROCESSOR DEMO - LIVE MONITORING[/]", border_style="blue")

    def _create_throughput_panel(self) -> Panel:
        """Create throughput metrics panel"""
        current = self._get_current_throughput()
        average = self._get_average_throughput()
        error_rate = (self.errors / self.processed * 100) if self.processed > 0 else 0

        content = Table.grid(padding=1)
        content.add_column(justify="left")
        content.add_column(justify="right")

        content.add_row(
            "Current:",
            f"[bold cyan]{current:.1f}[/] events/sec"
        )
        content.add_row(
            "Average:",
            f"[bold]{average:.1f}[/] events/sec"
        )
        content.add_row(
            "Peak:",
            f"[bold green]{self.peak_throughput:.1f}[/] events/sec"
        )
        content.add_row(
            "Error Rate:",
            f"[bold {'red' if error_rate > 1 else 'green'}]{error_rate:.1f}%[/]"
        )

        return Panel(content, title="THROUGHPUT", border_style="green")

    def _create_latency_panel(self) -> Panel:
        """Create latency statistics panel"""
        stats = self._get_latency_stats()

        content = Table.grid(padding=1)
        content.add_column(justify="left", width=10)
        content.add_column(justify="right")

        content.add_row("Average:", f"[bold]{stats['avg']:.1f}ms[/]")
        content.add_row("Min:", f"{stats['min']:.1f}ms")
        content.add_row("Max:", f"{stats['max']:.1f}ms")
        content.add_row("P50:", f"[cyan]{stats['p50']:.1f}ms[/]")
        content.add_row("P95:", f"[yellow]{stats['p95']:.1f}ms[/]")
        content.add_row("P99:", f"[red]{stats['p99']:.1f}ms[/]")

        # Add sparkline if we have data
        if self.latencies:
            sparkline = self._make_sparkline(self.latencies[-40:], width=25)
            content.add_row("", "")
            content.add_row("Trend:", f"[dim]{sparkline}[/]")

        return Panel(content, title="LATENCY (End-to-End)", border_style="yellow")

    def _create_events_panel(self) -> Panel:
        """Create event breakdown panel"""
        content = Table.grid(padding=1)
        content.add_column(justify="left")
        content.add_column(justify="right")

        # Sort by count descending
        sorted_events = sorted(self.event_types.items(), key=lambda x: x[1], reverse=True)

        for event_type, count in sorted_events:
            percentage = (count / self.processed * 100) if self.processed > 0 else 0
            content.add_row(
                f"{event_type}:",
                f"[bold]{count}[/] ({percentage:.1f}%)"
            )

        if not sorted_events:
            content.add_row("[dim]No events yet...[/]", "")

        return Panel(content, title="EVENT BREAKDOWN", border_style="magenta")

    def _create_recent_panel(self) -> Panel:
        """Create recent events panel"""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Type", style="cyan")
        table.add_column("Details", style="dim")
        table.add_column("Latency", justify="right")
        table.add_column("Time", justify="right", style="dim")

        for event in reversed(self.recent_events):  # Most recent first
            status = "✓" if event["success"] else "✗"
            color = "green" if event["success"] else "red"
            latency_str = f"{event['latency']:.0f}ms" if event['latency'] else "N/A"

            table.add_row(
                f"[{color}]{status}[/] {event['type']}",
                event['details'][:20] if event['details'] else "",
                latency_str,
                f"[{event['time']}]"
            )

        if not self.recent_events:
            table.add_row("[dim]Waiting for events...[/]", "", "", "")

        return Panel(table, title="RECENT EVENTS (last 5)", border_style="blue")

    def create_layout(self) -> Layout:
        """Create complete dashboard layout"""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=7),
            Layout(name="metrics", size=12),
            Layout(name="events", size=10)
        )

        layout["metrics"].split_row(
            Layout(name="throughput"),
            Layout(name="latency")
        )

        layout["events"].split_row(
            Layout(name="breakdown"),
            Layout(name="recent")
        )

        # Update all panels
        layout["header"].update(self._create_header_panel())
        layout["throughput"].update(self._create_throughput_panel())
        layout["latency"].update(self._create_latency_panel())
        layout["breakdown"].update(self._create_events_panel())
        layout["recent"].update(self._create_recent_panel())

        return layout

    def run_live(self, refresh_rate: float = 0.5):
        """
        Run dashboard in live mode (for use with Live context manager)

        Args:
            refresh_rate: Refresh interval in seconds
        """
        with Live(self.create_layout(), console=self.console, refresh_per_second=int(1/refresh_rate)) as live:
            while self.processed < self.target_events:
                time.sleep(refresh_rate)
                live.update(self.create_layout())

    def render_once(self):
        """Render dashboard once (for manual updates)"""
        self.console.clear()
        self.console.print(self.create_layout())


def main():
    """Example usage"""
    import random

    dashboard = Dashboard(target_events=100)

    # Simulate some events
    event_types = ["UserCreated", "ActivityCreated", "ParticipantJoined"]

    print("Starting demo dashboard...")
    time.sleep(1)

    for i in range(100):
        event_type = random.choice(event_types)
        latency = random.uniform(10, 100)
        success = random.random() > 0.02  # 2% error rate

        dashboard.update(
            event_type=event_type,
            latency_ms=latency,
            success=success,
            event_details=f"event_{i}"
        )

        dashboard.render_once()
        time.sleep(0.1)  # Simulate processing time

    print("\n✓ Demo complete!")


if __name__ == "__main__":
    main()
