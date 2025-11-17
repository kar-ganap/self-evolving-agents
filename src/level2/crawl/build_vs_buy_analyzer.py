"""
Build vs Buy Analyzer - Compares internal development vs external acquisition

Analyzes capability gaps and determines whether to build custom tools or
use existing libraries/APIs. Provides cost estimates and recommendations.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
import re


class AcquisitionType(Enum):
    """Type of tool acquisition"""
    BUILD = "build"  # Generate custom tool code
    LIBRARY = "library"  # Use existing Python library
    API = "api"  # Use external API/service
    HYBRID = "hybrid"  # Combination of build + library/API


@dataclass
class BuildOption:
    """
    Represents building a custom tool.

    Attributes:
        complexity: Estimated implementation complexity (1-10)
        estimated_hours: Development time in hours
        lines_of_code: Estimated LOC
        dependencies: Required libraries for implementation
        testing_effort: Testing complexity (1-10)
        maintenance_score: Ongoing maintenance burden (1-10, higher = more)
    """
    complexity: int  # 1-10
    estimated_hours: float
    lines_of_code: int
    dependencies: List[str]
    testing_effort: int  # 1-10
    maintenance_score: int  # 1-10


@dataclass
class BuyOption:
    """
    Represents using an existing library or API.

    Attributes:
        source: Library name or API service name
        acquisition_type: LIBRARY or API
        cost_per_month: Monthly cost in USD (0 for free libraries)
        setup_hours: Time to integrate
        learning_curve: Complexity to learn (1-10)
        vendor_lock_in: Risk of vendor dependency (1-10)
        maturity_score: How mature/stable (1-10, higher = better)
    """
    source: str
    acquisition_type: AcquisitionType
    cost_per_month: float  # USD
    setup_hours: float
    learning_curve: int  # 1-10
    vendor_lock_in: int  # 1-10
    maturity_score: int  # 1-10


@dataclass
class BuildVsBuyRecommendation:
    """
    Final recommendation for a capability gap.

    Attributes:
        pattern_name: Pattern requiring capability
        recommended_action: BUILD, LIBRARY, API, or HYBRID
        build_option: Build analysis (if applicable)
        buy_options: List of buy options (if applicable)
        rationale: Explanation of recommendation
        total_cost_estimate: Estimated total cost over 12 months
        confidence: Confidence in recommendation (0.0-1.0)
    """
    pattern_name: str
    recommended_action: AcquisitionType
    build_option: Optional[BuildOption]
    buy_options: List[BuyOption]
    rationale: str
    total_cost_estimate: float  # USD over 12 months
    confidence: float  # 0.0-1.0


class BuildVsBuyAnalyzer:
    """
    Analyzes capability gaps and recommends build vs buy.

    Decision factors:
    1. Complexity: Simple tools = build, complex = buy
    2. Cost: Free library > build > paid API
    3. Time: Quick integration (library) vs slower (build custom)
    4. Specificity: Generic needs = library, specific needs = build
    5. Maintenance: Prefer low-maintenance options
    """

    def __init__(self, hourly_dev_cost: float = 100.0):
        """
        Initialize the analyzer.

        Args:
            hourly_dev_cost: Cost per developer hour in USD (default: $100)
        """
        self.hourly_dev_cost = hourly_dev_cost

        # Known libraries for different capabilities
        self.known_libraries = {
            "type_checking": [
                {"name": "mypy", "setup_hours": 1.0, "maturity": 9},
                {"name": "pyright", "setup_hours": 0.5, "maturity": 8}
            ],
            "test_coverage": [
                {"name": "coverage.py", "setup_hours": 0.5, "maturity": 10},
                {"name": "pytest-cov", "setup_hours": 0.3, "maturity": 9}
            ],
            "code_complexity": [
                {"name": "radon", "setup_hours": 0.5, "maturity": 8},
                {"name": "mccabe", "setup_hours": 0.3, "maturity": 7}
            ],
            "linting": [
                {"name": "ruff", "setup_hours": 0.5, "maturity": 8},
                {"name": "pylint", "setup_hours": 1.0, "maturity": 9}
            ]
        }

    def analyze(
        self,
        pattern_name: str,
        missing_capabilities: List[str],
        automation_potential: float
    ) -> BuildVsBuyRecommendation:
        """
        Analyze a capability gap and recommend build vs buy.

        Args:
            pattern_name: Name of the pattern
            missing_capabilities: List of capability descriptions
            automation_potential: Automation score (0.0-1.0)

        Returns:
            BuildVsBuyRecommendation with analysis and decision
        """
        # Analyze build option
        build_option = self._estimate_build_cost(missing_capabilities, automation_potential)

        # Analyze buy options (libraries/APIs)
        buy_options = self._find_buy_options(missing_capabilities)

        # Make recommendation
        recommendation = self._make_recommendation(
            pattern_name=pattern_name,
            build_option=build_option,
            buy_options=buy_options,
            automation_potential=automation_potential
        )

        return recommendation

    def _estimate_build_cost(
        self,
        capabilities: List[str],
        automation_potential: float
    ) -> BuildOption:
        """
        Estimate cost and complexity of building custom tool.

        Args:
            capabilities: Capabilities to implement
            automation_potential: How automatable (affects complexity)

        Returns:
            BuildOption with cost estimates
        """
        # Base complexity on number of capabilities and automation potential
        num_capabilities = len(capabilities)

        # Lower automation potential = harder to build
        complexity_factor = 1.0 - (automation_potential * 0.5)
        base_complexity = min(num_capabilities * 2 * complexity_factor, 10)

        # Estimate LOC (50-200 per capability)
        loc_per_capability = int(100 * complexity_factor)
        total_loc = num_capabilities * loc_per_capability

        # Estimate hours (complexity * LOC / 50)
        estimated_hours = base_complexity * (total_loc / 50.0)
        estimated_hours = min(estimated_hours, 40)  # Cap at 1 week

        # Testing effort proportional to complexity
        testing_effort = min(int(base_complexity * 0.7), 10)

        # Maintenance score: higher complexity = more maintenance
        maintenance_score = min(int(base_complexity * 0.8), 10)

        # Detect likely dependencies from capability descriptions
        dependencies = self._detect_dependencies(capabilities)

        return BuildOption(
            complexity=int(base_complexity),
            estimated_hours=round(estimated_hours, 1),
            lines_of_code=total_loc,
            dependencies=dependencies,
            testing_effort=testing_effort,
            maintenance_score=maintenance_score
        )

    def _detect_dependencies(self, capabilities: List[str]) -> List[str]:
        """Detect likely Python dependencies from capability descriptions"""
        deps = []
        capability_text = " ".join(capabilities).lower()

        # Pattern matching for common dependencies
        if "ast" in capability_text or "parse" in capability_text:
            deps.append("ast")
        if "type" in capability_text:
            deps.append("typing")
        if "test" in capability_text:
            deps.append("pytest")
        if "coverage" in capability_text:
            deps.append("coverage")
        if "complexity" in capability_text or "cyclomatic" in capability_text:
            deps.append("radon")
        if "static" in capability_text or "lint" in capability_text:
            deps.append("pylint")

        return list(set(deps)) or ["typing"]  # Default to typing if none detected

    def _find_buy_options(self, capabilities: List[str]) -> List[BuyOption]:
        """
        Find existing libraries or APIs that could fulfill capabilities.

        Args:
            capabilities: Capability descriptions

        Returns:
            List of BuyOption objects
        """
        buy_options = []
        capability_text = " ".join(capabilities).lower()

        # Check for known library matches
        for capability_key, libraries in self.known_libraries.items():
            if capability_key.replace("_", " ") in capability_text:
                for lib in libraries:
                    buy_options.append(BuyOption(
                        source=lib["name"],
                        acquisition_type=AcquisitionType.LIBRARY,
                        cost_per_month=0.0,  # Free open-source
                        setup_hours=lib["setup_hours"],
                        learning_curve=3,  # Generally low for Python libs
                        vendor_lock_in=2,  # Open source = low lock-in
                        maturity_score=lib["maturity"]
                    ))

        # If no libraries found, suggest generic build
        if not buy_options:
            # For some patterns, building is the only option
            pass

        return buy_options

    def _make_recommendation(
        self,
        pattern_name: str,
        build_option: BuildOption,
        buy_options: List[BuyOption],
        automation_potential: float
    ) -> BuildVsBuyRecommendation:
        """
        Make final build vs buy recommendation.

        Decision logic:
        1. If good library exists (free, mature): BUY (library)
        2. If build is simple (< 5 complexity, < 10 hours): BUILD
        3. If API exists and build is complex (> 20 hours): BUY (API)
        4. Otherwise: BUILD

        Args:
            pattern_name: Pattern name
            build_option: Build analysis
            buy_options: Available buy options
            automation_potential: Automation score

        Returns:
            BuildVsBuyRecommendation with decision and rationale
        """
        # Cost calculations
        build_cost_12mo = build_option.estimated_hours * self.hourly_dev_cost
        build_cost_12mo += (build_option.maintenance_score * 2 * self.hourly_dev_cost)  # Maintenance

        # Decision logic
        best_buy_option = None
        buy_cost_12mo = float('inf')

        if buy_options:
            # Find cheapest buy option
            for option in buy_options:
                cost = (option.cost_per_month * 12) + (option.setup_hours * self.hourly_dev_cost)
                if cost < buy_cost_12mo:
                    buy_cost_12mo = cost
                    best_buy_option = option

            # Decision: Free mature library beats everything
            if best_buy_option and best_buy_option.cost_per_month == 0 and best_buy_option.maturity_score >= 8:
                return BuildVsBuyRecommendation(
                    pattern_name=pattern_name,
                    recommended_action=AcquisitionType.LIBRARY,
                    build_option=build_option,
                    buy_options=[best_buy_option],
                    rationale=f"Mature free library ({best_buy_option.source}) available. "
                              f"Setup cost: ${best_buy_option.setup_hours * self.hourly_dev_cost:.0f}, "
                              f"vs build cost: ${build_cost_12mo:.0f}",
                    total_cost_estimate=buy_cost_12mo,
                    confidence=0.9
                )

        # Decision: Simple build (< 5 complexity, < 10 hours)
        if build_option.complexity <= 5 and build_option.estimated_hours <= 10:
            return BuildVsBuyRecommendation(
                pattern_name=pattern_name,
                recommended_action=AcquisitionType.BUILD,
                build_option=build_option,
                buy_options=buy_options,
                rationale=f"Simple implementation ({build_option.estimated_hours}h, "
                          f"{build_option.lines_of_code} LOC). Building custom tool is cost-effective.",
                total_cost_estimate=build_cost_12mo,
                confidence=0.8
            )

        # Decision: Complex build and library available
        if best_buy_option and build_option.estimated_hours > 20:
            return BuildVsBuyRecommendation(
                pattern_name=pattern_name,
                recommended_action=best_buy_option.acquisition_type,
                build_option=build_option,
                buy_options=[best_buy_option],
                rationale=f"Complex build ({build_option.estimated_hours}h). "
                          f"Using {best_buy_option.source} saves time. "
                          f"Cost: ${buy_cost_12mo:.0f} vs ${build_cost_12mo:.0f} to build.",
                total_cost_estimate=buy_cost_12mo,
                confidence=0.7
            )

        # Default: BUILD (moderate complexity, no good alternatives)
        return BuildVsBuyRecommendation(
            pattern_name=pattern_name,
            recommended_action=AcquisitionType.BUILD,
            build_option=build_option,
            buy_options=buy_options,
            rationale=f"Moderate complexity ({build_option.complexity}/10). "
                      f"Custom tool provides best fit for specific needs. "
                      f"Estimated cost: ${build_cost_12mo:.0f} over 12 months.",
            total_cost_estimate=build_cost_12mo,
            confidence=0.6
        )


# Example usage and testing
if __name__ == "__main__":
    print("🔨 Build vs Buy Analyzer - Test Mode\n")

    analyzer = BuildVsBuyAnalyzer(hourly_dev_cost=100.0)

    # Test case 1: Production Readiness (has libraries available)
    print("=" * 80)
    print("Test 1: Production Readiness - Type Checking")
    print("=" * 80)

    rec1 = analyzer.analyze(
        pattern_name="Production Readiness",
        missing_capabilities=[
            "Static analyzer for missing type hints",
            "Type coverage checker"
        ],
        automation_potential=0.9
    )

    print(f"\nPattern: {rec1.pattern_name}")
    print(f"Recommendation: {rec1.recommended_action.value.upper()}")
    print(f"Rationale: {rec1.rationale}")
    print(f"Total Cost (12mo): ${rec1.total_cost_estimate:.0f}")
    print(f"Confidence: {rec1.confidence:.1%}")

    if rec1.build_option:
        print(f"\nBuild Option:")
        print(f"  Complexity: {rec1.build_option.complexity}/10")
        print(f"  Hours: {rec1.build_option.estimated_hours}h")
        print(f"  LOC: {rec1.build_option.lines_of_code}")

    if rec1.buy_options:
        print(f"\nBuy Options:")
        for opt in rec1.buy_options[:2]:
            print(f"  - {opt.source}: ${opt.cost_per_month}/mo, {opt.setup_hours}h setup")

    # Test case 2: Gap Analysis (likely build)
    print("\n" + "=" * 80)
    print("Test 2: Gap Analysis - Custom Checklist")
    print("=" * 80)

    rec2 = analyzer.analyze(
        pattern_name="Gap Analysis",
        missing_capabilities=[
            "Checklist generator for common missing items",
            "API design validator (pagination, filtering, sorting)"
        ],
        automation_potential=0.7
    )

    print(f"\nPattern: {rec2.pattern_name}")
    print(f"Recommendation: {rec2.recommended_action.value.upper()}")
    print(f"Rationale: {rec2.rationale}")
    print(f"Total Cost (12mo): ${rec2.total_cost_estimate:.0f}")
    print(f"Confidence: {rec2.confidence:.1%}")

    if rec2.build_option:
        print(f"\nBuild Option:")
        print(f"  Complexity: {rec2.build_option.complexity}/10")
        print(f"  Hours: {rec2.build_option.estimated_hours}h")
        print(f"  Dependencies: {', '.join(rec2.build_option.dependencies)}")

    print("\n" + "=" * 80)
