"""
Capability Evolution Engine - Orchestrates the full CRAWL workflow

This is the main integration point that coordinates:
1. Gap detection from Phase 0 patterns
2. Build vs Buy analysis
3. Approval workflow (with bypass)
4. Tool acquisition
5. Tool registration in pipeline

Implements the complete self-evolution loop for the CRAWL phase.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path

from src.level2.crawl.build_vs_buy_analyzer import BuildVsBuyAnalyzer
from src.level2.crawl.approval_workflow import ApprovalWorkflow
from src.level2.crawl.tool_acquisition_engine import ToolAcquisitionEngine, GeneratedTool
from src.level2.crawl.unified_agent_pipeline import ToolRegistry, UnifiedAgentPipeline


@dataclass
class EvolutionResult:
    """
    Result of evolution cycle.

    Attributes:
        pattern_name: Pattern that triggered evolution
        tool_acquired: Whether a tool was successfully acquired
        tool: Generated tool (if acquired)
        approval_bypassed: Whether approval was bypassed
        error: Error message if evolution failed
    """
    pattern_name: str
    tool_acquired: bool
    tool: Optional[GeneratedTool] = None
    approval_bypassed: bool = False
    error: Optional[str] = None


class CapabilityEvolutionEngine:
    """
    Orchestrates the complete CRAWL evolution workflow.

    Flow:
    1. Detect gaps in capabilities (from Phase 0 patterns)
    2. Analyze build vs buy options
    3. Check approval requirements (bypass if applicable)
    4. Acquire tool (build or buy)
    5. Register tool in pipeline
    6. Return evolution result

    This creates the self-improving loop where the agent identifies
    what it's missing and autonomously acquires new capabilities.
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        tool_registry: Optional[ToolRegistry] = None,
        config_path: Optional[Path] = None
    ):
        """
        Initialize the evolution engine.

        Args:
            gemini_api_key: Google API key for Gemini 2.5 Pro
            tool_registry: Existing ToolRegistry (or creates new one)
            config_path: Path to approval_settings.yaml
        """
        self.analyzer = BuildVsBuyAnalyzer()
        self.workflow = ApprovalWorkflow(config_path=config_path)
        self.engine = ToolAcquisitionEngine(gemini_api_key=gemini_api_key)
        self.tool_registry = tool_registry or ToolRegistry()

    def evolve_capability(
        self,
        pattern: Dict,
        missing_capabilities: List[str],
        automation_potential: float,
        auto_approve: bool = True
    ) -> EvolutionResult:
        """
        Execute full evolution cycle for a pattern.

        Args:
            pattern: Pattern dictionary with 'name' and 'description'
            missing_capabilities: List of missing capability descriptions
            automation_potential: 0.0-1.0 score of how automatable this is
            auto_approve: Whether to use bypass rules (default: True)

        Returns:
            EvolutionResult with outcome of evolution attempt
        """
        pattern_name = pattern['name']

        try:
            # Step 1: Analyze build vs buy
            recommendation = self.analyzer.analyze(
                pattern_name=pattern_name,
                missing_capabilities=missing_capabilities,
                automation_potential=automation_potential
            )

            # Step 2: Check approval requirements
            needs_approval = self.workflow.needs_approval(recommendation)

            if needs_approval and not auto_approve:
                # Require human approval
                approval = self.workflow.request_approval(recommendation, pattern_name)

                if not approval.approved:
                    return EvolutionResult(
                        pattern_name=pattern_name,
                        tool_acquired=False,
                        error="Rejected by user"
                    )
            else:
                # Auto-approve (bypass rules met)
                if needs_approval and auto_approve:
                    # User wants auto-approval but it requires approval
                    # Request approval anyway for safety
                    approval = self.workflow.request_approval(recommendation, pattern_name)

                    if not approval.approved:
                        return EvolutionResult(
                            pattern_name=pattern_name,
                            tool_acquired=False,
                            error="Rejected by user"
                        )
                else:
                    # Bypass conditions met - auto-approve
                    approval = self.workflow.approve_with_bypass(recommendation)

            # Step 3: Acquire tool
            tool = self.engine.acquire_tool(pattern, recommendation, approval)

            # Step 4: Save tool to file
            saved_path = self.engine.save_tool(tool)

            # Step 5: Register tool in pipeline
            self.tool_registry.register(tool, pattern_name)

            return EvolutionResult(
                pattern_name=pattern_name,
                tool_acquired=True,
                tool=tool,
                approval_bypassed=approval.auto_approved
            )

        except Exception as e:
            return EvolutionResult(
                pattern_name=pattern_name,
                tool_acquired=False,
                error=str(e)
            )

    def get_pipeline(
        self,
        gemini_api_key: Optional[str] = None
    ) -> UnifiedAgentPipeline:
        """
        Get UnifiedAgentPipeline with all registered tools.

        Args:
            gemini_api_key: Google API key (if different from engine's key)

        Returns:
            UnifiedAgentPipeline ready to process queries
        """
        return UnifiedAgentPipeline(
            gemini_api_key=gemini_api_key,
            tool_registry=self.tool_registry
        )

    def detect_gaps_from_query(
        self,
        query: str,
        code: Optional[str] = None
    ) -> List[Dict]:
        """
        Detect capability gaps from a user query.

        This is a simplified heuristic gap detector for CRAWL phase.
        In WALK phase, this will be replaced with ML-based gap detection.

        Args:
            query: User's question or request
            code: Optional code being analyzed

        Returns:
            List of gap dictionaries with pattern info and missing capabilities
        """
        query_lower = query.lower()
        gaps = []

        # Heuristic gap detection based on keywords
        # In practice, this would be more sophisticated (ML-based in WALK phase)

        # Gap 1: Production Readiness
        if any(kw in query_lower for kw in ['production', 'ready', 'deploy', 'quality']):
            gaps.append({
                'pattern': {
                    'name': 'Production Readiness',
                    'description': 'Check code for tests, type hints, error handling, and documentation'
                },
                'missing_capabilities': [
                    'Test coverage analysis',
                    'Type hint validation',
                    'Error handling patterns',
                    'Documentation completeness'
                ],
                'automation_potential': 0.9  # Highly automatable via AST analysis
            })

        # Gap 2: Security Analysis
        if any(kw in query_lower for kw in ['security', 'vulnerable', 'safe', 'exploit']):
            gaps.append({
                'pattern': {
                    'name': 'Security Analysis',
                    'description': 'Detect security vulnerabilities and unsafe patterns'
                },
                'missing_capabilities': [
                    'SQL injection detection',
                    'XSS vulnerability scanning',
                    'Unsafe deserialization checks',
                    'Authentication/authorization validation'
                ],
                'automation_potential': 0.85  # Automatable with pattern matching
            })

        # Gap 3: Performance Optimization
        if any(kw in query_lower for kw in ['performance', 'optimize', 'slow', 'faster']):
            gaps.append({
                'pattern': {
                    'name': 'Performance Optimization',
                    'description': 'Identify performance bottlenecks and optimization opportunities'
                },
                'missing_capabilities': [
                    'Complexity analysis (Big-O)',
                    'Memory usage profiling',
                    'N+1 query detection',
                    'Caching opportunities'
                ],
                'automation_potential': 0.7  # Some aspects need runtime profiling
            })

        return gaps

    def auto_evolve_from_query(
        self,
        query: str,
        code: Optional[str] = None,
        auto_approve: bool = True
    ) -> List[EvolutionResult]:
        """
        Detect gaps and automatically evolve capabilities.

        This is the full auto-evolution loop:
        1. Detect gaps from query
        2. For each gap, run evolution cycle
        3. Return results

        Args:
            query: User's question or request
            code: Optional code being analyzed
            auto_approve: Whether to use bypass rules (default: True)

        Returns:
            List of EvolutionResult for each gap detected
        """
        gaps = self.detect_gaps_from_query(query, code)
        results = []

        for gap in gaps:
            result = self.evolve_capability(
                pattern=gap['pattern'],
                missing_capabilities=gap['missing_capabilities'],
                automation_potential=gap['automation_potential'],
                auto_approve=auto_approve
            )
            results.append(result)

        return results


# Example usage and testing
if __name__ == "__main__":
    print("Capability Evolution Engine - Test Mode\n")

    # Initialize engine
    engine = CapabilityEvolutionEngine()

    # Test case 1: Manual evolution for Production Readiness
    print("=" * 80)
    print("Test 1: Manual Evolution - Production Readiness")
    print("=" * 80)

    pattern = {
        'name': 'Production Readiness',
        'description': 'Check code for tests, type hints, error handling, and documentation'
    }

    missing_capabilities = [
        'Test coverage analysis',
        'Type hint validation',
        'Error handling patterns',
        'Documentation completeness'
    ]

    result = engine.evolve_capability(
        pattern=pattern,
        missing_capabilities=missing_capabilities,
        automation_potential=0.9,
        auto_approve=True
    )

    print(f"\nPattern: {result.pattern_name}")
    print(f"Tool Acquired: {result.tool_acquired}")
    print(f"Auto-Approved: {result.approval_bypassed}")

    if result.tool_acquired:
        print(f"Tool Name: {result.tool.name}")
        print(f"Tool Type: {result.tool.acquisition_type}")
    elif result.error:
        print(f"Error: {result.error}")

    # Test case 2: Auto-evolution from query
    print("\n" + "=" * 80)
    print("Test 2: Auto-Evolution from Query")
    print("=" * 80)

    test_query = "Is this code production ready and secure?"
    print(f"\nQuery: {test_query}")

    # Detect gaps
    gaps = engine.detect_gaps_from_query(test_query)
    print(f"\nDetected {len(gaps)} capability gaps:")
    for i, gap in enumerate(gaps, 1):
        print(f"  {i}. {gap['pattern']['name']}")
        print(f"     Automation potential: {gap['automation_potential']:.0%}")

    # Auto-evolve (but skip actual tool acquisition for demo)
    print("\n" + "-" * 80)
    print("Auto-evolution would acquire tools for each gap.")
    print("Skipping actual acquisition to avoid API costs in test...")

    # Test case 3: Get pipeline with registered tools
    print("\n" + "=" * 80)
    print("Test 3: Get Unified Agent Pipeline")
    print("=" * 80)

    pipeline = engine.get_pipeline()

    print(f"\nPipeline created with {len(engine.tool_registry.tools)} pattern(s) registered:")
    for pattern_name in engine.tool_registry.tools.keys():
        tool_count = len(engine.tool_registry.tools[pattern_name])
        print(f"  - {pattern_name}: {tool_count} tool(s)")

    print("\n" + "=" * 80)
