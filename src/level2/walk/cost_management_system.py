"""
Cost Management System - Budget tracking and optimization

Implements comprehensive cost management:
1. Budget tracking (daily, weekly, monthly)
2. Cost enforcement (block acquisitions exceeding budget)
3. Cost optimization recommendations
4. Spend analytics and forecasting
5. Alert system for approaching budget limits
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BudgetPeriod(Enum):
    """Budget period types"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Budget:
    """
    Budget configuration.

    Attributes:
        period: Budget period (daily, weekly, monthly)
        limit: Maximum spend allowed per period
        current_spend: Current spend in this period
        start_date: Period start date
        end_date: Period end date
    """
    period: BudgetPeriod
    limit: float
    current_spend: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def __post_init__(self):
        if self.start_date is None:
            self.start_date = datetime.now()
            self.end_date = self._calculate_end_date()

    def _calculate_end_date(self) -> datetime:
        """Calculate period end date based on period type"""
        if self.period == BudgetPeriod.DAILY:
            return self.start_date + timedelta(days=1)
        elif self.period == BudgetPeriod.WEEKLY:
            return self.start_date + timedelta(weeks=1)
        elif self.period == BudgetPeriod.MONTHLY:
            # Approximate: 30 days
            return self.start_date + timedelta(days=30)
        return self.start_date

    def remaining(self) -> float:
        """Calculate remaining budget"""
        return max(0.0, self.limit - self.current_spend)

    def utilization_percent(self) -> float:
        """Calculate budget utilization percentage"""
        if self.limit == 0:
            return 0.0
        return (self.current_spend / self.limit) * 100

    def is_expired(self) -> bool:
        """Check if budget period has expired"""
        return datetime.now() > self.end_date


@dataclass
class CostAlert:
    """
    Cost alert notification.

    Attributes:
        level: Alert severity
        message: Alert description
        budget_period: Affected budget period
        current_spend: Current spend
        budget_limit: Budget limit
        timestamp: When alert was generated
    """
    level: AlertLevel
    message: str
    budget_period: BudgetPeriod
    current_spend: float
    budget_limit: float
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class CostOptimization:
    """
    Cost optimization recommendation.

    Attributes:
        recommendation: Description of optimization
        potential_savings: Estimated monthly savings
        implementation_effort: Effort level (low, medium, high)
        priority: Priority score (0.0-1.0)
        details: Additional context
    """
    recommendation: str
    potential_savings: float
    implementation_effort: str
    priority: float
    details: Dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class CostManagementSystem:
    """
    Comprehensive cost management with budgets, enforcement, and optimization.

    Features:
    - Multi-period budgets (daily, weekly, monthly)
    - Budget enforcement (block/warn on overspend)
    - Cost tracking and analytics
    - Spend forecasting
    - Optimization recommendations
    - Alert system
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize cost management system.

        Args:
            db_path: Path to SQLite database (default: data/cost_management.db)
        """
        if db_path is None:
            project_root = self._find_project_root()
            db_path = project_root / "data" / "cost_management.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()
        self.budgets: Dict[BudgetPeriod, Budget] = {}
        self._load_budgets()

    def _find_project_root(self) -> Path:
        """Find project root by locating pyproject.toml"""
        current = Path(__file__).resolve()
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current
            current = current.parent
        raise ValueError("Could not find project root")

    def _init_database(self):
        """Initialize SQLite database with schema"""
        with sqlite3.connect(self.db_path) as conn:
            # Cost transactions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cost_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    amount REAL NOT NULL,
                    tool_name TEXT,
                    pattern_name TEXT,
                    acquisition_type TEXT,
                    metadata TEXT
                )
            """)

            # Budgets table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period TEXT NOT NULL UNIQUE,
                    limit_amount REAL NOT NULL,
                    current_spend REAL DEFAULT 0.0,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Alerts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cost_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    budget_period TEXT,
                    current_spend REAL,
                    budget_limit REAL,
                    acknowledged INTEGER DEFAULT 0
                )
            """)

            # Indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_timestamp
                ON cost_transactions(timestamp)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_category
                ON cost_transactions(category)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp
                ON cost_alerts(timestamp)
            """)

            conn.commit()

    def _load_budgets(self):
        """Load budgets from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM budgets")

            for row in cursor.fetchall():
                period = BudgetPeriod(row[1])
                budget = Budget(
                    period=period,
                    limit=row[2],
                    current_spend=row[3],
                    start_date=datetime.fromisoformat(row[4]),
                    end_date=datetime.fromisoformat(row[5])
                )
                self.budgets[period] = budget

    def set_budget(self, period: BudgetPeriod, limit: float) -> Budget:
        """
        Set budget for a period.

        Args:
            period: Budget period type
            limit: Budget limit amount

        Returns:
            Budget object
        """
        budget = Budget(period=period, limit=limit)
        self.budgets[period] = budget

        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO budgets
                (period, limit_amount, current_spend, start_date, end_date, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                period.value,
                limit,
                budget.current_spend,
                budget.start_date.isoformat(),
                budget.end_date.isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()

        logger.info(f"Set {period.value} budget: ${limit:.2f}")
        return budget

    def record_cost(
        self,
        amount: float,
        category: str,
        description: Optional[str] = None,
        tool_name: Optional[str] = None,
        pattern_name: Optional[str] = None,
        acquisition_type: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Record a cost transaction.

        Args:
            amount: Cost amount
            category: Cost category (e.g., 'api', 'library', 'tool_generation')
            description: Optional description
            tool_name: Tool associated with cost
            pattern_name: Pattern associated with cost
            acquisition_type: Type of acquisition (build, library, api)
            metadata: Additional metadata

        Returns:
            True if recorded successfully (within budget), False otherwise
        """
        import json

        timestamp = datetime.now()

        # Check budget enforcement
        can_proceed = self._check_budget_enforcement(amount)

        if not can_proceed:
            logger.warning(f"Cost ${amount:.2f} blocked by budget enforcement")
            self._create_alert(
                level=AlertLevel.CRITICAL,
                message=f"Transaction blocked: ${amount:.2f} would exceed budget",
                budget_period=BudgetPeriod.MONTHLY,
                current_spend=self.budgets.get(BudgetPeriod.MONTHLY, Budget(BudgetPeriod.MONTHLY, 0)).current_spend,
                budget_limit=self.budgets.get(BudgetPeriod.MONTHLY, Budget(BudgetPeriod.MONTHLY, 0)).limit
            )
            return False

        # Record transaction
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO cost_transactions
                (timestamp, category, description, amount, tool_name, pattern_name, acquisition_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp.isoformat(),
                category,
                description,
                amount,
                tool_name,
                pattern_name,
                acquisition_type,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()

        # Update budget spend
        self._update_budget_spend(amount)

        # Check for alerts
        self._check_budget_alerts()

        logger.info(f"Recorded cost: ${amount:.2f} ({category})")
        return True

    def _check_budget_enforcement(self, amount: float) -> bool:
        """
        Check if transaction can proceed given budgets.

        Args:
            amount: Transaction amount

        Returns:
            True if allowed, False if blocked
        """
        # Check all active budgets
        for period, budget in self.budgets.items():
            # Reset expired budgets
            if budget.is_expired():
                self._reset_budget(period)
                budget = self.budgets[period]

            # Check if transaction would exceed budget
            if budget.current_spend + amount > budget.limit:
                logger.warning(
                    f"{period.value} budget would be exceeded: "
                    f"${budget.current_spend:.2f} + ${amount:.2f} > ${budget.limit:.2f}"
                )
                return False

        return True

    def _update_budget_spend(self, amount: float):
        """Update budget spend for all active periods"""
        with sqlite3.connect(self.db_path) as conn:
            for period, budget in self.budgets.items():
                budget.current_spend += amount

                # Update database
                conn.execute("""
                    UPDATE budgets
                    SET current_spend = ?, updated_at = ?
                    WHERE period = ?
                """, (budget.current_spend, datetime.now().isoformat(), period.value))

            conn.commit()

    def _reset_budget(self, period: BudgetPeriod):
        """Reset budget for new period"""
        old_budget = self.budgets[period]
        new_budget = Budget(period=period, limit=old_budget.limit)
        self.budgets[period] = new_budget

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE budgets
                SET current_spend = ?, start_date = ?, end_date = ?, updated_at = ?
                WHERE period = ?
            """, (
                0.0,
                new_budget.start_date.isoformat(),
                new_budget.end_date.isoformat(),
                datetime.now().isoformat(),
                period.value
            ))
            conn.commit()

        logger.info(f"Reset {period.value} budget for new period")

    def _check_budget_alerts(self):
        """Check if budget thresholds are crossed and create alerts"""
        for period, budget in self.budgets.items():
            utilization = budget.utilization_percent()

            # 80% threshold - warning
            if 80 <= utilization < 95:
                self._create_alert(
                    level=AlertLevel.WARNING,
                    message=f"{period.value.capitalize()} budget at {utilization:.1f}% ({budget.current_spend:.2f}/${budget.limit:.2f})",
                    budget_period=period,
                    current_spend=budget.current_spend,
                    budget_limit=budget.limit
                )

            # 95% threshold - critical
            elif utilization >= 95:
                self._create_alert(
                    level=AlertLevel.CRITICAL,
                    message=f"{period.value.capitalize()} budget CRITICAL at {utilization:.1f}% ({budget.current_spend:.2f}/${budget.limit:.2f})",
                    budget_period=period,
                    current_spend=budget.current_spend,
                    budget_limit=budget.limit
                )

    def _create_alert(
        self,
        level: AlertLevel,
        message: str,
        budget_period: Optional[BudgetPeriod] = None,
        current_spend: float = 0.0,
        budget_limit: float = 0.0
    ):
        """Create and store cost alert"""
        alert = CostAlert(
            level=level,
            message=message,
            budget_period=budget_period,
            current_spend=current_spend,
            budget_limit=budget_limit
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO cost_alerts
                (timestamp, level, message, budget_period, current_spend, budget_limit)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                alert.timestamp.isoformat(),
                alert.level.value,
                alert.message,
                alert.budget_period.value if alert.budget_period else None,
                alert.current_spend,
                alert.budget_limit
            ))
            conn.commit()

        logger.log(
            logging.WARNING if level == AlertLevel.WARNING else logging.CRITICAL,
            f"COST ALERT [{level.value.upper()}]: {message}"
        )

    def get_budget_status(self) -> Dict[str, Dict]:
        """
        Get current budget status for all periods.

        Returns:
            Dict with budget status for each period
        """
        status = {}

        for period, budget in self.budgets.items():
            # Reset if expired
            if budget.is_expired():
                self._reset_budget(period)
                budget = self.budgets[period]

            status[period.value] = {
                'limit': budget.limit,
                'current_spend': budget.current_spend,
                'remaining': budget.remaining(),
                'utilization_percent': budget.utilization_percent(),
                'start_date': budget.start_date.isoformat(),
                'end_date': budget.end_date.isoformat(),
                'days_remaining': (budget.end_date - datetime.now()).days
            }

        return status

    def get_spending_by_category(self, days: int = 30) -> Dict[str, float]:
        """
        Get spending breakdown by category.

        Args:
            days: Number of days to analyze

        Returns:
            Dict mapping category to total spend
        """
        since = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT category, SUM(amount) as total
                FROM cost_transactions
                WHERE timestamp >= ?
                GROUP BY category
                ORDER BY total DESC
            """, (since.isoformat(),))

            return {row[0]: row[1] for row in cursor.fetchall()}

    def forecast_monthly_spend(self) -> float:
        """
        Forecast monthly spend based on recent trends.

        Returns:
            Forecasted monthly spend
        """
        # Get spend for last 7 days
        since = datetime.now() - timedelta(days=7)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT SUM(amount) as total
                FROM cost_transactions
                WHERE timestamp >= ?
            """, (since.isoformat(),))

            row = cursor.fetchone()
            weekly_spend = row[0] if row[0] else 0.0

        # Extrapolate to monthly (30 days)
        daily_average = weekly_spend / 7
        monthly_forecast = daily_average * 30

        return monthly_forecast

    def get_optimization_recommendations(self) -> List[CostOptimization]:
        """
        Generate cost optimization recommendations.

        Returns:
            List of CostOptimization recommendations
        """
        recommendations = []

        # Analyze spending patterns
        spending_by_category = self.get_spending_by_category(days=30)
        total_spend = sum(spending_by_category.values())

        if total_spend == 0:
            return recommendations

        # Recommendation 1: High API costs
        api_spend = spending_by_category.get('api', 0.0)
        if api_spend > total_spend * 0.5:  # >50% on APIs
            recommendations.append(CostOptimization(
                recommendation="Consider caching API responses more aggressively",
                potential_savings=api_spend * 0.3,  # 30% savings estimate
                implementation_effort="medium",
                priority=0.8,
                details={
                    'current_api_spend': api_spend,
                    'percent_of_total': (api_spend / total_spend) * 100
                }
            ))

        # Recommendation 2: Tool generation costs
        generation_spend = spending_by_category.get('tool_generation', 0.0)
        if generation_spend > total_spend * 0.3:  # >30% on generation
            recommendations.append(CostOptimization(
                recommendation="Use cheaper models for tool generation (e.g., GPT-4o-mini instead of GPT-4o)",
                potential_savings=generation_spend * 0.6,  # 60% savings estimate
                implementation_effort="low",
                priority=0.9,
                details={
                    'current_generation_spend': generation_spend,
                    'percent_of_total': (generation_spend / total_spend) * 100
                }
            ))

        # Recommendation 3: Underutilized paid tools (from tool memory)
        # This would integrate with ToolMemorySystem to find tools with low usage
        recommendations.append(CostOptimization(
            recommendation="Review and retire underutilized paid tools",
            potential_savings=total_spend * 0.15,  # 15% savings estimate
            implementation_effort="medium",
            priority=0.7,
            details={
                'action': 'Run get_tools_to_retire() from ToolMemorySystem'
            }
        ))

        # Sort by priority
        recommendations.sort(key=lambda r: r.priority, reverse=True)

        return recommendations

    def get_recent_alerts(self, limit: int = 10) -> List[CostAlert]:
        """
        Get recent cost alerts.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of recent CostAlert objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT timestamp, level, message, budget_period, current_spend, budget_limit
                FROM cost_alerts
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            alerts = []
            for row in cursor.fetchall():
                alerts.append(CostAlert(
                    level=AlertLevel(row[1]),
                    message=row[2],
                    budget_period=BudgetPeriod(row[3]) if row[3] else None,
                    current_spend=row[4],
                    budget_limit=row[5],
                    timestamp=datetime.fromisoformat(row[0])
                ))

            return alerts


# Example usage and testing
if __name__ == "__main__":
    print("Cost Management System - Test Mode\n")

    cost_system = CostManagementSystem()

    print("=" * 80)
    print("Test 1: Set Budgets")
    print("=" * 80)

    cost_system.set_budget(BudgetPeriod.DAILY, 10.0)
    cost_system.set_budget(BudgetPeriod.WEEKLY, 50.0)
    cost_system.set_budget(BudgetPeriod.MONTHLY, 200.0)

    print("\n✓ Budgets configured")

    # Test 2: Record costs
    print("\n" + "=" * 80)
    print("Test 2: Record Cost Transactions")
    print("=" * 80)

    transactions = [
        (2.50, "api", "Weather API calls", "WeatherTool"),
        (1.00, "tool_generation", "Gemini 2.5 Pro generation", None),
        (0.50, "api", "Currency API calls", "CurrencyTool"),
        (3.00, "library", "PyPI library monthly fee", "premium-lib"),
    ]

    for amount, category, desc, tool in transactions:
        success = cost_system.record_cost(
            amount=amount,
            category=category,
            description=desc,
            tool_name=tool
        )
        print(f"  {'✓' if success else '✗'} ${amount:.2f} - {desc}")

    # Test 3: Budget status
    print("\n" + "=" * 80)
    print("Test 3: Budget Status")
    print("=" * 80)

    status = cost_system.get_budget_status()

    for period, info in status.items():
        print(f"\n{period.upper()} Budget:")
        print(f"  Limit: ${info['limit']:.2f}")
        print(f"  Spent: ${info['current_spend']:.2f}")
        print(f"  Remaining: ${info['remaining']:.2f}")
        print(f"  Utilization: {info['utilization_percent']:.1f}%")

    # Test 4: Spending breakdown
    print("\n" + "=" * 80)
    print("Test 4: Spending by Category")
    print("=" * 80)

    spending = cost_system.get_spending_by_category(days=30)

    print("\nLast 30 days:")
    for category, amount in spending.items():
        print(f"  {category}: ${amount:.2f}")

    # Test 5: Forecast
    print("\n" + "=" * 80)
    print("Test 5: Monthly Forecast")
    print("=" * 80)

    forecast = cost_system.forecast_monthly_spend()
    print(f"\nForecasted monthly spend: ${forecast:.2f}")

    # Test 6: Optimization recommendations
    print("\n" + "=" * 80)
    print("Test 6: Cost Optimization Recommendations")
    print("=" * 80)

    recommendations = cost_system.get_optimization_recommendations()

    if recommendations:
        print(f"\nFound {len(recommendations)} recommendations:\n")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec.recommendation}")
            print(f"   Potential savings: ${rec.potential_savings:.2f}/month")
            print(f"   Effort: {rec.implementation_effort} | Priority: {rec.priority:.1f}")
            print()
    else:
        print("\nNo optimization recommendations at this time")

    print("=" * 80)
