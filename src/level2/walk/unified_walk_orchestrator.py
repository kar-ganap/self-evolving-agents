"""
Unified WALK Orchestrator - Integrates all WALK phase components

Coordinates:
1. External library discovery (PyPI)
2. External API discovery
3. Tool memory and learning
4. Cost management and budgets
5. Acquisition decision-making

Provides complete external resource acquisition with cost awareness,
performance tracking, and intelligent decision-making.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.level2.walk.external_library_engine import ExternalLibraryEngine, ExternalLibraryIntegrationResult
from src.level2.walk.external_api_engine import ExternalAPIEngine, ExternalAPIIntegrationResult
from src.level2.walk.tool_memory_system import ToolMemorySystem, ToolUsageRecord
from src.level2.walk.cost_management_system import CostManagementSystem, BudgetPeriod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AcquisitionSource(Enum):
    """External resource acquisition sources"""
    LIBRARY = "library"  # PyPI library
    API = "api"          # External API


@dataclass
class WALKAcquisitionResult:
    """
    Result of WALK phase acquisition.

    Attributes:
        success: Whether acquisition succeeded
        source: Where the tool came from (library or API)
        tool_name: Name of acquired tool
        pattern_name: Pattern it addresses
        cost: Total cost of acquisition
        estimated_monthly_cost: Ongoing monthly cost
        tool_code: Generated wrapper code
        metadata: Additional acquisition metadata
        error: Error message if failed
    """
    success: bool
    source: Optional[AcquisitionSource] = None
    tool_name: Optional[str] = None
    pattern_name: Optional[str] = None
    cost: float = 0.0
    estimated_monthly_cost: float = 0.0
    tool_code: Optional[str] = None
    metadata: Optional[Dict] = None
    error: Optional[str] = None


class UnifiedWALKOrchestrator:
    """
    Unified orchestrator for WALK phase external resource acquisition.

    Integrates:
    - External library discovery and integration (PyPI)
    - External API discovery and wrapping
    - Tool memory and performance tracking
    - Cost management and budget enforcement

    Decision flow:
    1. Check budget before proceeding
    2. Search both libraries and APIs in parallel
    3. Rank by maturity, cost, and past performance
    4. Attempt acquisition (with cost tracking)
    5. Record usage in tool memory
    6. Return integrated tool
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        enable_cost_tracking: bool = True,
        enable_tool_memory: bool = True
    ):
        """
        Initialize unified WALK orchestrator.

        Args:
            gemini_api_key: Google API key for Gemini 2.5 Pro
            enable_cost_tracking: Enable cost management
            enable_tool_memory: Enable tool memory and learning
        """
        # Core engines
        self.library_engine = ExternalLibraryEngine(gemini_api_key=gemini_api_key)
        self.api_engine = ExternalAPIEngine(gemini_api_key=gemini_api_key)

        # Support systems
        self.enable_cost_tracking = enable_cost_tracking
        self.enable_tool_memory = enable_tool_memory

        if enable_cost_tracking:
            self.cost_system = CostManagementSystem()
        else:
            self.cost_system = None

        if enable_tool_memory:
            self.tool_memory = ToolMemorySystem()
        else:
            self.tool_memory = None

    def acquire_external_resource(
        self,
        pattern: Dict,
        missing_capabilities: List[str],
        prefer_source: Optional[AcquisitionSource] = None,
        max_cost: Optional[float] = None
    ) -> WALKAcquisitionResult:
        """
        Acquire external resource (library or API) for pattern.

        Args:
            pattern: Pattern dictionary with 'name' and 'description'
            missing_capabilities: List of missing capability descriptions
            prefer_source: Preferred source (library or API), or None for auto
            max_cost: Maximum cost to allow (overrides budget)

        Returns:
            WALKAcquisitionResult with acquisition outcome
        """
        pattern_name = pattern['name']
        logger.info(f"WALK acquisition for: {pattern_name}")

        start_time = time.time()

        try:
            # Step 1: Check budget
            if self.cost_system and not self._check_budget_allowance(max_cost or 50.0):
                return WALKAcquisitionResult(
                    success=False,
                    pattern_name=pattern_name,
                    error="Insufficient budget for acquisition"
                )

            # Step 2: Get recommendation from tool memory
            recommended_tool = None
            if self.tool_memory:
                recommended_tool = self.tool_memory.get_best_tool_for_pattern(pattern_name)
                if recommended_tool:
                    logger.info(f"Tool memory recommends: {recommended_tool}")

            # Step 3: Determine acquisition strategy
            if prefer_source == AcquisitionSource.LIBRARY:
                sources_to_try = [AcquisitionSource.LIBRARY]
            elif prefer_source == AcquisitionSource.API:
                sources_to_try = [AcquisitionSource.API]
            else:
                # Try library first (usually cheaper and more stable)
                sources_to_try = [AcquisitionSource.LIBRARY, AcquisitionSource.API]

            # Step 4: Attempt acquisition from sources
            for source in sources_to_try:
                logger.info(f"Attempting acquisition from: {source.value}")

                if source == AcquisitionSource.LIBRARY:
                    result = self._acquire_library(pattern, missing_capabilities)
                else:
                    result = self._acquire_api(pattern, missing_capabilities)

                if result.success:
                    # Record cost
                    if self.cost_system:
                        cost_recorded = self.cost_system.record_cost(
                            amount=result.cost,
                            category=f"{source.value}_acquisition",
                            description=f"Acquired {result.tool_name} for {pattern_name}",
                            tool_name=result.tool_name,
                            pattern_name=pattern_name,
                            acquisition_type=source.value
                        )

                        if not cost_recorded:
                            logger.warning("Cost recording failed (budget exceeded)")
                            # Acquisition succeeded but cost couldn't be recorded
                            # This is a warning, not a failure

                    # Record initial usage in tool memory (successful acquisition)
                    if self.tool_memory:
                        latency_ms = (time.time() - start_time) * 1000
                        self.tool_memory.record_usage(ToolUsageRecord(
                            tool_name=result.tool_name,
                            pattern_name=pattern_name,
                            query="initial_acquisition",
                            success=True,
                            latency_ms=latency_ms,
                            cost=result.cost,
                            score=0.7  # Initial optimistic score
                        ))

                    logger.info(f"Acquisition successful: {result.tool_name} from {source.value}")
                    return result

            # All sources failed
            return WALKAcquisitionResult(
                success=False,
                pattern_name=pattern_name,
                error="No suitable external resources found"
            )

        except Exception as e:
            logger.error(f"Acquisition failed with exception: {e}")
            return WALKAcquisitionResult(
                success=False,
                pattern_name=pattern_name,
                error=str(e)
            )

    def _check_budget_allowance(self, estimated_cost: float) -> bool:
        """
        Check if estimated cost is within budget.

        Args:
            estimated_cost: Estimated cost of acquisition

        Returns:
            True if cost is allowed, False otherwise
        """
        if not self.cost_system:
            return True

        # Check against all active budgets
        status = self.cost_system.get_budget_status()

        for period, info in status.items():
            remaining = info['remaining']
            if estimated_cost > remaining:
                logger.warning(
                    f"{period} budget insufficient: "
                    f"${estimated_cost:.2f} > ${remaining:.2f} remaining"
                )
                return False

        return True

    def _acquire_library(
        self,
        pattern: Dict,
        missing_capabilities: List[str]
    ) -> WALKAcquisitionResult:
        """
        Acquire external library from PyPI.

        Args:
            pattern: Pattern dictionary
            missing_capabilities: Missing capabilities

        Returns:
            WALKAcquisitionResult
        """
        # Use library engine (searches PyPI, installs, generates wrapper)
        result: ExternalLibraryIntegrationResult = self.library_engine.integrate_library(
            pattern=pattern,
            missing_capabilities=missing_capabilities,
            auto_install=False  # Don't auto-install to avoid system changes
        )

        if not result.success:
            return WALKAcquisitionResult(
                success=False,
                source=AcquisitionSource.LIBRARY,
                pattern_name=pattern['name'],
                error=result.error
            )

        # Calculate costs
        # Libraries are typically free, but wrapper generation has cost
        wrapper_generation_cost = 0.02  # ~$0.02 for Gemini 2.5 Pro call
        monthly_cost = 0.0  # Most PyPI libraries are free

        return WALKAcquisitionResult(
            success=True,
            source=AcquisitionSource.LIBRARY,
            tool_name=result.tool.name,
            pattern_name=pattern['name'],
            cost=wrapper_generation_cost,
            estimated_monthly_cost=monthly_cost,
            tool_code=result.tool.code,
            metadata={
                'library_name': result.library.name,
                'library_version': result.library.version,
                'maturity_score': result.library.maturity_score,
                'relevance_score': result.library.relevance_score
            }
        )

    def _acquire_api(
        self,
        pattern: Dict,
        missing_capabilities: List[str]
    ) -> WALKAcquisitionResult:
        """
        Acquire external API.

        Args:
            pattern: Pattern dictionary
            missing_capabilities: Missing capabilities

        Returns:
            WALKAcquisitionResult
        """
        # Use API engine (searches APIs.guru, generates wrapper)
        result: ExternalAPIIntegrationResult = self.api_engine.integrate_api(
            pattern=pattern,
            missing_capabilities=missing_capabilities
        )

        if not result.success:
            return WALKAcquisitionResult(
                success=False,
                source=AcquisitionSource.API,
                pattern_name=pattern['name'],
                error=result.error
            )

        # Calculate costs
        wrapper_generation_cost = 0.02  # ~$0.02 for Gemini 2.5 Pro call

        # Estimate monthly cost based on pricing
        monthly_cost = 0.0
        if result.api.pricing == "paid":
            monthly_cost = 30.0  # Assume $30/month for paid APIs
        elif result.api.pricing == "freemium":
            monthly_cost = 0.0  # Assume free tier usage

        return WALKAcquisitionResult(
            success=True,
            source=AcquisitionSource.API,
            tool_name=result.tool.name,
            pattern_name=pattern['name'],
            cost=wrapper_generation_cost,
            estimated_monthly_cost=monthly_cost,
            tool_code=result.tool.code,
            metadata={
                'api_name': result.api.name,
                'base_url': result.api.base_url,
                'auth_type': result.api.auth_type.value,
                'pricing': result.api.pricing,
                'maturity_score': result.api.maturity_score
            }
        )

    def record_tool_performance(
        self,
        tool_name: str,
        pattern_name: str,
        success: bool,
        latency_ms: float,
        score: float = 0.0,
        error: Optional[str] = None
    ):
        """
        Record tool performance for learning.

        Args:
            tool_name: Name of the tool
            pattern_name: Pattern it was used for
            success: Whether execution succeeded
            latency_ms: Execution time in milliseconds
            score: Quality score (0.0-1.0)
            error: Error message if failed
        """
        if not self.tool_memory:
            return

        self.tool_memory.record_usage(ToolUsageRecord(
            tool_name=tool_name,
            pattern_name=pattern_name,
            query="execution",
            success=success,
            latency_ms=latency_ms,
            score=score,
            error=error
        ))

        logger.info(
            f"Recorded performance: {tool_name} on {pattern_name} "
            f"(success={success}, score={score:.2f})"
        )

    def get_cost_summary(self) -> Dict:
        """
        Get cost management summary.

        Returns:
            Dict with budget status and spending analysis
        """
        if not self.cost_system:
            return {'enabled': False}

        return {
            'enabled': True,
            'budgets': self.cost_system.get_budget_status(),
            'spending_by_category': self.cost_system.get_spending_by_category(days=30),
            'monthly_forecast': self.cost_system.forecast_monthly_spend(),
            'optimization_recommendations': [
                {
                    'recommendation': r.recommendation,
                    'potential_savings': r.potential_savings,
                    'priority': r.priority
                }
                for r in self.cost_system.get_optimization_recommendations()
            ]
        }

    def get_tool_performance_summary(self) -> Dict:
        """
        Get tool performance summary.

        Returns:
            Dict with tool metrics and recommendations
        """
        if not self.tool_memory:
            return {'enabled': False}

        all_metrics = self.tool_memory.get_all_tool_metrics()

        return {
            'enabled': True,
            'total_tools_tracked': len(all_metrics),
            'tools_to_retire': [
                {'tool_name': m.tool_name, 'pattern': m.pattern_name, 'success_rate': m.success_rate}
                for m in self.tool_memory.get_tools_to_retire(min_uses=5)
            ],
            'top_performers': sorted(
                [
                    {
                        'tool_name': m.tool_name,
                        'pattern': m.pattern_name,
                        'success_rate': m.success_rate,
                        'avg_score': m.avg_score
                    }
                    for m in all_metrics
                ],
                key=lambda x: x['success_rate'] * x['avg_score'],
                reverse=True
            )[:5]
        }


# Example usage and testing
if __name__ == "__main__":
    print("Unified WALK Orchestrator - Test Mode\n")

    orchestrator = UnifiedWALKOrchestrator(
        enable_cost_tracking=True,
        enable_tool_memory=True
    )

    # Set budgets
    if orchestrator.cost_system:
        orchestrator.cost_system.set_budget(BudgetPeriod.DAILY, 10.0)
        orchestrator.cost_system.set_budget(BudgetPeriod.MONTHLY, 200.0)

    print("=" * 80)
    print("Test 1: Acquire External Library")
    print("=" * 80)

    pattern = {
        'name': 'JSON Schema Validation',
        'description': 'Validate JSON data against schemas'
    }

    capabilities = [
        'Validate JSON against schema',
        'Support draft-07 schemas'
    ]

    print(f"\nAcquiring resource for: {pattern['name']}")
    print("Preferred source: Library (PyPI)")

    result = orchestrator.acquire_external_resource(
        pattern=pattern,
        missing_capabilities=capabilities,
        prefer_source=AcquisitionSource.LIBRARY
    )

    if result.success:
        print(f"\n✓ Acquisition successful!")
        print(f"  Source: {result.source.value}")
        print(f"  Tool: {result.tool_name}")
        print(f"  Cost: ${result.cost:.2f}")
        print(f"  Monthly: ${result.estimated_monthly_cost:.2f}/month")
        print(f"  Code length: {len(result.tool_code)} characters")
    else:
        print(f"\n✗ Acquisition failed: {result.error}")

    # Test 2: Get summaries
    print("\n" + "=" * 80)
    print("Test 2: System Summaries")
    print("=" * 80)

    cost_summary = orchestrator.get_cost_summary()
    print("\nCost Summary:")
    print(f"  Enabled: {cost_summary['enabled']}")
    if cost_summary['enabled']:
        print(f"  Monthly forecast: ${cost_summary['monthly_forecast']:.2f}")

    performance_summary = orchestrator.get_tool_performance_summary()
    print("\nPerformance Summary:")
    print(f"  Enabled: {performance_summary['enabled']}")
    if performance_summary['enabled']:
        print(f"  Tools tracked: {performance_summary['total_tools_tracked']}")

    print("\n" + "=" * 80)
