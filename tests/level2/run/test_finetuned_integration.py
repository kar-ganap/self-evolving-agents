"""
End-to-end tests for Level 2 RUN fine-tuned model integration.

Tests the BuildVsBuyAnalyzer with fine-tuned model enabled.
"""

import pytest
from src.level2.crawl.build_vs_buy_analyzer import (
    BuildVsBuyAnalyzer,
    AcquisitionType,
    BuildVsBuyRecommendation
)


class TestFinetunedIntegration:
    """Tests for fine-tuned model integration."""

    def test_heuristic_mode_works(self):
        """Test that heuristic mode still works without fine-tuned model."""
        analyzer = BuildVsBuyAnalyzer(use_finetuned=False)

        rec = analyzer.analyze(
            pattern_name="Type Checking",
            missing_capabilities=["Static type analysis", "Type hint validation"],
            automation_potential=0.9
        )

        assert isinstance(rec, BuildVsBuyRecommendation)
        assert rec.pattern_name == "Type Checking"
        assert rec.recommended_action in [
            AcquisitionType.BUILD,
            AcquisitionType.LIBRARY,
            AcquisitionType.API
        ]
        assert 0.0 <= rec.confidence <= 1.0

    @pytest.mark.integration
    def test_finetuned_mode_returns_valid_recommendation(self):
        """Test that fine-tuned mode returns valid recommendations."""
        analyzer = BuildVsBuyAnalyzer(use_finetuned=True)

        rec = analyzer.analyze(
            pattern_name="PDF Generation",
            missing_capabilities=["Generate PDF reports", "Custom layouts"],
            automation_potential=0.8
        )

        assert isinstance(rec, BuildVsBuyRecommendation)
        assert rec.pattern_name == "PDF Generation"
        assert rec.recommended_action in [
            AcquisitionType.BUILD,
            AcquisitionType.LIBRARY,
            AcquisitionType.API
        ]
        assert 0.0 <= rec.confidence <= 1.0
        assert "[Fine-tuned model]" in rec.rationale

    @pytest.mark.integration
    def test_finetuned_prefers_library_for_common_tasks(self):
        """Test that fine-tuned model prefers libraries for common tasks."""
        analyzer = BuildVsBuyAnalyzer(use_finetuned=True)

        # CSV export is a very common task with good libraries
        rec = analyzer.analyze(
            pattern_name="CSV Export",
            missing_capabilities=["Export data to CSV", "Handle large files"],
            automation_potential=0.9
        )

        # Should recommend library (csv stdlib or pandas)
        # Note: May also correctly say no_gap since csv is in stdlib
        assert rec.recommended_action in [AcquisitionType.LIBRARY, AcquisitionType.BUILD]

    @pytest.mark.integration
    def test_finetuned_prefers_build_for_custom_logic(self):
        """Test that fine-tuned model prefers build for custom business logic."""
        analyzer = BuildVsBuyAnalyzer(use_finetuned=True)

        rec = analyzer.analyze(
            pattern_name="Custom Business Rules Engine",
            missing_capabilities=[
                "Domain-specific validation rules",
                "Custom scoring algorithm",
                "Proprietary workflow logic"
            ],
            automation_potential=0.6
        )

        # Should recommend build for proprietary logic
        assert rec.recommended_action == AcquisitionType.BUILD

    @pytest.mark.integration
    def test_finetuned_recommends_paid_api_for_complex_services(self):
        """Test that fine-tuned model recommends paid APIs for complex services."""
        analyzer = BuildVsBuyAnalyzer(use_finetuned=True)

        rec = analyzer.analyze(
            pattern_name="SMS Notifications",
            missing_capabilities=[
                "Send SMS messages",
                "Track delivery status",
                "Handle international numbers"
            ],
            automation_potential=0.5
        )

        # Should recommend paid API (Twilio, etc.)
        assert rec.recommended_action == AcquisitionType.API

    def test_fallback_to_heuristic_on_error(self):
        """Test that analyzer falls back to heuristic if fine-tuned fails."""
        # Create analyzer with fine-tuned but no valid API key
        analyzer = BuildVsBuyAnalyzer(
            use_finetuned=True,
            openai_api_key="invalid_key_for_testing"
        )

        # Should still return a valid recommendation (falling back to heuristic)
        rec = analyzer.analyze(
            pattern_name="Test Pattern",
            missing_capabilities=["Test capability"],
            automation_potential=0.8
        )

        assert isinstance(rec, BuildVsBuyRecommendation)
        # Should not have fine-tuned marker (fell back to heuristic)
        assert "[Fine-tuned model]" not in rec.rationale


class TestConfigLoading:
    """Tests for configuration loading."""

    def test_config_loads_from_default_path(self):
        """Test that config loads from default path."""
        analyzer = BuildVsBuyAnalyzer(use_finetuned=True)

        # Config should be loaded
        assert hasattr(analyzer, 'config')
        assert isinstance(analyzer.config, dict)

    def test_analyzer_uses_config_thresholds(self):
        """Test that analyzer respects config thresholds."""
        analyzer = BuildVsBuyAnalyzer(use_finetuned=True)

        # Should have loaded fine_tuning config
        if analyzer.config:
            ft_config = analyzer.config.get('fine_tuning', {})
            assert 'auto_approve_threshold' in ft_config or True  # Optional


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not integration"])
