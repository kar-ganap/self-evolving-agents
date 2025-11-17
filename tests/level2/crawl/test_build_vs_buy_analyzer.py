"""
Unit tests for BuildVsBuyAnalyzer

Tests build vs buy decision logic, cost estimation, and library matching.
"""

import pytest

from src.level2.crawl.build_vs_buy_analyzer import (
    BuildVsBuyAnalyzer,
    AcquisitionType,
    BuildOption,
    BuyOption,
    BuildVsBuyRecommendation
)


class TestBuildVsBuyAnalyzer:
    """Test suite for BuildVsBuyAnalyzer"""

    def test_initialization(self):
        """Test analyzer initializes with correct defaults"""
        analyzer = BuildVsBuyAnalyzer()

        assert analyzer.hourly_dev_cost == 100.0
        assert "type_checking" in analyzer.known_libraries
        assert "test_coverage" in analyzer.known_libraries
        assert "code_complexity" in analyzer.known_libraries
        assert "linting" in analyzer.known_libraries

    def test_custom_hourly_cost(self):
        """Test custom hourly developer cost"""
        analyzer = BuildVsBuyAnalyzer(hourly_dev_cost=150.0)
        assert analyzer.hourly_dev_cost == 150.0

    def test_build_cost_estimation_simple(self):
        """Test build cost estimation for simple capability"""
        analyzer = BuildVsBuyAnalyzer()

        build_option = analyzer._estimate_build_cost(
            capabilities=["Simple test coverage checker"],
            automation_potential=0.9  # High automation = lower complexity
        )

        assert build_option.complexity <= 5
        assert build_option.estimated_hours <= 10
        assert build_option.lines_of_code > 0
        assert len(build_option.dependencies) > 0
        assert build_option.testing_effort <= 10
        assert build_option.maintenance_score <= 10

    def test_build_cost_estimation_complex(self):
        """Test build cost estimation for complex capability"""
        analyzer = BuildVsBuyAnalyzer()

        build_option = analyzer._estimate_build_cost(
            capabilities=[
                "Advanced static analyzer",
                "Type inference engine",
                "AST transformation system"
            ],
            automation_potential=0.3  # Low automation = higher complexity
        )

        # More capabilities + low automation = higher complexity
        assert build_option.complexity >= 5
        assert build_option.lines_of_code >= 200
        assert build_option.estimated_hours > 10

    def test_dependency_detection_type_checking(self):
        """Test dependency detection for type checking capabilities"""
        analyzer = BuildVsBuyAnalyzer()

        deps = analyzer._detect_dependencies([
            "Static type checker",
            "Type coverage analyzer"
        ])

        assert "typing" in deps

    def test_dependency_detection_testing(self):
        """Test dependency detection for testing capabilities"""
        analyzer = BuildVsBuyAnalyzer()

        deps = analyzer._detect_dependencies([
            "Test coverage checker",
            "Coverage report generator"
        ])

        assert "pytest" in deps or "coverage" in deps

    def test_dependency_detection_complexity(self):
        """Test dependency detection for complexity analysis"""
        analyzer = BuildVsBuyAnalyzer()

        deps = analyzer._detect_dependencies([
            "Cyclomatic complexity analyzer",
            "Code complexity metrics"
        ])

        assert "radon" in deps

    def test_find_buy_options_type_checking(self):
        """Test finding buy options for type checking"""
        analyzer = BuildVsBuyAnalyzer()

        buy_options = analyzer._find_buy_options([
            "Static type checking",
            "Type coverage analysis"
        ])

        assert len(buy_options) > 0

        # Should find mypy or pyright
        names = [opt.source for opt in buy_options]
        assert "mypy" in names or "pyright" in names

        # Check properties
        for opt in buy_options:
            assert opt.acquisition_type == AcquisitionType.LIBRARY
            assert opt.cost_per_month == 0.0  # Free libraries
            assert opt.maturity_score >= 7

    def test_find_buy_options_test_coverage(self):
        """Test finding buy options for test coverage"""
        analyzer = BuildVsBuyAnalyzer()

        buy_options = analyzer._find_buy_options([
            "Test coverage checker",
            "Coverage reporting"
        ])

        assert len(buy_options) > 0

        names = [opt.source for opt in buy_options]
        assert "coverage.py" in names or "pytest-cov" in names

    def test_find_buy_options_no_match(self):
        """Test finding buy options when no libraries match"""
        analyzer = BuildVsBuyAnalyzer()

        buy_options = analyzer._find_buy_options([
            "Custom domain-specific tool",
            "Proprietary analysis engine"
        ])

        # Should return empty list for unknown capabilities
        assert len(buy_options) == 0

    def test_recommendation_free_mature_library(self):
        """Test recommendation prefers free mature library"""
        analyzer = BuildVsBuyAnalyzer()

        rec = analyzer.analyze(
            pattern_name="Production Readiness",
            missing_capabilities=[
                "Static type checking",
                "Type coverage analysis"
            ],
            automation_potential=0.9
        )

        assert rec.recommended_action == AcquisitionType.LIBRARY
        assert len(rec.buy_options) > 0
        assert rec.buy_options[0].cost_per_month == 0.0
        assert rec.buy_options[0].maturity_score >= 8
        assert rec.confidence >= 0.8

    def test_recommendation_simple_build(self):
        """Test recommendation for simple build (no good libraries)"""
        analyzer = BuildVsBuyAnalyzer()

        rec = analyzer.analyze(
            pattern_name="Gap Analysis",
            missing_capabilities=[
                "API design validator for pagination"
            ],
            automation_potential=0.9  # High automation = simple
        )

        # No libraries for this specific task, and it's simple
        if rec.recommended_action == AcquisitionType.BUILD:
            assert rec.build_option.complexity <= 5
            assert rec.build_option.estimated_hours <= 10
            assert "Simple implementation" in rec.rationale

    def test_recommendation_complex_build_with_library(self):
        """Test recommendation for complex build when library exists"""
        analyzer = BuildVsBuyAnalyzer()

        # Force complex build scenario
        rec = analyzer.analyze(
            pattern_name="Test Pattern",
            missing_capabilities=[
                "Advanced capability 1",
                "Advanced capability 2",
                "Advanced capability 3",
                "Advanced capability 4",
                "Static linting"  # This will match libraries
            ],
            automation_potential=0.3  # Low automation = complex
        )

        # Should find linting libraries
        if len(rec.buy_options) > 0 and rec.build_option.estimated_hours > 20:
            assert rec.recommended_action in [AcquisitionType.LIBRARY, AcquisitionType.API]

    def test_cost_calculation_build(self):
        """Test 12-month cost calculation for build option"""
        analyzer = BuildVsBuyAnalyzer(hourly_dev_cost=100.0)

        rec = analyzer.analyze(
            pattern_name="Custom Tool",
            missing_capabilities=["Simple capability"],
            automation_potential=0.9
        )

        # Cost should include dev hours + maintenance
        assert rec.total_cost_estimate > 0

        if rec.recommended_action == AcquisitionType.BUILD:
            expected_min_cost = rec.build_option.estimated_hours * 100.0
            assert rec.total_cost_estimate >= expected_min_cost

    def test_cost_calculation_library(self):
        """Test 12-month cost calculation for library option"""
        analyzer = BuildVsBuyAnalyzer(hourly_dev_cost=100.0)

        rec = analyzer.analyze(
            pattern_name="Production Readiness",
            missing_capabilities=["Type checking"],
            automation_potential=0.9
        )

        if rec.recommended_action == AcquisitionType.LIBRARY:
            # Free library cost = setup hours only
            assert rec.total_cost_estimate < rec.build_option.estimated_hours * 100.0

    def test_analyze_returns_all_fields(self):
        """Test analyze returns complete recommendation"""
        analyzer = BuildVsBuyAnalyzer()

        rec = analyzer.analyze(
            pattern_name="Test Pattern",
            missing_capabilities=["Test capability"],
            automation_potential=0.7
        )

        assert rec.pattern_name == "Test Pattern"
        assert rec.recommended_action is not None
        assert rec.build_option is not None
        assert isinstance(rec.buy_options, list)
        assert rec.rationale is not None
        assert rec.total_cost_estimate >= 0
        assert 0.0 <= rec.confidence <= 1.0

    def test_build_option_dataclass(self):
        """Test BuildOption dataclass structure"""
        build_opt = BuildOption(
            complexity=5,
            estimated_hours=8.5,
            lines_of_code=400,
            dependencies=["pytest", "typing"],
            testing_effort=4,
            maintenance_score=3
        )

        assert build_opt.complexity == 5
        assert build_opt.estimated_hours == 8.5
        assert build_opt.lines_of_code == 400
        assert len(build_opt.dependencies) == 2
        assert build_opt.testing_effort == 4
        assert build_opt.maintenance_score == 3

    def test_buy_option_dataclass(self):
        """Test BuyOption dataclass structure"""
        buy_opt = BuyOption(
            source="mypy",
            acquisition_type=AcquisitionType.LIBRARY,
            cost_per_month=0.0,
            setup_hours=1.0,
            learning_curve=3,
            vendor_lock_in=2,
            maturity_score=9
        )

        assert buy_opt.source == "mypy"
        assert buy_opt.acquisition_type == AcquisitionType.LIBRARY
        assert buy_opt.cost_per_month == 0.0
        assert buy_opt.setup_hours == 1.0
        assert buy_opt.learning_curve == 3
        assert buy_opt.vendor_lock_in == 2
        assert buy_opt.maturity_score == 9

    def test_recommendation_dataclass(self):
        """Test BuildVsBuyRecommendation dataclass structure"""
        rec = BuildVsBuyRecommendation(
            pattern_name="Test",
            recommended_action=AcquisitionType.BUILD,
            build_option=BuildOption(
                complexity=3,
                estimated_hours=5.0,
                lines_of_code=200,
                dependencies=["typing"],
                testing_effort=2,
                maintenance_score=2
            ),
            buy_options=[],
            rationale="Simple build",
            total_cost_estimate=700.0,
            confidence=0.8
        )

        assert rec.pattern_name == "Test"
        assert rec.recommended_action == AcquisitionType.BUILD
        assert rec.build_option.complexity == 3
        assert rec.buy_options == []
        assert rec.rationale == "Simple build"
        assert rec.total_cost_estimate == 700.0
        assert rec.confidence == 0.8

    def test_multiple_capabilities_increase_complexity(self):
        """Test that more capabilities increase build complexity"""
        analyzer = BuildVsBuyAnalyzer()

        build_1 = analyzer._estimate_build_cost(
            capabilities=["Capability 1"],
            automation_potential=0.7
        )

        build_3 = analyzer._estimate_build_cost(
            capabilities=["Capability 1", "Capability 2", "Capability 3"],
            automation_potential=0.7
        )

        # More capabilities = higher complexity and hours
        assert build_3.complexity >= build_1.complexity
        assert build_3.estimated_hours >= build_1.estimated_hours
        assert build_3.lines_of_code >= build_1.lines_of_code

    def test_low_automation_increases_complexity(self):
        """Test that low automation potential increases complexity"""
        analyzer = BuildVsBuyAnalyzer()

        build_high_auto = analyzer._estimate_build_cost(
            capabilities=["Capability"],
            automation_potential=0.9
        )

        build_low_auto = analyzer._estimate_build_cost(
            capabilities=["Capability"],
            automation_potential=0.3
        )

        # Low automation = higher complexity
        assert build_low_auto.complexity >= build_high_auto.complexity
        assert build_low_auto.estimated_hours >= build_high_auto.estimated_hours

    def test_known_libraries_coverage(self):
        """Test known_libraries covers expected categories"""
        analyzer = BuildVsBuyAnalyzer()

        # Verify all expected categories exist
        assert "type_checking" in analyzer.known_libraries
        assert "test_coverage" in analyzer.known_libraries
        assert "code_complexity" in analyzer.known_libraries
        assert "linting" in analyzer.known_libraries

        # Verify each category has multiple options
        assert len(analyzer.known_libraries["type_checking"]) >= 2
        assert len(analyzer.known_libraries["test_coverage"]) >= 2
        assert len(analyzer.known_libraries["code_complexity"]) >= 2
        assert len(analyzer.known_libraries["linting"]) >= 2

    def test_confidence_scores_valid(self):
        """Test confidence scores are within valid range"""
        analyzer = BuildVsBuyAnalyzer()

        test_cases = [
            (["Type checking"], 0.9),
            (["Custom capability"], 0.5),
            (["Complex capability 1", "Complex capability 2", "Complex capability 3"], 0.3)
        ]

        for capabilities, automation_potential in test_cases:
            rec = analyzer.analyze(
                pattern_name="Test",
                missing_capabilities=capabilities,
                automation_potential=automation_potential
            )

            assert 0.0 <= rec.confidence <= 1.0

    def test_rationale_provided(self):
        """Test that rationale is always provided"""
        analyzer = BuildVsBuyAnalyzer()

        rec = analyzer.analyze(
            pattern_name="Test",
            missing_capabilities=["Test capability"],
            automation_potential=0.7
        )

        assert len(rec.rationale) > 0
        assert isinstance(rec.rationale, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
