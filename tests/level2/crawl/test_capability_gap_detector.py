"""
Unit tests for CapabilityGapDetector

Tests capability gap detection logic, automation scoring, and prioritization.
"""

import pytest
from pathlib import Path
import json
import tempfile

from src.level2.crawl.capability_gap_detector import (
    CapabilityGapDetector,
    CapabilityStatus,
    CapabilityGap
)


class TestCapabilityGapDetector:
    """Test suite for CapabilityGapDetector"""

    def test_initialization(self):
        """Test detector initializes with correct patterns"""
        detector = CapabilityGapDetector()

        assert len(detector.patterns) == 10
        assert "Gap Analysis" in detector.patterns
        assert "Production Readiness" in detector.patterns
        assert "Brutal Accuracy" in detector.patterns

    def test_automation_scores_defined(self):
        """Test all patterns have automation scores"""
        detector = CapabilityGapDetector()

        for pattern in detector.patterns:
            assert pattern in detector.automation_scores
            score = detector.automation_scores[pattern]
            assert 0.0 <= score <= 1.0

    def test_detect_gaps_no_tools(self):
        """Test gap detection when no tools exist"""
        detector = CapabilityGapDetector()
        gaps = detector.detect_gaps()

        assert len(gaps) == 10

        # Should have UNSUPPORTED or NOT_AUTOMATABLE status
        for gap in gaps:
            assert gap.status in [
                CapabilityStatus.UNSUPPORTED,
                CapabilityStatus.NOT_AUTOMATABLE
            ]

    def test_detect_gaps_with_frequency(self):
        """Test gap detection respects frequency for prioritization"""
        detector = CapabilityGapDetector()

        # Production Readiness has high automation score (0.9)
        # Gap Analysis has good automation score (0.7)
        frequency = {
            "Production Readiness": 10,
            "Gap Analysis": 5,
            "Brutal Accuracy": 20  # High freq but low automation (0.1) = NOT_AUTOMATABLE
        }

        gaps = detector.detect_gaps(pattern_frequency=frequency)

        # Gaps should be sorted by priority (frequency * automation_potential)
        # Production Readiness: 10 * 0.9 = 9.0
        # Gap Analysis: 5 * 0.7 = 3.5

        # Find these gaps
        prod_gap = next(g for g in gaps if g.pattern_name == "Production Readiness")
        gap_gap = next(g for g in gaps if g.pattern_name == "Gap Analysis")
        brutal_gap = next(g for g in gaps if g.pattern_name == "Brutal Accuracy")

        assert prod_gap.frequency == 10
        assert gap_gap.frequency == 5
        assert brutal_gap.frequency == 20
        assert brutal_gap.status == CapabilityStatus.NOT_AUTOMATABLE

        # Production Readiness should be higher priority than Gap Analysis
        prod_priority = prod_gap.frequency * prod_gap.automation_potential
        gap_priority = gap_gap.frequency * gap_gap.automation_potential
        assert prod_priority > gap_priority

    def test_get_top_gaps(self):
        """Test getting top N actionable gaps"""
        detector = CapabilityGapDetector()

        frequency = {
            "Production Readiness": 15,
            "Gap Analysis": 12,
            "Precision Policing": 8,
            "Brutal Accuracy": 5,  # Low automation, should be filtered
            "Mechanistic Understanding": 3  # Low automation, should be filtered
        }

        top_gaps = detector.get_top_gaps(n=3, min_frequency=1)

        # Should return <=3 gaps, excluding NOT_AUTOMATABLE
        assert len(top_gaps) <= 3

        # Should not include low-automation patterns
        gap_names = [g.pattern_name for g in top_gaps]
        assert "Brutal Accuracy" not in gap_names
        assert "Mechanistic Understanding" not in gap_names

        # Should be sorted by priority
        for i in range(len(top_gaps) - 1):
            priority_i = top_gaps[i].frequency * top_gaps[i].automation_potential
            priority_next = top_gaps[i+1].frequency * top_gaps[i+1].automation_potential
            assert priority_i >= priority_next

    def test_get_top_gaps_min_frequency_filter(self):
        """Test min_frequency filtering"""
        detector = CapabilityGapDetector()

        frequency = {
            "Production Readiness": 10,
            "Gap Analysis": 3,  # Below min_frequency=5
            "Precision Policing": 1   # Below min_frequency=5
        }

        top_gaps = detector.get_top_gaps(n=5, min_frequency=5, pattern_frequency=frequency)

        # Only Production Readiness (freq=10) should pass filter
        gap_names = [g.pattern_name for g in top_gaps]
        assert "Production Readiness" in gap_names
        assert "Gap Analysis" not in gap_names
        assert "Precision Policing" not in gap_names

    def test_missing_capabilities_defined(self):
        """Test all patterns have defined missing capabilities"""
        detector = CapabilityGapDetector()

        # High-automation patterns should have specific capabilities
        high_auto_patterns = [
            "Production Readiness",
            "Gap Analysis",
            "Precision Policing"
        ]

        for pattern in high_auto_patterns:
            capabilities = detector._get_missing_capabilities(pattern)
            assert len(capabilities) > 0, f"{pattern} should have defined capabilities"

    def test_tool_registry_loading_empty(self):
        """Test tool registry loads empty when file doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_path = Path(tmpdir) / "nonexistent" / "tool_registry.json"
            detector = CapabilityGapDetector(tool_registry_path=nonexistent_path)

            assert detector.tool_registry == {}

    def test_tool_registry_loading_with_tools(self):
        """Test tool registry loads correctly when tools exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "tool_registry.json"

            # Create mock registry
            mock_registry = {
                "Production Readiness": ["type_checker", "test_coverage_tool"],
                "Gap Analysis": ["gap_analyzer"]
            }

            registry_path.parent.mkdir(parents=True, exist_ok=True)
            with open(registry_path, 'w') as f:
                json.dump(mock_registry, f)

            detector = CapabilityGapDetector(tool_registry_path=registry_path)

            assert detector.tool_registry == mock_registry
            assert "Production Readiness" in detector.tool_registry
            assert len(detector.tool_registry["Production Readiness"]) == 2

    def test_status_with_existing_tools(self):
        """Test gap status reflects existing tools"""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "tool_registry.json"

            mock_registry = {
                "Production Readiness": ["type_checker", "test_coverage_tool"],  # 2 tools = FULLY_SUPPORTED
                "Gap Analysis": ["gap_analyzer"]  # 1 tool = PARTIALLY_SUPPORTED
            }

            registry_path.parent.mkdir(parents=True, exist_ok=True)
            with open(registry_path, 'w') as f:
                json.dump(mock_registry, f)

            detector = CapabilityGapDetector(tool_registry_path=registry_path)
            gaps = detector.detect_gaps()

            prod_gap = next(g for g in gaps if g.pattern_name == "Production Readiness")
            gap_gap = next(g for g in gaps if g.pattern_name == "Gap Analysis")

            assert prod_gap.status == CapabilityStatus.FULLY_SUPPORTED
            assert len(prod_gap.existing_tools) == 2

            assert gap_gap.status == CapabilityStatus.PARTIALLY_SUPPORTED
            assert len(gap_gap.existing_tools) == 1

    def test_capability_gap_dataclass(self):
        """Test CapabilityGap dataclass structure"""
        gap = CapabilityGap(
            pattern_name="Test Pattern",
            status=CapabilityStatus.UNSUPPORTED,
            existing_tools=[],
            missing_capabilities=["test_cap_1", "test_cap_2"],
            frequency=5,
            automation_potential=0.8,
            justification="Test justification"
        )

        assert gap.pattern_name == "Test Pattern"
        assert gap.status == CapabilityStatus.UNSUPPORTED
        assert gap.frequency == 5
        assert gap.automation_potential == 0.8
        assert len(gap.missing_capabilities) == 2

    def test_low_automation_marked_not_automatable(self):
        """Test patterns with low automation potential are marked NOT_AUTOMATABLE"""
        detector = CapabilityGapDetector()
        gaps = detector.detect_gaps()

        # Brutal Accuracy has automation_potential=0.1 (< 0.3 threshold)
        brutal_gap = next(g for g in gaps if g.pattern_name == "Brutal Accuracy")
        assert brutal_gap.status == CapabilityStatus.NOT_AUTOMATABLE
        assert "human judgment" in brutal_gap.justification.lower()

    def test_print_gap_report_runs(self, capsys):
        """Test print_gap_report executes without errors"""
        detector = CapabilityGapDetector()

        frequency = {
            "Production Readiness": 10,
            "Gap Analysis": 5
        }

        # Should not raise
        detector.print_gap_report(pattern_frequency=frequency)

        captured = capsys.readouterr()
        assert "CAPABILITY GAP ANALYSIS REPORT" in captured.out
        assert "Production Readiness" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
