"""
Approval Workflow - Human-in-loop approval for tool acquisition

Manages approval decisions for building or buying tools based on configurable
bypass and require-approval rules.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import yaml

from src.level2.crawl.build_vs_buy_analyzer import (
    BuildVsBuyRecommendation,
    AcquisitionType
)


@dataclass
class ApprovalResponse:
    """
    Response from approval process.

    Attributes:
        approved: Whether the acquisition was approved
        selected_option: 'build' or name of buy option (e.g., 'mypy')
        auto_approved: Whether this was auto-approved via bypass rules
        notes: Optional notes about the decision
    """
    approved: bool
    selected_option: str  # 'build' or name of buy option
    auto_approved: bool
    notes: Optional[str] = None


class ApprovalWorkflow:
    """
    Manages human-in-loop approval for tool acquisition.

    Bypass rules (configurable):
    - Free libraries (no API costs)
    - Internal code generation (no external dependencies)
    - Cost < $10/month AND implementation time < 1 hour

    Require approval:
    - Any subscription cost
    - External API dependencies
    - Complex build (>1 day implementation)
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the approval workflow.

        Args:
            config_path: Path to approval_settings.yaml
                        If None, uses default: config/approval_settings.yaml
        """
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            config_path = project_root / "config/approval_settings.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def needs_approval(
        self,
        recommendation: BuildVsBuyRecommendation
    ) -> bool:
        """
        Check if this recommendation needs human approval.

        Args:
            recommendation: BuildVsBuyRecommendation from analyzer

        Returns:
            True if approval required, False if can proceed automatically
        """
        # Check bypass conditions first (highest priority)
        if self._check_bypass_conditions(recommendation):
            return False  # Auto-approve

        # Check require approval conditions
        if self._check_require_approval(recommendation):
            return True  # Needs approval

        # Default: require approval for safety
        return True

    def _check_bypass_conditions(
        self,
        recommendation: BuildVsBuyRecommendation
    ) -> bool:
        """
        Check if recommendation meets any bypass conditions for auto-approval.

        Returns:
            True if should bypass approval, False otherwise
        """
        bypass_rules = self.config['approval_rules']['bypass_conditions']

        # Check for free library bypass
        if recommendation.recommended_action == AcquisitionType.LIBRARY:
            for rule in bypass_rules:
                if rule['type'] == 'free_library':
                    # Check if it's a free library
                    if recommendation.buy_options:
                        selected = recommendation.buy_options[0]
                        if selected.cost_per_month == 0.0:
                            return True  # Auto-approve free libraries

        # Check for simple build bypass
        if recommendation.recommended_action == AcquisitionType.BUILD:
            build_option = recommendation.build_option

            for rule in bypass_rules:
                if rule['type'] == 'internal_code':
                    # Check complexity (using scale 1-10 -> 0.1-1.0)
                    complexity_normalized = build_option.complexity / 10.0
                    if complexity_normalized <= rule['max_complexity_score']:
                        return True  # Auto-approve simple builds

                if rule['type'] == 'low_cost':
                    # Check time and cost constraints
                    time_hours = build_option.estimated_hours
                    time_ok = (time_hours * 3600) <= rule['max_implementation_time']

                    # Use total cost estimate instead of just build cost
                    cost_ok = recommendation.total_cost_estimate <= rule['max_monthly_cost']

                    if time_ok or cost_ok:  # OR condition: low cost OR quick
                        return True  # Auto-approve low-cost builds

        return False

    def _check_require_approval(
        self,
        recommendation: BuildVsBuyRecommendation
    ) -> bool:
        """
        Check if recommendation meets any conditions that require approval.

        Returns:
            True if approval required, False otherwise
        """
        require_rules = self.config['approval_rules']['require_approval']

        for rule in require_rules:
            # Check for subscription costs
            if rule['type'] == 'subscription':
                if recommendation.buy_options:
                    for option in recommendation.buy_options:
                        if option.cost_per_month > 0:
                            return True  # Requires approval

            # Check for external API (implied by buy_options with monthly cost)
            if rule['type'] == 'external_api':
                if recommendation.recommended_action == AcquisitionType.API:
                    return True

            # Check for complex builds
            if rule['type'] == 'complex_build':
                if recommendation.recommended_action == AcquisitionType.BUILD:
                    build_option = recommendation.build_option
                    time_limit = rule['min_implementation_time']
                    if (build_option.estimated_hours * 3600) >= time_limit:
                        return True  # Requires approval for complex builds

            # Check for high cost
            if rule['type'] == 'high_cost':
                if recommendation.buy_options:
                    for option in recommendation.buy_options:
                        if option.cost_per_month >= rule['monthly_cost']:
                            return True

        return False

    def request_approval(
        self,
        recommendation: BuildVsBuyRecommendation,
        pattern_name: str
    ) -> ApprovalResponse:
        """
        Present recommendation to human for approval via CLI.

        Args:
            recommendation: BuildVsBuyRecommendation from analyzer
            pattern_name: Name of the pattern needing this tool

        Returns:
            ApprovalResponse with user's decision
        """
        print("\n" + "="*80)
        print("TOOL ACQUISITION APPROVAL REQUEST")
        print("="*80)
        print(f"\nPattern: {pattern_name}")
        print(f"\nRecommendation: {recommendation.recommended_action.value.upper()}")
        print(f"Confidence: {recommendation.confidence:.0%}")
        print(f"\nRationale:\n{recommendation.rationale}")

        print("\n" + "-"*80)
        print("COST ANALYSIS (12-month total):")
        print(f"  Recommended option: ${recommendation.total_cost_estimate:.2f}")

        if recommendation.build_option:
            print("\n" + "-"*80)
            print("BUILD OPTION:")
            print(f"  Time: {recommendation.build_option.estimated_hours:.1f} hours")
            print(f"  Complexity: {recommendation.build_option.complexity}/10")
            print(f"  LOC: ~{recommendation.build_option.lines_of_code}")
            print(f"  Dependencies: {', '.join(recommendation.build_option.dependencies)}")

        if recommendation.buy_options:
            print("\n" + "-"*80)
            print("EXTERNAL OPTIONS:")
            for i, option in enumerate(recommendation.buy_options, 1):
                print(f"\n  {i}. {option.source} ({option.acquisition_type.value})")
                print(f"     Cost: ${option.cost_per_month:.2f}/month")
                print(f"     Setup: {option.setup_hours:.1f} hours")
                print(f"     Maturity: {option.maturity_score}/10")

        print("\n" + "="*80)
        print("APPROVE THIS ACQUISITION?")
        print("  [y] Yes, proceed with recommendation")
        print("  [b] Choose BUILD option")
        if recommendation.buy_options:
            for i in range(len(recommendation.buy_options)):
                print(f"  [{i+1}] Choose external option {i+1}")
        print("  [n] No, cancel")
        print("="*80)

        choice = input("\nYour choice: ").strip().lower()

        if choice == 'y':
            # Approve recommended option
            if recommendation.recommended_action == AcquisitionType.BUILD:
                selected = 'build'
            else:
                selected = recommendation.buy_options[0].source if recommendation.buy_options else 'build'

            return ApprovalResponse(
                approved=True,
                selected_option=selected,
                auto_approved=False,
                notes="Approved by user"
            )

        elif choice == 'b':
            return ApprovalResponse(
                approved=True,
                selected_option='build',
                auto_approved=False,
                notes="User selected BUILD option"
            )

        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(recommendation.buy_options):
                return ApprovalResponse(
                    approved=True,
                    selected_option=recommendation.buy_options[idx].source,
                    auto_approved=False,
                    notes=f"User selected {recommendation.buy_options[idx].source}"
                )

        # Default: reject
        return ApprovalResponse(
            approved=False,
            selected_option='',
            auto_approved=False,
            notes="Rejected by user"
        )

    def approve_with_bypass(
        self,
        recommendation: BuildVsBuyRecommendation
    ) -> ApprovalResponse:
        """
        Create auto-approval response for recommendations that pass bypass rules.

        Args:
            recommendation: BuildVsBuyRecommendation from analyzer

        Returns:
            ApprovalResponse with auto_approved=True
        """
        if recommendation.recommended_action == AcquisitionType.BUILD:
            selected = 'build'
            reason = "Auto-approved: simple build"
        else:
            selected = recommendation.buy_options[0].source if recommendation.buy_options else 'build'
            reason = "Auto-approved: free library"

        return ApprovalResponse(
            approved=True,
            selected_option=selected,
            auto_approved=True,
            notes=reason
        )


# Example usage and testing
if __name__ == "__main__":
    from src.level2.crawl.build_vs_buy_analyzer import (
        BuildVsBuyAnalyzer,
        BuildOption,
        BuyOption
    )

    print("Approval Workflow - Test Mode\n")

    workflow = ApprovalWorkflow()
    analyzer = BuildVsBuyAnalyzer()

    # Test case 1: Free library (should bypass approval)
    print("="*80)
    print("Test 1: Free library recommendation")
    print("="*80)

    rec1 = analyzer.analyze(
        pattern_name="Production Readiness",
        missing_capabilities=["Type checking", "Type coverage"],
        automation_potential=0.9
    )

    needs_approval = workflow.needs_approval(rec1)
    print(f"\nRecommendation: {rec1.recommended_action.value}")
    print(f"Needs approval: {needs_approval}")

    if not needs_approval:
        approval = workflow.approve_with_bypass(rec1)
        print(f"Auto-approved: {approval.auto_approved}")
        print(f"Selected: {approval.selected_option}")

    # Test case 2: Simple build (should bypass approval)
    print("\n" + "="*80)
    print("Test 2: Simple build recommendation")
    print("="*80)

    rec2 = analyzer.analyze(
        pattern_name="Gap Analysis",
        missing_capabilities=["Simple API validator"],
        automation_potential=0.9  # High automation = simple
    )

    needs_approval2 = workflow.needs_approval(rec2)
    print(f"\nRecommendation: {rec2.recommended_action.value}")
    print(f"Complexity: {rec2.build_option.complexity}/10")
    print(f"Needs approval: {needs_approval2}")

    print("\n" + "="*80)
