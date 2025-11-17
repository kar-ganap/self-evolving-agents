"""
Capability Gap Detector - Identifies missing capabilities in pattern execution

Analyzes detected patterns and determines which ones lack adequate tooling
to support automated execution. This is the first component in the autonomous
tool generation pipeline.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
from pathlib import Path
import json


class CapabilityStatus(Enum):
    """Status of a pattern's capability support"""
    FULLY_SUPPORTED = "fully_supported"  # Has tool, works well
    PARTIALLY_SUPPORTED = "partially_supported"  # Has tool, needs improvement
    UNSUPPORTED = "unsupported"  # No tool exists
    NOT_AUTOMATABLE = "not_automatable"  # Pattern is inherently manual


@dataclass
class CapabilityGap:
    """
    Represents a detected capability gap for a pattern.

    Attributes:
        pattern_name: Name of the pattern (e.g., "Gap Analysis")
        status: Current capability support status
        existing_tools: List of tool names that partially support this pattern
        missing_capabilities: Specific capabilities that are missing
        frequency: How often this pattern appears (for prioritization)
        automation_potential: 0.0-1.0 score of how automatable this is
        justification: Why this status was assigned
    """
    pattern_name: str
    status: CapabilityStatus
    existing_tools: List[str]
    missing_capabilities: List[str]
    frequency: int
    automation_potential: float  # 0.0 = not automatable, 1.0 = fully automatable
    justification: str


class CapabilityGapDetector:
    """
    Detects capability gaps by analyzing patterns and their tooling support.

    This class:
    1. Loads pattern definitions
    2. Checks for existing tools (from src/level2/crawl/tools/)
    3. Analyzes which patterns lack tooling
    4. Assigns automation potential scores
    5. Returns prioritized capability gaps
    """

    def __init__(self, tool_registry_path: Optional[Path] = None):
        """
        Initialize the capability gap detector.

        Args:
            tool_registry_path: Path to tool_registry.json (tracks pattern->tool mappings)
                              If None, uses default: src/level2/crawl/tools/tool_registry.json
        """
        # Define the 10 learned patterns
        self.patterns = [
            "Gap Analysis",
            "Tradeoff Analysis",
            "Production Readiness",
            "Brutal Accuracy",
            "Multi-Dimensional Evaluation",
            "Hint-Based Learning",
            "Diminishing Returns",
            "Mechanistic Understanding",
            "Context-Dependent Recommendations",
            "Precision Policing"
        ]

        # Load tool registry (pattern -> tool mappings)
        if tool_registry_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            tool_registry_path = project_root / "src/level2/crawl/tools/tool_registry.json"

        self.tool_registry_path = tool_registry_path
        self.tool_registry = self._load_tool_registry()

        # Pattern automation potential (heuristic scores)
        # High = mechanical checks, Low = requires human judgment
        self.automation_scores = {
            "Gap Analysis": 0.7,  # Can check for common missing items
            "Tradeoff Analysis": 0.3,  # Highly domain-dependent, needs context
            "Production Readiness": 0.9,  # Very mechanical (tests, types, docs, error handling)
            "Brutal Accuracy": 0.1,  # Requires deep reasoning, not automatable
            "Multi-Dimensional Evaluation": 0.6,  # Can structure evaluation, but filling needs human
            "Hint-Based Learning": 0.4,  # Can provide hints templates, but context-dependent
            "Diminishing Returns": 0.5,  # Can estimate complexity, but ROI needs human judgment
            "Mechanistic Understanding": 0.2,  # Requires explanation generation, hard to automate
            "Context-Dependent Recommendations": 0.3,  # By definition requires context understanding
            "Precision Policing": 0.6  # Can check for vague terms, suggest specific alternatives
        }

    def _load_tool_registry(self) -> Dict[str, List[str]]:
        """
        Load tool registry from JSON file.

        Returns:
            Dict mapping pattern_name -> list of tool names
        """
        if not self.tool_registry_path.exists():
            # No registry yet, return empty
            return {}

        try:
            with open(self.tool_registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading tool registry: {e}")
            return {}

    def detect_gaps(self, pattern_frequency: Optional[Dict[str, int]] = None) -> List[CapabilityGap]:
        """
        Detect capability gaps across all patterns.

        Args:
            pattern_frequency: Optional dict of pattern_name -> count (how often it's triggered)
                             Used for prioritization. If None, all patterns get frequency=1.

        Returns:
            List of CapabilityGap objects, sorted by priority (high to low)
            Priority = frequency * automation_potential
        """
        if pattern_frequency is None:
            pattern_frequency = {pattern: 1 for pattern in self.patterns}

        gaps = []

        for pattern in self.patterns:
            gap = self._analyze_pattern_capability(
                pattern_name=pattern,
                frequency=pattern_frequency.get(pattern, 0)
            )
            gaps.append(gap)

        # Sort by priority: frequency * automation_potential
        gaps.sort(key=lambda g: g.frequency * g.automation_potential, reverse=True)

        return gaps

    def _analyze_pattern_capability(self, pattern_name: str, frequency: int) -> CapabilityGap:
        """
        Analyze a single pattern's capability support.

        Args:
            pattern_name: Name of the pattern to analyze
            frequency: How often this pattern is triggered

        Returns:
            CapabilityGap object describing the gap
        """
        # Check if tools exist for this pattern
        existing_tools = self.tool_registry.get(pattern_name, [])
        automation_potential = self.automation_scores.get(pattern_name, 0.5)

        # Determine status and missing capabilities
        if not existing_tools:
            status = CapabilityStatus.UNSUPPORTED
            missing_capabilities = self._get_missing_capabilities(pattern_name)
            justification = f"No tools exist for {pattern_name}"
        elif len(existing_tools) < 2:  # Has 1 tool, but may need more
            status = CapabilityStatus.PARTIALLY_SUPPORTED
            missing_capabilities = self._get_missing_capabilities(pattern_name)
            justification = f"Only {len(existing_tools)} tool(s) exist, may need enhancement"
        else:
            status = CapabilityStatus.FULLY_SUPPORTED
            missing_capabilities = []
            justification = f"{len(existing_tools)} tools provide good coverage"

        # Mark low-automation patterns as NOT_AUTOMATABLE
        if automation_potential < 0.3:
            status = CapabilityStatus.NOT_AUTOMATABLE
            justification = f"{pattern_name} requires human judgment (automation_potential={automation_potential:.1f})"

        return CapabilityGap(
            pattern_name=pattern_name,
            status=status,
            existing_tools=existing_tools,
            missing_capabilities=missing_capabilities,
            frequency=frequency,
            automation_potential=automation_potential,
            justification=justification
        )

    def _get_missing_capabilities(self, pattern_name: str) -> List[str]:
        """
        Determine what capabilities are missing for a pattern.

        This is pattern-specific logic defining what a tool should do.

        Args:
            pattern_name: The pattern to analyze

        Returns:
            List of missing capability descriptions
        """
        capabilities_map = {
            "Gap Analysis": [
                "Checklist generator for common missing items (tests, docs, error handling)",
                "Code analyzer to detect missing error paths",
                "API design validator (checks for pagination, filtering, sorting)"
            ],
            "Tradeoff Analysis": [
                "Tradeoff template generator (pros/cons structure)",
                "Benchmark data fetcher (performance comparisons)",
                "Cost calculator for cloud services"
            ],
            "Production Readiness": [
                "Static analyzer for missing type hints",
                "Test coverage checker",
                "Documentation completeness checker",
                "Error handling validator"
            ],
            "Brutal Accuracy": [
                # Not automatable - requires reasoning
            ],
            "Multi-Dimensional Evaluation": [
                "Evaluation criteria generator (dimensions to consider)",
                "Scoring template builder"
            ],
            "Hint-Based Learning": [
                "Debugging hint generator (common error patterns)",
                "Example trace generator"
            ],
            "Diminishing Returns": [
                "Complexity estimator (Big-O analyzer)",
                "Performance impact calculator"
            ],
            "Mechanistic Understanding": [
                # Hard to automate - needs explanation
            ],
            "Context-Dependent Recommendations": [
                "Context extractor (identify constraints from query)",
                "Recommendation template with context placeholders"
            ],
            "Precision Policing": [
                "Vague term detector (finds 'fast', 'slow', 'better')",
                "Specific alternative suggester"
            ]
        }

        return capabilities_map.get(pattern_name, [])

    def get_top_gaps(
        self,
        n: int = 5,
        min_frequency: int = 1,
        pattern_frequency: Optional[Dict[str, int]] = None
    ) -> List[CapabilityGap]:
        """
        Get top N capability gaps that should be addressed.

        Args:
            n: Number of top gaps to return
            min_frequency: Minimum frequency to consider (filters out rare patterns)
            pattern_frequency: Optional dict of pattern_name -> count

        Returns:
            Top N capability gaps sorted by priority
        """
        all_gaps = self.detect_gaps(pattern_frequency=pattern_frequency)

        # Filter by frequency
        filtered = [g for g in all_gaps if g.frequency >= min_frequency]

        # Filter out NOT_AUTOMATABLE and FULLY_SUPPORTED
        actionable = [
            g for g in filtered
            if g.status in [CapabilityStatus.UNSUPPORTED, CapabilityStatus.PARTIALLY_SUPPORTED]
        ]

        return actionable[:n]

    def print_gap_report(self, pattern_frequency: Optional[Dict[str, int]] = None):
        """Print a human-readable gap analysis report"""
        gaps = self.detect_gaps(pattern_frequency)

        print("=" * 80)
        print("CAPABILITY GAP ANALYSIS REPORT")
        print("=" * 80)
        print()

        # Summary by status
        status_counts = {}
        for gap in gaps:
            status_counts[gap.status] = status_counts.get(gap.status, 0) + 1

        print("Summary:")
        for status, count in status_counts.items():
            print(f"  {status.value:20s}: {count}")
        print()

        # Top actionable gaps
        top_gaps = self.get_top_gaps(n=5)
        print("Top 5 Actionable Gaps (by priority):")
        print("-" * 80)

        for i, gap in enumerate(top_gaps, 1):
            priority = gap.frequency * gap.automation_potential
            print(f"\n{i}. {gap.pattern_name}")
            print(f"   Status:    {gap.status.value}")
            print(f"   Frequency: {gap.frequency}")
            print(f"   Automation Potential: {gap.automation_potential:.1f}")
            print(f"   Priority Score: {priority:.2f}")
            print(f"   Existing Tools: {', '.join(gap.existing_tools) if gap.existing_tools else 'None'}")
            print(f"   Missing Capabilities:")
            for cap in gap.missing_capabilities[:3]:  # Show top 3
                print(f"     - {cap}")
            print(f"   Justification: {gap.justification}")

        print()
        print("=" * 80)


# Example usage and testing
if __name__ == "__main__":
    import sys

    print("🔍 Capability Gap Detector - Test Mode\n")

    # Create detector
    detector = CapabilityGapDetector()

    # Simulate pattern frequency (from pattern matcher historical data)
    simulated_frequency = {
        "Production Readiness": 15,  # Most common
        "Gap Analysis": 12,
        "Tradeoff Analysis": 10,
        "Precision Policing": 8,
        "Diminishing Returns": 6,
        "Multi-Dimensional Evaluation": 5,
        "Mechanistic Understanding": 4,
        "Hint-Based Learning": 3,
        "Context-Dependent Recommendations": 2,
        "Brutal Accuracy": 1
    }

    # Print report
    detector.print_gap_report(pattern_frequency=simulated_frequency)

    # Test: Get top gaps
    print("\n" + "=" * 80)
    print("Testing get_top_gaps(n=3):")
    print("=" * 80)

    top_3 = detector.get_top_gaps(n=3, min_frequency=5)
    for gap in top_3:
        priority = gap.frequency * gap.automation_potential
        print(f"\n- {gap.pattern_name}: priority={priority:.2f}, freq={gap.frequency}, auto={gap.automation_potential:.1f}")
