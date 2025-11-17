"""
Tool Memory System - Tracks tool usage and learns from performance

Implements a learning system that:
1. Records every tool usage with metrics
2. Calculates success rates, latency, costs
3. Learns which tools work best for which patterns
4. Recommends tool retirement/replacement based on performance
5. Provides insights for future acquisition decisions
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ToolUsageRecord:
    """
    Single tool usage record.

    Attributes:
        tool_name: Name of the tool
        pattern_name: Pattern the tool addresses
        query: User query
        success: Whether execution succeeded
        latency_ms: Execution time in milliseconds
        cost: Estimated cost (API calls, etc.)
        score: Tool output score (0.0-1.0)
        error: Error message if failed
        timestamp: When the tool was used
    """
    tool_name: str
    pattern_name: str
    query: str
    success: bool
    latency_ms: float
    cost: float = 0.0
    score: float = 0.0
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ToolPerformanceMetrics:
    """
    Aggregated performance metrics for a tool.

    Attributes:
        tool_name: Name of the tool
        pattern_name: Pattern the tool addresses
        total_uses: Total number of uses
        success_rate: Percentage of successful executions
        avg_latency_ms: Average execution time
        total_cost: Total cost incurred
        avg_score: Average quality score
        last_used: Most recent usage timestamp
        recommendation: 'keep', 'monitor', or 'retire'
    """
    tool_name: str
    pattern_name: str
    total_uses: int
    success_rate: float
    avg_latency_ms: float
    total_cost: float
    avg_score: float
    last_used: datetime
    recommendation: str = 'keep'


class ToolMemorySystem:
    """
    Persistent memory system for tool usage tracking and learning.

    Uses SQLite to store usage history and provide analytics.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize tool memory system.

        Args:
            db_path: Path to SQLite database (default: data/tool_memory.db)
        """
        if db_path is None:
            project_root = self._find_project_root()
            db_path = project_root / "data" / "tool_memory.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _find_project_root(self) -> Path:
        """Find project root by locating pyproject.toml."""
        current = Path(__file__).resolve()
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current
            current = current.parent
        raise ValueError("Could not find project root")

    def _init_database(self):
        """Initialize SQLite database with schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    pattern_name TEXT NOT NULL,
                    query TEXT,
                    success INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    cost REAL DEFAULT 0.0,
                    score REAL DEFAULT 0.0,
                    error TEXT,
                    timestamp TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tool_pattern
                ON tool_usage(tool_name, pattern_name)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON tool_usage(timestamp)
            """)

            conn.commit()

    def record_usage(self, record: ToolUsageRecord):
        """
        Record a tool usage event.

        Args:
            record: ToolUsageRecord to store
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO tool_usage
                (tool_name, pattern_name, query, success, latency_ms, cost, score, error, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.tool_name,
                record.pattern_name,
                record.query,
                1 if record.success else 0,
                record.latency_ms,
                record.cost,
                record.score,
                record.error,
                record.timestamp.isoformat()
            ))
            conn.commit()

        logger.info(f"Recorded usage: {record.tool_name} (success={record.success}, latency={record.latency_ms:.0f}ms)")

    def get_tool_metrics(self, tool_name: str, pattern_name: str) -> Optional[ToolPerformanceMetrics]:
        """
        Get aggregated performance metrics for a tool.

        Args:
            tool_name: Name of the tool
            pattern_name: Pattern name

        Returns:
            ToolPerformanceMetrics or None if no data
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_uses,
                    AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                    AVG(latency_ms) as avg_latency,
                    SUM(cost) as total_cost,
                    AVG(score) as avg_score,
                    MAX(timestamp) as last_used
                FROM tool_usage
                WHERE tool_name = ? AND pattern_name = ?
            """, (tool_name, pattern_name))

            row = cursor.fetchone()

            if row[0] == 0:  # No usage records
                return None

            last_used = datetime.fromisoformat(row[5]) if row[5] else datetime.now()

            metrics = ToolPerformanceMetrics(
                tool_name=tool_name,
                pattern_name=pattern_name,
                total_uses=row[0],
                success_rate=row[1] * 100,  # Convert to percentage
                avg_latency_ms=row[2],
                total_cost=row[3],
                avg_score=row[4],
                last_used=last_used
            )

            # Determine recommendation
            metrics.recommendation = self._determine_recommendation(metrics)

            return metrics

    def get_best_tool_for_pattern(self, pattern_name: str) -> Optional[str]:
        """
        Get the best-performing tool for a given pattern.

        Args:
            pattern_name: Pattern to find best tool for

        Returns:
            Tool name or None if no tools found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    tool_name,
                    COUNT(*) as total_uses,
                    AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                    AVG(score) as avg_score,
                    AVG(latency_ms) as avg_latency
                FROM tool_usage
                WHERE pattern_name = ?
                GROUP BY tool_name
                HAVING total_uses >= 3
                ORDER BY
                    (success_rate * 0.5 + avg_score * 0.4 - (avg_latency / 10000) * 0.1) DESC
                LIMIT 1
            """, (pattern_name,))

            row = cursor.fetchone()

            if row:
                logger.info(f"Best tool for '{pattern_name}': {row[0]} (success={row[2]*100:.1f}%, score={row[3]:.2f})")
                return row[0]

            return None

    def get_all_tool_metrics(self) -> List[ToolPerformanceMetrics]:
        """
        Get metrics for all tools.

        Returns:
            List of ToolPerformanceMetrics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT tool_name, pattern_name
                FROM tool_usage
            """)

            metrics_list = []
            for row in cursor.fetchall():
                metrics = self.get_tool_metrics(row[0], row[1])
                if metrics:
                    metrics_list.append(metrics)

            return metrics_list

    def get_tools_to_retire(self, min_uses: int = 10) -> List[ToolPerformanceMetrics]:
        """
        Get tools that should be retired based on poor performance.

        Args:
            min_uses: Minimum uses before considering retirement

        Returns:
            List of ToolPerformanceMetrics for tools to retire
        """
        all_metrics = self.get_all_tool_metrics()

        retire_candidates = [
            m for m in all_metrics
            if m.total_uses >= min_uses and m.recommendation == 'retire'
        ]

        return retire_candidates

    def _determine_recommendation(self, metrics: ToolPerformanceMetrics) -> str:
        """
        Determine whether to keep, monitor, or retire a tool.

        Args:
            metrics: ToolPerformanceMetrics to evaluate

        Returns:
            'keep', 'monitor', or 'retire'
        """
        # Retire if: low success rate AND (low score OR not used recently)
        if metrics.success_rate < 50:
            if metrics.avg_score < 0.3 or self._days_since_last_use(metrics.last_used) > 30:
                return 'retire'

        # Monitor if: mediocre performance
        if metrics.success_rate < 70 or metrics.avg_score < 0.5:
            return 'monitor'

        # Keep if: good performance
        return 'keep'

    def _days_since_last_use(self, last_used: datetime) -> int:
        """Calculate days since last use."""
        return (datetime.now() - last_used).days

    def get_usage_trends(self, days: int = 30) -> Dict[str, List[Tuple[datetime, float]]]:
        """
        Get usage trends over time.

        Args:
            days: Number of days to analyze

        Returns:
            Dict mapping tool_name to list of (timestamp, success_rate) tuples
        """
        since = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT tool_name, timestamp, success
                FROM tool_usage
                WHERE timestamp >= ?
                ORDER BY timestamp
            """, (since.isoformat(),))

            trends = defaultdict(list)
            for row in cursor.fetchall():
                tool_name = row[0]
                timestamp = datetime.fromisoformat(row[1])
                success = row[2]
                trends[tool_name].append((timestamp, float(success)))

            return dict(trends)

    def get_cost_analysis(self) -> Dict[str, float]:
        """
        Get total costs by tool.

        Returns:
            Dict mapping tool_name to total cost
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT tool_name, SUM(cost) as total_cost
                FROM tool_usage
                GROUP BY tool_name
                ORDER BY total_cost DESC
            """)

            return {row[0]: row[1] for row in cursor.fetchall()}

    def export_metrics_to_json(self, output_path: Path):
        """
        Export all metrics to JSON file.

        Args:
            output_path: Path to save JSON file
        """
        metrics = self.get_all_tool_metrics()

        data = {
            'exported_at': datetime.now().isoformat(),
            'total_tools': len(metrics),
            'tools': [
                {
                    **asdict(m),
                    'last_used': m.last_used.isoformat()
                }
                for m in metrics
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported metrics to {output_path}")


# Example usage and testing
if __name__ == "__main__":
    print("Tool Memory System - Test Mode\n")

    # Initialize system
    memory = ToolMemorySystem()

    print("=" * 80)
    print("Test 1: Record Tool Usage")
    print("=" * 80)

    # Simulate tool usage
    tools_to_test = [
        ("ProductionReadiness", "Production Readiness", True, 500, 0.85),
        ("ProductionReadiness", "Production Readiness", True, 450, 0.82),
        ("ProductionReadiness", "Production Readiness", False, 2000, 0.0),
        ("EmailValidator", "Email Validation", True, 150, 0.92),
        ("EmailValidator", "Email Validation", True, 140, 0.95),
        ("JSONSchemaValidator", "JSON Schema Validation", True, 200, 0.88),
        ("JSONSchemaValidator", "JSON Schema Validation", True, 180, 0.90),
        ("JSONSchemaValidator", "JSON Schema Validation", True, 190, 0.89),
    ]

    for tool_name, pattern, success, latency, score in tools_to_test:
        record = ToolUsageRecord(
            tool_name=tool_name,
            pattern_name=pattern,
            query="test query",
            success=success,
            latency_ms=latency,
            score=score,
            cost=0.01 if "API" in tool_name else 0.0
        )
        memory.record_usage(record)

    print(f"\n✓ Recorded {len(tools_to_test)} tool usages")

    # Test 2: Get metrics
    print("\n" + "=" * 80)
    print("Test 2: Tool Performance Metrics")
    print("=" * 80)

    all_metrics = memory.get_all_tool_metrics()

    for metrics in all_metrics:
        print(f"\n{metrics.tool_name} ({metrics.pattern_name})")
        print(f"  Uses: {metrics.total_uses}")
        print(f"  Success Rate: {metrics.success_rate:.1f}%")
        print(f"  Avg Latency: {metrics.avg_latency_ms:.0f}ms")
        print(f"  Avg Score: {metrics.avg_score:.2f}")
        print(f"  Total Cost: ${metrics.total_cost:.2f}")
        print(f"  Recommendation: {metrics.recommendation.upper()}")

    # Test 3: Get best tool
    print("\n" + "=" * 80)
    print("Test 3: Best Tool for Pattern")
    print("=" * 80)

    best = memory.get_best_tool_for_pattern("Production Readiness")
    print(f"\nBest tool for Production Readiness: {best}")

    # Test 4: Cost analysis
    print("\n" + "=" * 80)
    print("Test 4: Cost Analysis")
    print("=" * 80)

    costs = memory.get_cost_analysis()
    print("\nTotal costs by tool:")
    for tool, cost in costs.items():
        print(f"  {tool}: ${cost:.2f}")

    # Test 5: Tools to retire
    print("\n" + "=" * 80)
    print("Test 5: Tools to Retire")
    print("=" * 80)

    retire = memory.get_tools_to_retire(min_uses=2)
    if retire:
        print("\nTools recommended for retirement:")
        for m in retire:
            print(f"  - {m.tool_name}: {m.success_rate:.1f}% success, score={m.avg_score:.2f}")
    else:
        print("\nNo tools recommended for retirement")

    print("\n" + "=" * 80)
