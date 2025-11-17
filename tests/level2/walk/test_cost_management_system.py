"""
Comprehensive Tests for Cost Management System

Tests all functionality:
1. Budget configuration and management
2. Cost recording and tracking
3. Budget enforcement
4. Alert system
5. Cost optimization recommendations
6. Analytics and forecasting
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from src.level2.walk.cost_management_system import (
    CostManagementSystem,
    Budget,
    BudgetPeriod,
    AlertLevel,
    CostAlert,
    CostOptimization
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test_cost_management.db"

    yield db_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def cost_system(temp_db):
    """Create a fresh CostManagementSystem for each test"""
    return CostManagementSystem(db_path=temp_db)


class TestBudgetManagement:
    """Test budget configuration and lifecycle"""

    def test_set_budget(self, cost_system):
        """Test setting a budget"""
        budget = cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        assert budget.period == BudgetPeriod.MONTHLY
        assert budget.limit == 100.0
        assert budget.current_spend == 0.0
        assert budget.remaining() == 100.0

    def test_multiple_budgets(self, cost_system):
        """Test setting budgets for multiple periods"""
        daily = cost_system.set_budget(BudgetPeriod.DAILY, 10.0)
        weekly = cost_system.set_budget(BudgetPeriod.WEEKLY, 50.0)
        monthly = cost_system.set_budget(BudgetPeriod.MONTHLY, 200.0)

        assert len(cost_system.budgets) == 3
        assert cost_system.budgets[BudgetPeriod.DAILY].limit == 10.0
        assert cost_system.budgets[BudgetPeriod.WEEKLY].limit == 50.0
        assert cost_system.budgets[BudgetPeriod.MONTHLY].limit == 200.0

    def test_budget_utilization(self, cost_system):
        """Test budget utilization calculation"""
        budget = cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        # 0% utilization initially
        assert budget.utilization_percent() == 0.0

        # Record some costs
        cost_system.record_cost(25.0, "api", "Test API call")

        # Check updated utilization
        budget = cost_system.budgets[BudgetPeriod.MONTHLY]
        assert budget.utilization_percent() == 25.0

    def test_budget_remaining(self, cost_system):
        """Test remaining budget calculation"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)
        cost_system.record_cost(30.0, "api")

        budget = cost_system.budgets[BudgetPeriod.MONTHLY]
        assert budget.remaining() == 70.0

    def test_budget_persistence(self, temp_db):
        """Test that budgets persist across instances"""
        # Create system and set budget
        system1 = CostManagementSystem(db_path=temp_db)
        system1.set_budget(BudgetPeriod.MONTHLY, 150.0)

        # Create new instance with same database
        system2 = CostManagementSystem(db_path=temp_db)

        # Budget should be loaded
        assert BudgetPeriod.MONTHLY in system2.budgets
        assert system2.budgets[BudgetPeriod.MONTHLY].limit == 150.0


class TestCostRecording:
    """Test cost recording functionality"""

    def test_record_simple_cost(self, cost_system):
        """Test recording a simple cost"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        success = cost_system.record_cost(
            amount=10.0,
            category="api",
            description="Test API call"
        )

        assert success == True

        # Check budget was updated
        budget = cost_system.budgets[BudgetPeriod.MONTHLY]
        assert budget.current_spend == 10.0

    def test_record_cost_with_metadata(self, cost_system):
        """Test recording cost with full metadata"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        success = cost_system.record_cost(
            amount=5.0,
            category="tool_generation",
            description="Gemini API call",
            tool_name="TestTool",
            pattern_name="Test Pattern",
            acquisition_type="api",
            metadata={'model': 'gemini-2.5-pro', 'tokens': 1000}
        )

        assert success == True

    def test_multiple_cost_recordings(self, cost_system):
        """Test recording multiple costs"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        costs = [10.0, 15.0, 20.0, 25.0]

        for cost in costs:
            success = cost_system.record_cost(cost, "api")
            assert success == True

        budget = cost_system.budgets[BudgetPeriod.MONTHLY]
        assert budget.current_spend == sum(costs)

    def test_cost_updates_all_budgets(self, cost_system):
        """Test that costs update all active budgets"""
        cost_system.set_budget(BudgetPeriod.DAILY, 10.0)
        cost_system.set_budget(BudgetPeriod.WEEKLY, 50.0)
        cost_system.set_budget(BudgetPeriod.MONTHLY, 200.0)

        cost_system.record_cost(5.0, "api")

        # All budgets should be updated
        assert cost_system.budgets[BudgetPeriod.DAILY].current_spend == 5.0
        assert cost_system.budgets[BudgetPeriod.WEEKLY].current_spend == 5.0
        assert cost_system.budgets[BudgetPeriod.MONTHLY].current_spend == 5.0


class TestBudgetEnforcement:
    """Test budget enforcement and blocking"""

    def test_budget_allows_within_limit(self, cost_system):
        """Test that costs within budget are allowed"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        success = cost_system.record_cost(50.0, "api")
        assert success == True

    def test_budget_blocks_exceeding_limit(self, cost_system):
        """Test that costs exceeding budget are blocked"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        # First cost succeeds
        cost_system.record_cost(60.0, "api")

        # Second cost would exceed budget - should be blocked
        success = cost_system.record_cost(50.0, "api")
        assert success == False

        # Budget should not be updated
        budget = cost_system.budgets[BudgetPeriod.MONTHLY]
        assert budget.current_spend == 60.0  # Only first cost

    def test_budget_enforcement_across_periods(self, cost_system):
        """Test enforcement across multiple budget periods"""
        cost_system.set_budget(BudgetPeriod.DAILY, 10.0)
        cost_system.set_budget(BudgetPeriod.MONTHLY, 200.0)

        # Cost within monthly but exceeds daily - should be blocked
        success = cost_system.record_cost(15.0, "api")
        assert success == False

    def test_exact_budget_limit(self, cost_system):
        """Test cost exactly at budget limit"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        # Record up to limit
        cost_system.record_cost(60.0, "api")
        success = cost_system.record_cost(40.0, "api")

        assert success == True

        budget = cost_system.budgets[BudgetPeriod.MONTHLY]
        assert budget.current_spend == 100.0


class TestAlertSystem:
    """Test cost alert generation"""

    def test_no_alerts_below_threshold(self, cost_system):
        """Test no alerts when below 80% threshold"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)
        cost_system.record_cost(70.0, "api")

        alerts = cost_system.get_recent_alerts()
        assert len(alerts) == 0

    def test_warning_alert_at_80_percent(self, cost_system):
        """Test warning alert at 80% utilization"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)
        cost_system.record_cost(85.0, "api")

        alerts = cost_system.get_recent_alerts()
        assert len(alerts) > 0
        assert any(a.level == AlertLevel.WARNING for a in alerts)

    def test_critical_alert_at_95_percent(self, cost_system):
        """Test critical alert at 95% utilization"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)
        cost_system.record_cost(97.0, "api")

        alerts = cost_system.get_recent_alerts()
        assert len(alerts) > 0
        assert any(a.level == AlertLevel.CRITICAL for a in alerts)

    def test_alert_on_blocked_transaction(self, cost_system):
        """Test alert when transaction is blocked"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        # Block a transaction
        cost_system.record_cost(90.0, "api")
        cost_system.record_cost(20.0, "api")  # Blocked

        alerts = cost_system.get_recent_alerts()
        assert any("blocked" in a.message.lower() for a in alerts)


class TestBudgetStatus:
    """Test budget status reporting"""

    def test_get_budget_status(self, cost_system):
        """Test getting current budget status"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)
        cost_system.record_cost(25.0, "api")

        status = cost_system.get_budget_status()

        assert 'monthly' in status
        assert status['monthly']['limit'] == 100.0
        assert status['monthly']['current_spend'] == 25.0
        assert status['monthly']['remaining'] == 75.0
        assert status['monthly']['utilization_percent'] == 25.0

    def test_budget_status_all_periods(self, cost_system):
        """Test status for all budget periods"""
        cost_system.set_budget(BudgetPeriod.DAILY, 10.0)
        cost_system.set_budget(BudgetPeriod.WEEKLY, 50.0)
        cost_system.set_budget(BudgetPeriod.MONTHLY, 200.0)

        cost_system.record_cost(5.0, "api")

        status = cost_system.get_budget_status()

        assert len(status) == 3
        assert 'daily' in status
        assert 'weekly' in status
        assert 'monthly' in status

        # All should show same spend
        assert status['daily']['current_spend'] == 5.0
        assert status['weekly']['current_spend'] == 5.0
        assert status['monthly']['current_spend'] == 5.0


class TestAnalytics:
    """Test cost analytics and reporting"""

    def test_spending_by_category(self, cost_system):
        """Test spending breakdown by category"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        cost_system.record_cost(10.0, "api")
        cost_system.record_cost(15.0, "api")
        cost_system.record_cost(5.0, "tool_generation")
        cost_system.record_cost(20.0, "library")

        spending = cost_system.get_spending_by_category(days=30)

        assert spending['api'] == 25.0
        assert spending['tool_generation'] == 5.0
        assert spending['library'] == 20.0

    def test_spending_time_window(self, cost_system):
        """Test spending analysis for specific time window"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        # Record costs
        cost_system.record_cost(10.0, "api")
        cost_system.record_cost(20.0, "library")

        # Get spending for last 7 days
        spending_7d = cost_system.get_spending_by_category(days=7)
        assert sum(spending_7d.values()) == 30.0

        # Get spending for last 1 day
        spending_1d = cost_system.get_spending_by_category(days=1)
        assert sum(spending_1d.values()) == 30.0

    def test_monthly_forecast(self, cost_system):
        """Test monthly spend forecasting"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 300.0)  # Higher budget

        # Record $7 per day for 7 days = $49 total
        for _ in range(7):
            cost_system.record_cost(7.0, "api")

        forecast = cost_system.forecast_monthly_spend()

        # Should forecast ~$210/month ($7/day * 30 days)
        # Note: Forecast extrapolates: (49 / 7) * 30 = 210
        assert 200.0 <= forecast <= 220.0  # Allow some margin


class TestOptimizationRecommendations:
    """Test cost optimization recommendation engine"""

    def test_high_api_cost_recommendation(self, cost_system):
        """Test recommendation for high API costs"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        # Record high API costs (>50% of total)
        cost_system.record_cost(60.0, "api")
        cost_system.record_cost(10.0, "tool_generation")

        recommendations = cost_system.get_optimization_recommendations()

        # Should recommend caching
        assert any("cach" in r.recommendation.lower() for r in recommendations)

    def test_high_generation_cost_recommendation(self, cost_system):
        """Test recommendation for high generation costs"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        # Record high generation costs (>30% of total)
        cost_system.record_cost(50.0, "tool_generation")
        cost_system.record_cost(30.0, "api")

        recommendations = cost_system.get_optimization_recommendations()

        # Should recommend cheaper models
        assert any("cheaper" in r.recommendation.lower() or "mini" in r.recommendation.lower()
                   for r in recommendations)

    def test_recommendation_priority_ordering(self, cost_system):
        """Test that recommendations are ordered by priority"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        cost_system.record_cost(40.0, "tool_generation")
        cost_system.record_cost(40.0, "api")

        recommendations = cost_system.get_optimization_recommendations()

        if len(recommendations) >= 2:
            # Higher priority should come first
            for i in range(len(recommendations) - 1):
                assert recommendations[i].priority >= recommendations[i+1].priority

    def test_no_recommendations_for_low_spend(self, cost_system):
        """Test no spurious recommendations for low spend"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        # Record minimal, balanced costs
        cost_system.record_cost(1.0, "api")
        cost_system.record_cost(1.0, "tool_generation")
        cost_system.record_cost(1.0, "library")

        recommendations = cost_system.get_optimization_recommendations()

        # Should still return default recommendations, but with low savings
        assert all(r.potential_savings < 5.0 for r in recommendations)


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_zero_budget_limit(self, cost_system):
        """Test budget with zero limit"""
        budget = cost_system.set_budget(BudgetPeriod.MONTHLY, 0.0)

        assert budget.limit == 0.0
        assert budget.remaining() == 0.0

        # Any cost should be blocked
        success = cost_system.record_cost(0.01, "api")
        assert success == False

    def test_negative_cost_handling(self, cost_system):
        """Test handling of negative costs (refunds)"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        # Record positive cost
        cost_system.record_cost(20.0, "api")

        # Record negative cost (refund) - should still be allowed
        success = cost_system.record_cost(-5.0, "api")

        # Note: Current implementation allows negative costs
        # This could be a refund scenario
        assert success == True

    def test_very_large_costs(self, cost_system):
        """Test handling of very large cost amounts"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 1000000.0)

        success = cost_system.record_cost(999999.0, "api")
        assert success == True

    def test_empty_spending_by_category(self, cost_system):
        """Test spending analysis with no costs"""
        spending = cost_system.get_spending_by_category(days=30)

        assert isinstance(spending, dict)
        assert len(spending) == 0

    def test_forecast_with_no_data(self, cost_system):
        """Test forecasting with no historical data"""
        forecast = cost_system.forecast_monthly_spend()

        assert forecast == 0.0


class TestIntegrationScenarios:
    """End-to-end integration scenarios"""

    def test_complete_cost_management_workflow(self, cost_system):
        """Test complete workflow: budget → spend → monitor → optimize"""
        # Step 1: Set budgets with sufficient room
        cost_system.set_budget(BudgetPeriod.DAILY, 20.0)  # Higher budget
        cost_system.set_budget(BudgetPeriod.MONTHLY, 200.0)

        # Step 2: Record costs over time
        transactions = [
            (5.0, "api", "Weather API"),
            (2.0, "tool_generation", "Generate wrapper"),
            (3.0, "library", "Premium lib subscription"),
            (1.5, "api", "Currency API"),
        ]

        for amount, category, desc in transactions:
            success = cost_system.record_cost(amount, category, desc)
            assert success == True

        # Step 3: Check budget status
        status = cost_system.get_budget_status()
        assert status['daily']['current_spend'] == 11.5  # Total spent

        # Step 4: Get spending breakdown
        spending = cost_system.get_spending_by_category(days=1)
        assert spending['api'] == 6.5
        assert spending['tool_generation'] == 2.0
        assert spending['library'] == 3.0

        # Step 5: Get optimization recommendations
        recommendations = cost_system.get_optimization_recommendations()
        assert len(recommendations) > 0

    def test_budget_enforcement_scenario(self, cost_system):
        """Test realistic budget enforcement scenario"""
        # Set tight daily budget
        cost_system.set_budget(BudgetPeriod.DAILY, 20.0)

        # Record costs throughout the day
        costs = [5.0, 6.0, 4.0, 3.0]  # Total: 18.0

        for cost in costs:
            success = cost_system.record_cost(cost, "api")
            assert success == True

        # Try to add one more cost that would exceed budget
        success = cost_system.record_cost(5.0, "api")
        assert success == False

        # Verify budget was not exceeded
        budget = cost_system.budgets[BudgetPeriod.DAILY]
        assert budget.current_spend == 18.0
        assert budget.remaining() == 2.0

    def test_multi_category_optimization(self, cost_system):
        """Test optimization recommendations across multiple categories"""
        cost_system.set_budget(BudgetPeriod.MONTHLY, 100.0)

        # Simulate unbalanced spending
        cost_system.record_cost(40.0, "api")  # High API costs
        cost_system.record_cost(35.0, "tool_generation")  # High generation costs
        cost_system.record_cost(10.0, "library")

        recommendations = cost_system.get_optimization_recommendations()

        # Should get recommendations for both high-cost categories
        assert len(recommendations) >= 2

        # Total potential savings should be significant
        total_savings = sum(r.potential_savings for r in recommendations)
        assert total_savings > 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
