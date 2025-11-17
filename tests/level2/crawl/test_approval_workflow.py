"""
Unit tests for ApprovalWorkflow

Tests approval bypass logic, require approval rules, and response handling.
"""

import pytest
import tempfile
from pathlib import Path

from src.level2.crawl.approval_workflow import (
    ApprovalWorkflow,
    ApprovalResponse
)
from src.level2.crawl.build_vs_buy_analyzer import (
    BuildVsBuyAnalyzer,
    BuildVsBuyRecommendation,
    BuildOption,
    BuyOption,
    AcquisitionType
)


class TestApprovalWorkflow:
    """Test suite for ApprovalWorkflow"""

    def test_initialization(self):
        """Test workflow initializes with default config"""
        workflow = ApprovalWorkflow()

        assert workflow.config is not None
        assert 'approval_rules' in workflow.config
        assert 'bypass_conditions' in workflow.config['approval_rules']
        assert 'require_approval' in workflow.config['approval_rules']

    def test_config_loading(self):
        """Test custom config path loading"""
        # Use default config
        workflow = ApprovalWorkflow()
        assert workflow.config['cost_settings']['hourly_dev_rate'] == 100.00

    def test_bypass_free_library(self):
        """Test free library bypasses approval"""
        workflow = ApprovalWorkflow()
        analyzer = BuildVsBuyAnalyzer()

        # Get recommendation for type checking (free library)
        rec = analyzer.analyze(
            pattern_name="Production Readiness",
            missing_capabilities=["Type checking"],
            automation_potential=0.9
        )

        # Should not need approval (free library)
        needs_approval = workflow.needs_approval(rec)
        assert needs_approval == False

    def test_bypass_simple_build(self):
        """Test simple build bypasses approval"""
        workflow = ApprovalWorkflow()
        analyzer = BuildVsBuyAnalyzer()

        # Get recommendation for simple capability
        rec = analyzer.analyze(
            pattern_name="Gap Analysis",
            missing_capabilities=["Simple validator"],
            automation_potential=0.9  # High automation = simple
        )

        # If it's a BUILD with low complexity, should bypass
        if rec.recommended_action == AcquisitionType.BUILD:
            if rec.build_option.complexity <= 5:
                needs_approval = workflow.needs_approval(rec)
                assert needs_approval == False

    def test_require_approval_complex_build(self):
        """Test complex build requires approval"""
        workflow = ApprovalWorkflow()

        # Create mock complex build recommendation
        complex_build = BuildVsBuyRecommendation(
            pattern_name="Complex Pattern",
            recommended_action=AcquisitionType.BUILD,
            build_option=BuildOption(
                complexity=9,
                estimated_hours=30.0,  # > 24 hours
                lines_of_code=1500,
                dependencies=["many", "dependencies"],
                testing_effort=8,
                maintenance_score=7
            ),
            buy_options=[],
            rationale="Complex build",
            total_cost_estimate=3000.0,
            confidence=0.7
        )

        needs_approval = workflow.needs_approval(complex_build)
        assert needs_approval == True

    def test_approval_response_dataclass(self):
        """Test ApprovalResponse structure"""
        response = ApprovalResponse(
            approved=True,
            selected_option='build',
            auto_approved=True,
            notes="Test auto-approval"
        )

        assert response.approved == True
        assert response.selected_option == 'build'
        assert response.auto_approved == True
        assert response.notes == "Test auto-approval"

    def test_approve_with_bypass_build(self):
        """Test auto-approval for build option"""
        workflow = ApprovalWorkflow()

        # Create simple build recommendation
        simple_build = BuildVsBuyRecommendation(
            pattern_name="Simple Pattern",
            recommended_action=AcquisitionType.BUILD,
            build_option=BuildOption(
                complexity=3,
                estimated_hours=2.0,
                lines_of_code=100,
                dependencies=["typing"],
                testing_effort=2,
                maintenance_score=2
            ),
            buy_options=[],
            rationale="Simple build",
            total_cost_estimate=200.0,
            confidence=0.8
        )

        approval = workflow.approve_with_bypass(simple_build)

        assert approval.approved == True
        assert approval.selected_option == 'build'
        assert approval.auto_approved == True

    def test_approve_with_bypass_library(self):
        """Test auto-approval for library option"""
        workflow = ApprovalWorkflow()

        # Create library recommendation
        lib_rec = BuildVsBuyRecommendation(
            pattern_name="Type Checking",
            recommended_action=AcquisitionType.LIBRARY,
            build_option=BuildOption(
                complexity=5,
                estimated_hours=10.0,
                lines_of_code=500,
                dependencies=["typing"],
                testing_effort=4,
                maintenance_score=5
            ),
            buy_options=[
                BuyOption(
                    source="mypy",
                    acquisition_type=AcquisitionType.LIBRARY,
                    cost_per_month=0.0,
                    setup_hours=1.0,
                    learning_curve=3,
                    vendor_lock_in=2,
                    maturity_score=9
                )
            ],
            rationale="Free library available",
            total_cost_estimate=100.0,
            confidence=0.9
        )

        approval = workflow.approve_with_bypass(lib_rec)

        assert approval.approved == True
        assert approval.selected_option == 'mypy'
        assert approval.auto_approved == True

    def test_bypass_conditions_check(self):
        """Test _check_bypass_conditions logic"""
        workflow = ApprovalWorkflow()

        # Test free library bypass
        free_lib = BuildVsBuyRecommendation(
            pattern_name="Test",
            recommended_action=AcquisitionType.LIBRARY,
            build_option=None,
            buy_options=[
                BuyOption(
                    source="pytest",
                    acquisition_type=AcquisitionType.LIBRARY,
                    cost_per_month=0.0,  # Free
                    setup_hours=0.5,
                    learning_curve=2,
                    vendor_lock_in=1,
                    maturity_score=10
                )
            ],
            rationale="Test",
            total_cost_estimate=50.0,
            confidence=0.9
        )

        assert workflow._check_bypass_conditions(free_lib) == True

    def test_require_approval_check(self):
        """Test _check_require_approval logic"""
        workflow = ApprovalWorkflow()

        # Test paid subscription requires approval
        paid_api = BuildVsBuyRecommendation(
            pattern_name="Test",
            recommended_action=AcquisitionType.API,
            build_option=None,
            buy_options=[
                BuyOption(
                    source="Paid API",
                    acquisition_type=AcquisitionType.API,
                    cost_per_month=50.0,  # Paid
                    setup_hours=2.0,
                    learning_curve=5,
                    vendor_lock_in=7,
                    maturity_score=8
                )
            ],
            rationale="Test",
            total_cost_estimate=600.0,
            confidence=0.7
        )

        assert workflow._check_require_approval(paid_api) == True

    def test_config_has_all_required_sections(self):
        """Test config has all required sections"""
        workflow = ApprovalWorkflow()

        assert 'approval_rules' in workflow.config
        assert 'notification' in workflow.config
        assert 'cost_settings' in workflow.config
        assert 'tool_generation' in workflow.config
        assert 'gap_detection' in workflow.config

    def test_bypass_low_cost_build(self):
        """Test low cost build bypasses approval"""
        workflow = ApprovalWorkflow()

        # Create low-cost build
        low_cost_build = BuildVsBuyRecommendation(
            pattern_name="Low Cost",
            recommended_action=AcquisitionType.BUILD,
            build_option=BuildOption(
                complexity=2,
                estimated_hours=0.5,  # 30 minutes
                lines_of_code=50,
                dependencies=["typing"],
                testing_effort=1,
                maintenance_score=1
            ),
            buy_options=[],
            rationale="Very simple",
            total_cost_estimate=5.0,  # < $10
            confidence=0.9
        )

        needs_approval = workflow.needs_approval(low_cost_build)
        assert needs_approval == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
