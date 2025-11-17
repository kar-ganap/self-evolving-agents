"""
Comprehensive Tests for Tool Memory System

Tests all functionality:
1. Database initialization and schema
2. Usage recording
3. Performance metrics calculation
4. Best tool selection algorithm
5. Tool retirement recommendations
6. Cost analysis and analytics
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from src.level2.walk.tool_memory_system import (
    ToolMemorySystem,
    ToolUsageRecord,
    ToolPerformanceMetrics
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test_tool_memory.db"

    yield db_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def memory_system(temp_db):
    """Create a fresh ToolMemorySystem for each test"""
    return ToolMemorySystem(db_path=temp_db)


class TestDatabaseInitialization:
    """Test database setup and schema"""

    def test_database_creation(self, temp_db):
        """Test that database file is created"""
        assert not temp_db.exists(), "DB should not exist initially"

        memory = ToolMemorySystem(db_path=temp_db)

        assert temp_db.exists(), "DB file should be created"
        assert temp_db.stat().st_size > 0, "DB should not be empty"

    def test_schema_tables(self, memory_system):
        """Test that required tables are created"""
        import sqlite3

        with sqlite3.connect(memory_system.db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]

        assert 'tool_usage' in tables, "tool_usage table should exist"

    def test_schema_indexes(self, memory_system):
        """Test that indexes are created"""
        import sqlite3

        with sqlite3.connect(memory_system.db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = [row[0] for row in cursor.fetchall()]

        assert any('tool_pattern' in idx for idx in indexes), \
            "Tool-pattern index should exist"
        assert any('timestamp' in idx for idx in indexes), \
            "Timestamp index should exist"


class TestUsageRecording:
    """Test recording tool usage events"""

    def test_record_single_usage(self, memory_system):
        """Test recording a single usage event"""
        record = ToolUsageRecord(
            tool_name="TestTool",
            pattern_name="Test Pattern",
            query="test query",
            success=True,
            latency_ms=250.0,
            cost=0.01,
            score=0.85
        )

        memory_system.record_usage(record)

        # Verify record was saved
        metrics = memory_system.get_tool_metrics("TestTool", "Test Pattern")

        assert metrics is not None, "Should have metrics for recorded tool"
        assert metrics.total_uses == 1, "Should have 1 usage"
        assert metrics.success_rate == 100.0, "Should be 100% success"

    def test_record_multiple_usages(self, memory_system):
        """Test recording multiple usage events"""
        for i in range(5):
            record = ToolUsageRecord(
                tool_name="MultiTool",
                pattern_name="Test Pattern",
                query=f"query {i}",
                success=True,
                latency_ms=100.0 + i * 10,
                cost=0.01,
                score=0.8 + i * 0.02
            )
            memory_system.record_usage(record)

        metrics = memory_system.get_tool_metrics("MultiTool", "Test Pattern")

        assert metrics.total_uses == 5, "Should have 5 usages"
        assert metrics.success_rate == 100.0, "Should be 100% success"
        assert 100 < metrics.avg_latency_ms < 150, "Avg latency should be in range"

    def test_record_failed_usage(self, memory_system):
        """Test recording failed usages"""
        # 2 successes, 3 failures
        for i in range(5):
            record = ToolUsageRecord(
                tool_name="FailTool",
                pattern_name="Test Pattern",
                query=f"query {i}",
                success=(i < 2),  # First 2 succeed, rest fail
                latency_ms=200.0,
                score=0.8 if i < 2 else 0.0,
                error=None if i < 2 else "Test error"
            )
            memory_system.record_usage(record)

        metrics = memory_system.get_tool_metrics("FailTool", "Test Pattern")

        assert metrics.total_uses == 5
        assert metrics.success_rate == 40.0, "Should be 40% success (2/5)"

    def test_timestamp_auto_generation(self, memory_system):
        """Test that timestamp is automatically set"""
        record = ToolUsageRecord(
            tool_name="TimestampTool",
            pattern_name="Test Pattern",
            query="test",
            success=True,
            latency_ms=100.0
        )
        # Don't set timestamp - should auto-generate

        memory_system.record_usage(record)
        metrics = memory_system.get_tool_metrics("TimestampTool", "Test Pattern")

        assert metrics.last_used is not None
        # Should be within last minute
        assert (datetime.now() - metrics.last_used).total_seconds() < 60


class TestPerformanceMetrics:
    """Test performance metrics calculation"""

    def test_metrics_calculation(self, memory_system):
        """Test that metrics are calculated correctly"""
        # Record 10 usages with varying performance
        for i in range(10):
            record = ToolUsageRecord(
                tool_name="MetricsTool",
                pattern_name="Test Pattern",
                query=f"query {i}",
                success=(i % 2 == 0),  # 50% success
                latency_ms=100.0 + i * 20,  # Increasing latency
                cost=0.01 + i * 0.001,  # Increasing cost
                score=0.5 + i * 0.05  # Increasing score
            )
            memory_system.record_usage(record)

        metrics = memory_system.get_tool_metrics("MetricsTool", "Test Pattern")

        assert metrics.total_uses == 10
        assert metrics.success_rate == 50.0, "Should be 50% success"
        assert 100 <= metrics.avg_latency_ms <= 300, "Avg latency should be in range"
        assert metrics.total_cost > 0, "Should have accumulated cost"
        assert 0 < metrics.avg_score < 1, "Avg score should be in range"

    def test_no_metrics_for_nonexistent_tool(self, memory_system):
        """Test that non-existent tool returns None"""
        metrics = memory_system.get_tool_metrics("NonExistent", "Test Pattern")
        assert metrics is None, "Non-existent tool should return None"

    def test_separate_metrics_per_pattern(self, memory_system):
        """Test that metrics are separated by pattern"""
        # Same tool, different patterns
        for pattern in ["Pattern A", "Pattern B"]:
            for i in range(3):
                record = ToolUsageRecord(
                    tool_name="SameTool",
                    pattern_name=pattern,
                    query="test",
                    success=True,
                    latency_ms=100.0,
                    score=0.8
                )
                memory_system.record_usage(record)

        metrics_a = memory_system.get_tool_metrics("SameTool", "Pattern A")
        metrics_b = memory_system.get_tool_metrics("SameTool", "Pattern B")

        assert metrics_a.total_uses == 3
        assert metrics_b.total_uses == 3
        assert metrics_a.pattern_name == "Pattern A"
        assert metrics_b.pattern_name == "Pattern B"


class TestBestToolSelection:
    """Test learning algorithm for best tool selection"""

    def test_best_tool_selection(self, memory_system):
        """Test that best tool is selected correctly"""
        # Create 3 tools with different performance profiles
        tools = [
            ("ToolA", 10, 0.9, 0.85, 100),  # High success, high score, fast
            ("ToolB", 10, 0.6, 0.9, 150),   # Medium success, high score, medium
            ("ToolC", 10, 0.5, 0.6, 80),    # Low success, medium score, fast
        ]

        for tool_name, uses, success_rate, score, latency in tools:
            for i in range(uses):
                record = ToolUsageRecord(
                    tool_name=tool_name,
                    pattern_name="Common Pattern",
                    query=f"test {i}",
                    success=(i < uses * success_rate),
                    latency_ms=latency,
                    score=score if i < uses * success_rate else 0.0
                )
                memory_system.record_usage(record)

        best_tool = memory_system.get_best_tool_for_pattern("Common Pattern")

        # ToolA should win (high success, high score, good latency)
        assert best_tool == "ToolA", \
            "ToolA should be selected as best (success=0.9, score=0.85)"

    def test_minimum_uses_threshold(self, memory_system):
        """Test that tools need minimum uses to be considered"""
        # Tool with only 2 uses (below threshold of 3)
        for i in range(2):
            record = ToolUsageRecord(
                tool_name="NewTool",
                pattern_name="Test Pattern",
                query=f"test {i}",
                success=True,
                latency_ms=50,
                score=1.0
            )
            memory_system.record_usage(record)

        best_tool = memory_system.get_best_tool_for_pattern("Test Pattern")

        assert best_tool is None, \
            "Tools with < 3 uses should not be recommended"

    def test_no_tools_returns_none(self, memory_system):
        """Test that non-existent pattern returns None"""
        best_tool = memory_system.get_best_tool_for_pattern("NonExistent Pattern")
        assert best_tool is None


class TestToolRetirement:
    """Test tool retirement recommendations"""

    def test_retire_low_success_rate(self, memory_system):
        """Test retirement of tools with low success rate"""
        # Tool with 30% success rate and low score
        for i in range(15):
            record = ToolUsageRecord(
                tool_name="BadTool",
                pattern_name="Test Pattern",
                query=f"test {i}",
                success=(i < 5),  # 5/15 = 33% success
                latency_ms=200,
                score=0.2 if i < 5 else 0.0
            )
            memory_system.record_usage(record)

        metrics = memory_system.get_tool_metrics("BadTool", "Test Pattern")

        assert metrics.success_rate < 50, "Should have low success rate"
        assert metrics.recommendation == 'retire', \
            "Low success + low score should trigger retirement"

    def test_retire_unused_tool(self, memory_system):
        """Test retirement of tools not used recently"""
        # Tool with poor success and old timestamp
        old_timestamp = datetime.now() - timedelta(days=35)

        for i in range(12):
            record = ToolUsageRecord(
                tool_name="OldTool",
                pattern_name="Test Pattern",
                query=f"test {i}",
                success=(i < 5),  # 42% success
                latency_ms=200,
                score=0.3,
                timestamp=old_timestamp
            )
            memory_system.record_usage(record)

        metrics = memory_system.get_tool_metrics("OldTool", "Test Pattern")

        assert metrics.success_rate < 50
        assert (datetime.now() - metrics.last_used).days > 30
        assert metrics.recommendation == 'retire', \
            "Old + low success should trigger retirement"

    def test_monitor_mediocre_tool(self, memory_system):
        """Test monitoring recommendation for mediocre tools"""
        # Tool with 65% success (below 70% threshold)
        for i in range(20):
            record = ToolUsageRecord(
                tool_name="MediocreTool",
                pattern_name="Test Pattern",
                query=f"test {i}",
                success=(i < 13),  # 13/20 = 65% success
                latency_ms=150,
                score=0.6
            )
            memory_system.record_usage(record)

        metrics = memory_system.get_tool_metrics("MediocreTool", "Test Pattern")

        assert metrics.success_rate == 65.0
        assert metrics.recommendation == 'monitor', \
            "Mediocre performance should trigger monitoring"

    def test_keep_good_tool(self, memory_system):
        """Test keeping recommendation for good tools"""
        # Tool with 85% success and good score
        for i in range(20):
            record = ToolUsageRecord(
                tool_name="GoodTool",
                pattern_name="Test Pattern",
                query=f"test {i}",
                success=(i < 17),  # 17/20 = 85% success
                latency_ms=100,
                score=0.8 if i < 17 else 0.0
            )
            memory_system.record_usage(record)

        metrics = memory_system.get_tool_metrics("GoodTool", "Test Pattern")

        assert metrics.success_rate == 85.0
        assert metrics.avg_score > 0.5
        assert metrics.recommendation == 'keep', \
            "Good performance should be kept"

    def test_get_tools_to_retire(self, memory_system):
        """Test getting list of tools to retire"""
        # Create 3 tools: 1 good, 1 mediocre, 1 bad
        tools = [
            ("GoodTool", 15, 0.9, 0.85),     # Keep
            ("MediocreTool", 15, 0.65, 0.6), # Monitor
            ("BadTool", 15, 0.3, 0.2),       # Retire
        ]

        for tool_name, uses, success_rate, score in tools:
            for i in range(uses):
                record = ToolUsageRecord(
                    tool_name=tool_name,
                    pattern_name="Test Pattern",
                    query=f"test {i}",
                    success=(i < uses * success_rate),
                    latency_ms=150,
                    score=score if i < uses * success_rate else 0.0
                )
                memory_system.record_usage(record)

        retire_candidates = memory_system.get_tools_to_retire(min_uses=10)

        assert len(retire_candidates) == 1, "Should have 1 retirement candidate"
        assert retire_candidates[0].tool_name == "BadTool"


class TestAnalytics:
    """Test analytics and reporting features"""

    def test_cost_analysis(self, memory_system):
        """Test cost analysis by tool"""
        # Create tools with different costs
        tools = [
            ("ExpensiveTool", 10, 0.05),   # $0.50 total
            ("CheapTool", 10, 0.01),       # $0.10 total
            ("FreeTool", 10, 0.0),         # $0.00 total
        ]

        for tool_name, uses, cost_per_use in tools:
            for i in range(uses):
                record = ToolUsageRecord(
                    tool_name=tool_name,
                    pattern_name="Test Pattern",
                    query=f"test {i}",
                    success=True,
                    latency_ms=100,
                    cost=cost_per_use
                )
                memory_system.record_usage(record)

        cost_analysis = memory_system.get_cost_analysis()

        assert len(cost_analysis) == 3
        assert cost_analysis["ExpensiveTool"] == pytest.approx(0.50, rel=0.01)
        assert cost_analysis["CheapTool"] == pytest.approx(0.10, rel=0.01)
        assert cost_analysis["FreeTool"] == 0.0

    def test_usage_trends(self, memory_system):
        """Test usage trends over time"""
        # Record usages over time
        base_time = datetime.now() - timedelta(days=7)

        for day in range(7):
            timestamp = base_time + timedelta(days=day)
            for i in range(3):
                record = ToolUsageRecord(
                    tool_name="TrendTool",
                    pattern_name="Test Pattern",
                    query=f"test {day}-{i}",
                    success=(day > 3),  # Improve over time
                    latency_ms=100,
                    timestamp=timestamp
                )
                memory_system.record_usage(record)

        trends = memory_system.get_usage_trends(days=10)

        assert "TrendTool" in trends
        assert len(trends["TrendTool"]) == 21  # 7 days * 3 usages

    def test_get_all_tool_metrics(self, memory_system):
        """Test getting metrics for all tools"""
        # Create 3 different tools
        for tool_num in range(3):
            for i in range(5):
                record = ToolUsageRecord(
                    tool_name=f"Tool{tool_num}",
                    pattern_name="Test Pattern",
                    query=f"test {i}",
                    success=True,
                    latency_ms=100
                )
                memory_system.record_usage(record)

        all_metrics = memory_system.get_all_tool_metrics()

        assert len(all_metrics) == 3
        tool_names = {m.tool_name for m in all_metrics}
        assert tool_names == {"Tool0", "Tool1", "Tool2"}

    def test_export_metrics_to_json(self, memory_system, temp_db):
        """Test exporting metrics to JSON"""
        # Record some usage
        for i in range(5):
            record = ToolUsageRecord(
                tool_name="ExportTool",
                pattern_name="Test Pattern",
                query=f"test {i}",
                success=True,
                latency_ms=100,
                score=0.8
            )
            memory_system.record_usage(record)

        output_path = temp_db.parent / "metrics_export.json"
        memory_system.export_metrics_to_json(output_path)

        assert output_path.exists(), "Export file should be created"

        # Verify JSON structure
        import json
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'exported_at' in data
        assert 'total_tools' in data
        assert 'tools' in data
        assert len(data['tools']) > 0
        assert data['tools'][0]['tool_name'] == 'ExportTool'


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_database(self, memory_system):
        """Test operations on empty database"""
        metrics = memory_system.get_tool_metrics("Any", "Any")
        assert metrics is None

        best_tool = memory_system.get_best_tool_for_pattern("Any")
        assert best_tool is None

        all_metrics = memory_system.get_all_tool_metrics()
        assert len(all_metrics) == 0

        cost_analysis = memory_system.get_cost_analysis()
        assert len(cost_analysis) == 0

    def test_zero_latency(self, memory_system):
        """Test handling of zero latency"""
        record = ToolUsageRecord(
            tool_name="FastTool",
            pattern_name="Test Pattern",
            query="test",
            success=True,
            latency_ms=0.0,
            score=0.8
        )
        memory_system.record_usage(record)

        metrics = memory_system.get_tool_metrics("FastTool", "Test Pattern")
        assert metrics.avg_latency_ms == 0.0

    def test_negative_score_clamped(self, memory_system):
        """Test that negative scores are handled"""
        record = ToolUsageRecord(
            tool_name="TestTool",
            pattern_name="Test Pattern",
            query="test",
            success=False,
            latency_ms=100,
            score=-0.5  # Invalid, but shouldn't crash
        )
        memory_system.record_usage(record)

        metrics = memory_system.get_tool_metrics("TestTool", "Test Pattern")
        assert metrics is not None


class TestIntegrationScenarios:
    """End-to-end integration scenarios"""

    def test_complete_learning_workflow(self, memory_system):
        """Test complete workflow: record → analyze → select best → retire worst"""
        # Simulate 3 tools competing for same pattern over time
        tools = [
            ("ToolAlpha", 25, 0.88, 0.85, 120),  # Good
            ("ToolBeta", 25, 0.72, 0.70, 100),   # Mediocre
            ("ToolGamma", 25, 0.35, 0.30, 200),  # Bad
        ]

        # Step 1: Record usages
        for tool_name, uses, success_rate, score, latency in tools:
            for i in range(uses):
                record = ToolUsageRecord(
                    tool_name=tool_name,
                    pattern_name="Production Readiness",
                    query=f"check code {i}",
                    success=(i < uses * success_rate),
                    latency_ms=latency,
                    cost=0.01,
                    score=score if i < uses * success_rate else 0.0
                )
                memory_system.record_usage(record)

        # Step 2: Get all metrics
        all_metrics = memory_system.get_all_tool_metrics()
        assert len(all_metrics) == 3

        # Step 3: Select best tool
        best_tool = memory_system.get_best_tool_for_pattern("Production Readiness")
        assert best_tool == "ToolAlpha", "Best performing tool should be selected"

        # Step 4: Identify tools to retire
        retire_candidates = memory_system.get_tools_to_retire(min_uses=20)
        assert len(retire_candidates) == 1
        assert retire_candidates[0].tool_name == "ToolGamma"

        # Step 5: Cost analysis
        costs = memory_system.get_cost_analysis()
        assert costs["ToolAlpha"] == pytest.approx(0.25, rel=0.01)  # 25 * $0.01

    def test_pattern_specific_performance(self, memory_system):
        """Test that same tool performs differently on different patterns"""
        # Tool performs well on Pattern A, poorly on Pattern B
        patterns = [
            ("Pattern A", 15, 0.9, 0.85),
            ("Pattern B", 15, 0.4, 0.35),
        ]

        for pattern_name, uses, success_rate, score in patterns:
            for i in range(uses):
                record = ToolUsageRecord(
                    tool_name="SameTool",
                    pattern_name=pattern_name,
                    query=f"test {i}",
                    success=(i < uses * success_rate),
                    latency_ms=100,
                    score=score if i < uses * success_rate else 0.0
                )
                memory_system.record_usage(record)

        metrics_a = memory_system.get_tool_metrics("SameTool", "Pattern A")
        metrics_b = memory_system.get_tool_metrics("SameTool", "Pattern B")

        assert metrics_a.recommendation == 'keep'
        assert metrics_b.recommendation == 'retire'

        # Best tool selection should be pattern-specific
        best_a = memory_system.get_best_tool_for_pattern("Pattern A")
        best_b = memory_system.get_best_tool_for_pattern("Pattern B")

        assert best_a == "SameTool"  # Good for Pattern A
        # Note: Even though Pattern B recommendation is 'retire',
        # it's still selected as best because it's the only option with enough uses.
        # This is reasonable behavior: select best available even if not ideal.
        assert best_b == "SameTool"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
