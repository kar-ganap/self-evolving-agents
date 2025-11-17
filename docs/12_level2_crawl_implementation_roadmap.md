# Level 2 CRAWL: Detailed Implementation Roadmap
## Autonomous Tool Generation with Build vs Buy Analysis

**Document Purpose:** Step-by-step implementation guide with go/no-go checkpoints, validation tests, and rollback procedures for Level 2 CRAWL phase.

**Created:** 2025-01-15
**Status:** Ready for Implementation
**Prerequisites:** Phase 0 complete (base GPT-4.1 + system prompting = 80% pattern adherence)

---

## Quick Reference: Milestone Overview

| Milestone | Duration | Risk | Deliverable | Test Command |
|-----------|----------|------|-------------|--------------|
| **2.1** | 3h | Low | `capability_gap_detector.py` | `pytest tests/test_gap_detector.py` |
| **2.2** | 4h | Medium | `build_vs_buy_analyzer.py` | `pytest tests/test_build_vs_buy.py` |
| **2.3** | 3h | Low | `approval_workflow.py` + `config/approval_settings.yaml` | `pytest tests/test_approval.py` |
| **2.4** | 5h | High | `tool_acquisition_engine.py` | Manual validation (generates code) |
| **2.5** | 4h | Medium | `unified_agent_pipeline.py` | End-to-end test script |
| **2.6** | 3h | Low | `capability_evolution_engine.py` | Integration test |
| **2.7** | 2h | Low | Testing & Validation | Full system test |

**Total Time:** 24 hours (3 working days)
**Risk Level:** Medium (tool generation is unproven, but has fallbacks)

---

# MILESTONE 2.1: Capability Gap Detector

**Goal:** Determine if we can fulfill a pattern's requirements
**Duration:** 3 hours
**Deliverable:** `src/level2/crawl/capability_gap_detector.py`

---

## Tasks

1. **[45 min]** Create project structure
   - Create `src/level2/crawl/` directory
   - Create `src/level2/crawl/__init__.py`
   - Create initial `capability_gap_detector.py` with class skeleton

2. **[60 min]** Implement `CapabilityGapDetector` class
   - `__init__()` - Load known capabilities database
   - `assess_capability()` - Main assessment method
   - `_extract_required_capabilities()` - Parse pattern description
   - `_have_capability()` - Check against known capabilities
   - `_load_capability_database()` - Return capability dictionary

3. **[45 min]** Create `CapabilityStatus` dataclass and unit tests
   - Define dataclass with: `exists`, `confidence`, `current_tools`, `gap_description`
   - Write 5 test cases covering different scenarios

4. **[30 min]** Integration with patterns.json
   - Load patterns from `data/patterns.json`
   - Test against 3 real patterns from Phase 0

---

## Implementation Details

### File Structure
```python
# src/level2/crawl/capability_gap_detector.py

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class CapabilityStatus:
    """Result of capability assessment."""
    exists: bool
    confidence: float
    current_tools: List[str]
    gap_description: str

class CapabilityGapDetector:
    """
    Analyzes patterns to determine if we have the capability.

    Uses a knowledge base of known capabilities:
    - Code analysis: AST parsing, linting, formatting
    - Data retrieval: Local files, databases, caching
    - External data: APIs, web scraping, real-time feeds
    """

    def __init__(self, tool_registry=None):
        self.tool_registry = tool_registry or MockToolRegistry()
        self.known_capabilities = self._load_capability_database()

    def assess_capability(self, pattern: Dict) -> CapabilityStatus:
        """
        Determine if we can fulfill this pattern's requirements.

        Args:
            pattern: Pattern dictionary from patterns.json

        Returns:
            CapabilityStatus with existence and gap details
        """
        # Check if we have tools that address this pattern
        existing_tools = self.tool_registry.get_tools_for_pattern(
            pattern['name']
        )

        if existing_tools:
            return CapabilityStatus(
                exists=True,
                confidence=1.0,
                current_tools=[t.name for t in existing_tools],
                gap_description=""
            )

        # Check if this requires capabilities we don't have
        required_capabilities = self._extract_required_capabilities(pattern)
        missing = [cap for cap in required_capabilities
                   if not self._have_capability(cap)]

        if not missing:
            return CapabilityStatus(
                exists=True,
                confidence=0.8,
                current_tools=[],
                gap_description="Can be built with existing capabilities"
            )

        return CapabilityStatus(
            exists=False,
            confidence=0.9,
            current_tools=[],
            gap_description=f"Missing capabilities: {', '.join(missing)}"
        )

    def _extract_required_capabilities(self, pattern: Dict) -> List[str]:
        """
        Parse pattern description to identify required capabilities.

        Examples:
        - "check for tests" → ['code_analysis', 'file_system']
        - "fetch real-time market data" → ['external_api', 'data_parsing']
        """
        description = pattern.get('description', '').lower()
        capabilities = []

        # Code analysis capabilities
        if any(kw in description for kw in ['parse', 'analyze', 'ast', 'syntax', 'code']):
            capabilities.append('code_analysis')

        # External data capabilities
        if any(kw in description for kw in ['fetch', 'api', 'real-time', 'external']):
            capabilities.append('external_api')

        # File system capabilities
        if any(kw in description for kw in ['file', 'directory', 'path', 'test']):
            capabilities.append('file_system')

        # Data processing capabilities
        if any(kw in description for kw in ['process', 'transform', 'parse']):
            capabilities.append('data_processing')

        return capabilities

    def _have_capability(self, capability: str) -> bool:
        """Check if we have this capability in our knowledge base."""
        return capability in self.known_capabilities

    def _load_capability_database(self) -> Dict[str, Dict]:
        """
        Load database of known capabilities.

        Each capability includes:
        - Available libraries/tools
        - Typical use cases
        - Implementation complexity
        """
        return {
            'code_analysis': {
                'libraries': ['ast', 'astroid', 'rope'],
                'complexity': 'low',
                'description': 'Parse and analyze Python code'
            },
            'file_system': {
                'libraries': ['pathlib', 'os', 'shutil'],
                'complexity': 'low',
                'description': 'File and directory operations'
            },
            'data_processing': {
                'libraries': ['json', 'csv'],
                'complexity': 'low',
                'description': 'Data manipulation and transformation'
            },
            # External capabilities we DON'T have yet
            # These will trigger build vs buy analysis
        }


class MockToolRegistry:
    """Mock registry for testing until we build the real one."""
    def get_tools_for_pattern(self, pattern_name: str):
        return []
```

---

## Success Criteria

- [ ] File `src/level2/crawl/capability_gap_detector.py` exists and imports without errors
- [ ] `CapabilityGapDetector` class instantiates successfully
- [ ] `assess_capability()` returns `CapabilityStatus` for valid pattern input
- [ ] Test case 1: Pattern requiring `code_analysis` → `exists=True` (we have it)
- [ ] Test case 2: Pattern requiring `external_api` → `exists=False` (we don't have it)
- [ ] Test case 3: Pattern with existing tools → `exists=True`, `current_tools` populated
- [ ] All unit tests pass: `pytest tests/test_gap_detector.py`

---

## Go/No-Go Checkpoint 2.1

**GO if:**
- ✅ All 7 success criteria met
- ✅ Class correctly identifies gaps for 3 test patterns
- ✅ Tests pass

**NO-GO if:**
- ❌ Can't parse pattern descriptions
- ❌ Always returns same result (not detecting differences)
- ❌ Crashes on edge cases (missing fields, None values)

---

## If NO-GO: Rollback Procedures

1. **Can't parse pattern descriptions:**
   - Simplify to exact keyword matching only
   - Hardcode mapping for known patterns
   - **Minimum viable:** Just return "gap exists" for all patterns (triggers build vs buy for everything)

2. **Always returns same result:**
   - Debug `_extract_required_capabilities()` logic
   - Add print statements to see what's being matched
   - **Quick fix:** Return `exists=False` for all patterns initially (everything goes through build vs buy)

3. **Crashes on edge cases:**
   - Add defensive checks: `if not pattern: return default_status`
   - Add try/except around description parsing
   - **Fallback:** Return "unknown" status and log for manual review

---

## Test Commands

```bash
# Create test file
cat > tests/test_gap_detector.py << 'EOF'
import pytest
from src.level2.crawl.capability_gap_detector import (
    CapabilityGapDetector,
    CapabilityStatus
)

def test_detector_initialization():
    """Test that detector initializes correctly."""
    detector = CapabilityGapDetector()
    assert detector is not None
    assert len(detector.known_capabilities) > 0

def test_code_analysis_capability_exists():
    """Test that code analysis capability is recognized."""
    detector = CapabilityGapDetector()
    pattern = {
        'name': 'Production Readiness',
        'description': 'Check code for tests, type hints, error handling'
    }
    status = detector.assess_capability(pattern)
    assert status.exists == True
    assert 'code_analysis' in detector._extract_required_capabilities(pattern)

def test_external_api_capability_missing():
    """Test that external API capability is detected as missing."""
    detector = CapabilityGapDetector()
    pattern = {
        'name': 'Real-Time Market Data',
        'description': 'Fetch real-time stock prices from external API'
    }
    status = detector.assess_capability(pattern)
    assert status.exists == False
    assert 'Missing capabilities' in status.gap_description

def test_pattern_with_existing_tools():
    """Test that existing tools are recognized."""
    # This will fail until we implement ToolRegistry
    # For now, just test the mock behavior
    detector = CapabilityGapDetector()
    pattern = {'name': 'Test Pattern', 'description': 'test'}
    status = detector.assess_capability(pattern)
    assert status.current_tools == []  # Mock returns empty list

def test_edge_case_empty_pattern():
    """Test handling of malformed input."""
    detector = CapabilityGapDetector()
    pattern = {}
    status = detector.assess_capability(pattern)
    # Should not crash
    assert isinstance(status, CapabilityStatus)
EOF

# Run tests
pytest tests/test_gap_detector.py -v
```

---

## Time Checkpoint

**Should complete by:** Hour 3 of implementation
**If running late:**
- Skip comprehensive tests, just test happy path
- Hardcode capability mappings instead of keyword parsing
- Proceed with simplified version

---

## Dependencies

**Input:**
- `data/patterns.json` (from Phase 0)

**Output:**
- `CapabilityStatus` object for downstream components

**Blocks:**
- Milestone 2.2 (Build vs Buy Analyzer needs gap status)

---

# MILESTONE 2.2: Build vs Buy Analyzer

**Goal:** Compare building internally vs acquiring externally
**Duration:** 4 hours
**Deliverable:** `src/level2/crawl/build_vs_buy_analyzer.py`

---

## Tasks

1. **[60 min]** Implement dataclasses
   - `BuildOption` - Details for building internally
   - `BuyOption` - Details for external acquisition
   - `BuildVsBuyRecommendation` - Complete recommendation with analysis

2. **[90 min]** Implement `BuildVsBuyAnalyzer` class
   - `__init__()` - Set hourly dev rate
   - `analyze()` - Main analysis method
   - `_analyze_build_option()` - Estimate internal build cost
   - `_search_external_options()` - Find libraries/APIs
   - `_make_recommendation()` - Compare and recommend

3. **[60 min]** External search implementation
   - PyPI search integration (use `requests` to query PyPI API)
   - Hardcoded mappings for common patterns
   - Placeholder for future API search

4. **[30 min]** Unit tests and validation
   - Test cost calculations
   - Test recommendation logic
   - Test with 3 different patterns

---

## Implementation Details

### Core Logic

```python
# src/level2/crawl/build_vs_buy_analyzer.py

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class AcquisitionStrategy(Enum):
    BUILD = "build"
    BUY_LIBRARY = "buy_library"
    BUY_API = "buy_api"

@dataclass
class BuildOption:
    """Details for building internally."""
    implementation_time_hours: float
    estimated_cost_usd: float
    complexity_score: float  # 0-1, where 1 is very complex
    pros: List[str]
    cons: List[str]
    implementation_notes: str

@dataclass
class BuyOption:
    """Details for external acquisition."""
    name: str
    type: str  # 'library' or 'api'
    monthly_cost_usd: float
    one_time_cost_usd: float
    features: List[str]
    limitations: List[str]
    pros: List[str]
    cons: List[str]
    installation_notes: str

@dataclass
class BuildVsBuyRecommendation:
    """Complete recommendation with analysis."""
    recommendation: AcquisitionStrategy
    build_option: Optional[BuildOption]
    buy_options: List[BuyOption]
    confidence: float
    reasoning: str
    total_cost_analysis: Dict[str, float]

class BuildVsBuyAnalyzer:
    """
    For capability gaps, analyze build vs buy tradeoffs.

    Considers:
    - Implementation complexity
    - Cost (development time vs subscription)
    - Reliability requirements
    - Maintenance burden
    - Feature completeness
    """

    def __init__(self, hourly_dev_rate: float = 150.0):
        self.hourly_dev_rate = hourly_dev_rate

    def analyze(
        self,
        pattern: Dict,
        gap: 'CapabilityStatus'
    ) -> BuildVsBuyRecommendation:
        """
        Analyze build vs buy options for a capability gap.

        Args:
            pattern: The pattern requiring this capability
            gap: Details about the capability gap

        Returns:
            BuildVsBuyRecommendation with detailed analysis
        """
        # Analyze build option
        build_option = self._analyze_build_option(pattern, gap)

        # Search for buy options (libraries and APIs)
        buy_options = self._search_external_options(pattern, gap)

        # Compare options and make recommendation
        recommendation = self._make_recommendation(
            build_option,
            buy_options
        )

        return recommendation

    def _analyze_build_option(
        self,
        pattern: Dict,
        gap: 'CapabilityStatus'
    ) -> BuildOption:
        """
        Estimate cost and complexity of building internally.
        """
        description = pattern.get('description', '')

        # Estimate implementation time based on keywords
        base_hours = 4.0  # Minimum for any tool

        complexity_factors = {
            'api': 8.0,
            'real-time': 6.0,
            'parsing': 4.0,
            'analysis': 3.0,
            'validation': 2.0,
        }

        total_hours = base_hours
        for keyword, hours in complexity_factors.items():
            if keyword in description.lower():
                total_hours += hours

        complexity_score = min(1.0, total_hours / 40.0)
        estimated_cost = total_hours * self.hourly_dev_rate

        return BuildOption(
            implementation_time_hours=total_hours,
            estimated_cost_usd=estimated_cost,
            complexity_score=complexity_score,
            pros=[
                "Full control over implementation",
                "No external dependencies",
                "No ongoing API costs",
                "Custom-fit to exact needs"
            ],
            cons=[
                f"Development time: {total_hours:.1f} hours",
                f"One-time cost: ${estimated_cost:.2f}",
                "Need to maintain and update",
                "May have limited features initially"
            ],
            implementation_notes=f"Estimated {total_hours:.1f} hours to implement"
        )

    def _search_external_options(
        self,
        pattern: Dict,
        gap: 'CapabilityStatus'
    ) -> List[BuyOption]:
        """
        Search for external libraries and APIs.

        For CRAWL phase: Use hardcoded mappings for known patterns.
        For WALK phase: Implement actual PyPI/API search.
        """
        options = []
        description = pattern.get('description', '').lower()

        # Hardcoded mappings for common capabilities
        if 'complexity' in description and 'code' in description:
            options.append(BuyOption(
                name='radon',
                type='library',
                monthly_cost_usd=0.0,
                one_time_cost_usd=0.0,
                features=[
                    'Cyclomatic complexity',
                    'Maintainability index',
                    'Halstead metrics',
                    'Raw metrics (LOC, comments)'
                ],
                limitations=[
                    'Python only',
                    'No custom metrics'
                ],
                pros=[
                    'Free and open source (MIT license)',
                    'Battle-tested (1k+ stars)',
                    'Rich feature set',
                    'Active maintenance'
                ],
                cons=[
                    'Additional dependency',
                    'Limited to Python code'
                ],
                installation_notes='pip install radon'
            ))

        if 'test' in description or 'coverage' in description:
            options.append(BuyOption(
                name='pytest-cov',
                type='library',
                monthly_cost_usd=0.0,
                one_time_cost_usd=0.0,
                features=[
                    'Test coverage measurement',
                    'pytest integration',
                    'HTML reports',
                    'Branch coverage'
                ],
                limitations=[
                    'Requires pytest',
                    'Python only'
                ],
                pros=[
                    'Free (MIT license)',
                    'Industry standard',
                    'Rich reporting'
                ],
                cons=[
                    'pytest dependency'
                ],
                installation_notes='pip install pytest-cov'
            ))

        return options

    def _make_recommendation(
        self,
        build_option: BuildOption,
        buy_options: List[BuyOption]
    ) -> BuildVsBuyRecommendation:
        """
        Compare options and make a recommendation.

        Decision factors:
        1. Cost over 12 months
        2. Implementation time
        3. Reliability requirements
        4. Feature completeness
        """
        # Calculate 12-month total cost for each option
        build_total_cost = build_option.estimated_cost_usd

        buy_costs = {}
        for option in buy_options:
            total_cost = (
                option.one_time_cost_usd +
                (option.monthly_cost_usd * 12)
            )
            buy_costs[option.name] = total_cost

        # Decision logic
        if not buy_options:
            # No external options available - must build
            return BuildVsBuyRecommendation(
                recommendation=AcquisitionStrategy.BUILD,
                build_option=build_option,
                buy_options=[],
                confidence=1.0,
                reasoning="No external options available",
                total_cost_analysis={'build': build_total_cost}
            )

        # Check for free libraries with good features
        free_libraries = [
            opt for opt in buy_options
            if opt.monthly_cost_usd == 0 and opt.type == 'library'
        ]

        if free_libraries:
            best_free = max(free_libraries, key=lambda x: len(x.features))
            return BuildVsBuyRecommendation(
                recommendation=AcquisitionStrategy.BUY_LIBRARY,
                build_option=build_option,
                buy_options=buy_options,
                confidence=0.9,
                reasoning=(
                    f"Free library '{best_free.name}' provides {len(best_free.features)} "
                    f"features with no ongoing cost. Building would cost "
                    f"${build_total_cost:.2f} and provide fewer features initially."
                ),
                total_cost_analysis={
                    'build': build_total_cost,
                    best_free.name: 0.0
                }
            )

        # Compare paid options vs build
        cheapest_buy = min(buy_options, key=lambda x: buy_costs[x.name])
        cheapest_buy_cost = buy_costs[cheapest_buy.name]

        if cheapest_buy_cost < build_total_cost * 0.5:
            # External option is significantly cheaper
            return BuildVsBuyRecommendation(
                recommendation=(
                    AcquisitionStrategy.BUY_API
                    if cheapest_buy.type == 'api'
                    else AcquisitionStrategy.BUY_LIBRARY
                ),
                build_option=build_option,
                buy_options=buy_options,
                confidence=0.85,
                reasoning=(
                    f"External option '{cheapest_buy.name}' costs "
                    f"${cheapest_buy_cost:.2f}/year vs building at "
                    f"${build_total_cost:.2f} one-time. External option "
                    f"provides {len(cheapest_buy.features)} features immediately."
                ),
                total_cost_analysis={
                    'build': build_total_cost,
                    **buy_costs
                }
            )

        # Build is competitive or better
        return BuildVsBuyRecommendation(
            recommendation=AcquisitionStrategy.BUILD,
            build_option=build_option,
            buy_options=buy_options,
            confidence=0.8,
            reasoning=(
                f"Building internally costs ${build_total_cost:.2f} one-time. "
                f"Cheapest external option '{cheapest_buy.name}' costs "
                f"${cheapest_buy_cost:.2f}/year. Building provides full control "
                f"and no ongoing costs."
            ),
            total_cost_analysis={
                'build': build_total_cost,
                **buy_costs
            }
        )
```

---

## Success Criteria

- [ ] `BuildVsBuyAnalyzer` class instantiates successfully
- [ ] `analyze()` returns `BuildVsBuyRecommendation` for valid inputs
- [ ] Test case 1: Pattern with free library → Recommends BUY_LIBRARY
- [ ] Test case 2: Pattern with no external options → Recommends BUILD
- [ ] Test case 3: Pattern with expensive API → Compares cost, makes decision
- [ ] Cost calculations are accurate (12-month total)
- [ ] Reasoning field explains the decision clearly
- [ ] All unit tests pass: `pytest tests/test_build_vs_buy.py`

---

## Go/No-Go Checkpoint 2.2

**GO if:**
- ✅ All 8 success criteria met
- ✅ Recommendations make sense for test patterns
- ✅ Cost analysis is accurate

**NO-GO if:**
- ❌ Always recommends same option
- ❌ Cost calculations are wrong
- ❌ Can't find any external options

---

## If NO-GO: Rollback Procedures

1. **Always recommends same option:**
   - Debug `_make_recommendation()` decision logic
   - Add logging to see what values are being compared
   - **Quick fix:** Always recommend BUILD initially (safe default)

2. **Cost calculations wrong:**
   - Verify 12-month calculation: `one_time + (monthly * 12)`
   - Check that hourly rate is being applied correctly
   - **Fallback:** Use simplified flat cost estimates

3. **Can't find external options:**
   - Expand hardcoded mappings for more keywords
   - Add fallback: "Unknown if external options exist"
   - **Minimum viable:** Always return empty buy_options (will recommend BUILD)

---

## Test Commands

```bash
# Run tests
pytest tests/test_build_vs_buy.py -v

# Manual validation
python -c "
from src.level2.crawl.build_vs_buy_analyzer import BuildVsBuyAnalyzer
from src.level2.crawl.capability_gap_detector import CapabilityStatus

analyzer = BuildVsBuyAnalyzer(hourly_dev_rate=150.0)

# Test pattern: Code complexity analysis
pattern = {
    'name': 'Complexity Analysis',
    'description': 'Analyze code complexity using cyclomatic complexity'
}
gap = CapabilityStatus(exists=False, confidence=0.9, current_tools=[], gap_description='Missing')

recommendation = analyzer.analyze(pattern, gap)
print(f'Recommendation: {recommendation.recommendation.value}')
print(f'Confidence: {recommendation.confidence:.0%}')
print(f'Reasoning: {recommendation.reasoning}')
print(f'Costs: {recommendation.total_cost_analysis}')
"
```

---

## Time Checkpoint

**Should complete by:** Hour 7 of implementation
**If running late:**
- Skip PyPI API integration, use hardcoded mappings only
- Simplify cost calculation (flat estimates)
- Skip detailed pros/cons, just provide basic info

---

## Dependencies

**Input:**
- `CapabilityStatus` from Milestone 2.1
- Pattern dictionary

**Output:**
- `BuildVsBuyRecommendation` for Milestone 2.3

**Blocks:**
- Milestone 2.3 (Approval Workflow needs recommendation)

---

# MILESTONE 2.3: Approval Workflow

**Goal:** Human-in-loop approval with configurable bypass rules
**Duration:** 3 hours
**Deliverables:**
- `src/level2/crawl/approval_workflow.py`
- `config/approval_settings.yaml`

---

## Tasks

1. **[30 min]** Create configuration file structure
   - Create `config/approval_settings.yaml`
   - Define bypass conditions (free libraries, simple builds)
   - Define require approval conditions (subscriptions, complex builds)

2. **[60 min]** Implement `ApprovalWorkflow` class
   - `__init__()` - Load configuration
   - `needs_approval()` - Check bypass/require rules
   - `request_approval()` - CLI prompt for human input
   - Helper methods for rule checking

3. **[45 min]** Implement `ApprovalResponse` dataclass
   - Fields: `approved`, `selected_option`, `auto_approved`, `notes`
   - Validation logic

4. **[45 min]** Unit tests and CLI testing
   - Test bypass rules
   - Test require approval rules
   - Manual CLI test

---

## Implementation Details

### Configuration File

```yaml
# config/approval_settings.yaml

approval_rules:
  # Bypass conditions (auto-approve)
  bypass_conditions:
    - type: free_library
      max_dependencies: 5
      description: "Free Python libraries with <5 dependencies"

    - type: internal_code
      max_complexity_score: 0.7
      description: "Simple internal tool generation (complexity < 0.7)"

    - type: low_cost
      max_monthly_cost: 10  # USD
      max_implementation_time: 3600  # seconds (1 hour)
      description: "Low-cost options (<$10/mo OR <1hr implementation)"

  # Require approval conditions
  require_approval:
    - type: subscription
      any_recurring_cost: true
      description: "Any option with ongoing monthly cost"

    - type: external_api
      has_rate_limits: true
      description: "External APIs with rate limits or usage costs"

    - type: complex_build
      min_implementation_time: 86400  # seconds (1 day)
      description: "Complex builds requiring >1 day implementation"

    - type: high_cost
      monthly_cost: 50  # USD
      description: "High-cost options (>$50/month)"

notification:
  method: "cli_prompt"  # Options: "cli_prompt", "email", "slack"
  timeout: 3600  # seconds to wait for approval
  default_on_timeout: "reject"

cost_settings:
  hourly_dev_rate: 150.00
  monthly_budget: 200.00
  warn_threshold: 0.8

tool_generation:
  model: "claude-sonnet-4-5-20250929"
  temperature: 0.3
  max_tokens: 3000

gap_detection:
  threshold: 3  # Trigger after 3 occurrences
  window_hours: 24
```

### Python Implementation

```python
# src/level2/crawl/approval_workflow.py

from dataclasses import dataclass
from typing import Optional
import yaml

@dataclass
class ApprovalResponse:
    """Response from approval process."""
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

    def __init__(self, config_path: str = 'config/approval_settings.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def needs_approval(
        self,
        recommendation: 'BuildVsBuyRecommendation'
    ) -> bool:
        """
        Check if this recommendation needs human approval.

        Returns True if approval required, False if can proceed automatically.
        """
        bypass_rules = self.config['approval_rules']['bypass_conditions']

        if recommendation.recommendation.value == 'buy_library':
            # Check if it's a free library
            selected_option = next(
                (opt for opt in recommendation.buy_options
                 if opt.type == 'library' and opt.monthly_cost_usd == 0),
                None
            )
            if selected_option:
                # Free library - bypass approval
                return False

        if recommendation.recommendation.value == 'build':
            build_option = recommendation.build_option

            # Check complexity bypass
            for rule in bypass_rules:
                if rule['type'] == 'internal_code':
                    if build_option.complexity_score <= rule['max_complexity_score']:
                        return False  # Auto-approve simple builds

                if rule['type'] == 'low_cost':
                    time_ok = (
                        build_option.implementation_time_hours * 3600 <=
                        rule['max_implementation_time']
                    )
                    cost_ok = (
                        build_option.estimated_cost_usd <=
                        rule['max_monthly_cost']
                    )
                    if time_ok and cost_ok:
                        return False  # Auto-approve low-cost builds

        # Check require approval conditions
        require_rules = self.config['approval_rules']['require_approval']

        for rule in require_rules:
            if rule['type'] == 'subscription':
                if recommendation.recommendation.value == 'buy_api':
                    selected = recommendation.buy_options[0]
                    if selected.monthly_cost_usd > 0:
                        return True

            if rule['type'] == 'complex_build':
                if recommendation.recommendation.value == 'build':
                    build_option = recommendation.build_option
                    time_limit = rule['min_implementation_time']
                    if build_option.implementation_time_hours * 3600 >= time_limit:
                        return True

        return True  # Default: require approval

    def request_approval(
        self,
        recommendation: 'BuildVsBuyRecommendation',
        pattern: Dict
    ) -> ApprovalResponse:
        """
        Present recommendation to human for approval via CLI.
        """
        print("\n" + "="*80)
        print("TOOL ACQUISITION APPROVAL REQUEST")
        print("="*80)
        print(f"\nPattern: {pattern['name']}")
        print(f"Description: {pattern.get('description', 'N/A')}")
        print(f"\nRecommendation: {recommendation.recommendation.value.upper()}")
        print(f"Confidence: {recommendation.confidence:.0%}")
        print(f"\nReasoning:\n{recommendation.reasoning}")

        print("\n" + "-"*80)
        print("COST ANALYSIS (12-month total):")
        for option, cost in recommendation.total_cost_analysis.items():
            print(f"  {option}: ${cost:.2f}")

        if recommendation.build_option:
            print("\n" + "-"*80)
            print("BUILD OPTION:")
            print(f"  Time: {recommendation.build_option.implementation_time_hours:.1f} hours")
            print(f"  Cost: ${recommendation.build_option.estimated_cost_usd:.2f}")
            print(f"  Complexity: {recommendation.build_option.complexity_score:.2f}")

        if recommendation.buy_options:
            print("\n" + "-"*80)
            print("EXTERNAL OPTIONS:")
            for i, option in enumerate(recommendation.buy_options, 1):
                print(f"\n  {i}. {option.name} ({option.type})")
                print(f"     Cost: ${option.monthly_cost_usd}/month")
                print(f"     Features: {', '.join(option.features[:3])}")

        print("\n" + "="*80)
        print("APPROVE THIS ACQUISITION?")
        print("  [y] Yes, proceed with recommendation")
        print("  [b] Choose BUILD option")
        for i in enumerate(recommendation.buy_options, 1):
            print(f"  [{i}] Choose external option {i}")
        print("  [n] No, cancel")
        print("="*80)

        choice = input("\nYour choice: ").strip().lower()

        if choice == 'y':
            selected = (
                'build' if recommendation.recommendation.value == 'build'
                else recommendation.buy_options[0].name
            )
            return ApprovalResponse(
                approved=True,
                selected_option=selected,
                auto_approved=False,
                notes="Approved by user"
            )

        if choice == 'b':
            return ApprovalResponse(
                approved=True,
                selected_option='build',
                auto_approved=False,
                notes="User selected BUILD option"
            )

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(recommendation.buy_options):
                return ApprovalResponse(
                    approved=True,
                    selected_option=recommendation.buy_options[idx].name,
                    auto_approved=False,
                    notes=f"User selected {recommendation.buy_options[idx].name}"
                )

        return ApprovalResponse(
            approved=False,
            selected_option='',
            auto_approved=False,
            notes="Rejected by user"
        )
```

---

## Success Criteria

- [ ] Configuration file `config/approval_settings.yaml` exists and is valid YAML
- [ ] `ApprovalWorkflow` loads configuration without errors
- [ ] `needs_approval()` correctly identifies bypass cases (free library → False)
- [ ] `needs_approval()` correctly identifies require cases (paid API → True)
- [ ] `request_approval()` displays formatted prompt in CLI
- [ ] User can select options and approval is captured
- [ ] All unit tests pass: `pytest tests/test_approval.py`

---

## Go/No-Go Checkpoint 2.3

**GO if:**
- ✅ All 7 success criteria met
- ✅ Bypass rules work for free libraries
- ✅ CLI prompt is clear and functional

**NO-GO if:**
- ❌ Can't load YAML configuration
- ❌ Bypass rules don't work (always requires approval)
- ❌ CLI prompt crashes or hangs

---

## If NO-GO: Rollback Procedures

1. **Can't load YAML:**
   - Hardcode configuration in Python (dict instead of YAML)
   - **Quick fix:** Skip configuration, require approval for everything

2. **Bypass rules don't work:**
   - Simplify to single rule: "free library = auto-approve"
   - **Fallback:** Require approval for all acquisitions (safe default)

3. **CLI prompt issues:**
   - Use simple `input("Approve? (y/n): ")` instead of fancy formatting
   - **Minimum viable:** Just yes/no, no option selection

---

## Test Commands

```bash
# Test configuration loading
python -c "
import yaml
with open('config/approval_settings.yaml') as f:
    config = yaml.safe_load(f)
print('✓ Config loaded')
print(f'Bypass rules: {len(config[\"approval_rules\"][\"bypass_conditions\"])}')
"

# Test approval workflow
pytest tests/test_approval.py -v

# Manual CLI test
python -c "
from src.level2.crawl.approval_workflow import ApprovalWorkflow
from src.level2.crawl.build_vs_buy_analyzer import BuildVsBuyRecommendation, BuildOption, AcquisitionStrategy

workflow = ApprovalWorkflow()

# Create dummy recommendation
recommendation = BuildVsBuyRecommendation(
    recommendation=AcquisitionStrategy.BUILD,
    build_option=BuildOption(
        implementation_time_hours=2.0,
        estimated_cost_usd=300.0,
        complexity_score=0.3,
        pros=['Simple'],
        cons=['Time'],
        implementation_notes='Easy'
    ),
    buy_options=[],
    confidence=0.9,
    reasoning='Test',
    total_cost_analysis={'build': 300.0}
)

needs = workflow.needs_approval(recommendation)
print(f'Needs approval: {needs}')
# Should be False (simple build, complexity < 0.7)
"
```

---

## Time Checkpoint

**Should complete by:** Hour 10 of implementation
**If running late:**
- Skip YAML, use Python dict for config
- Skip fancy CLI formatting
- Just implement yes/no approval

---

## Dependencies

**Input:**
- `BuildVsBuyRecommendation` from Milestone 2.2
- Pattern dictionary

**Output:**
- `ApprovalResponse` for Milestone 2.4

**Blocks:**
- Milestone 2.4 (Tool Acquisition needs approval decision)

---

# MILESTONE 2.4: Tool Acquisition Engine

**Goal:** Generate or acquire tools based on approved strategy
**Duration:** 5 hours
**Risk:** High (Claude API code generation is unproven)
**Deliverable:** `src/level2/crawl/tool_acquisition_engine.py`

---

## Tasks

1. **[60 min]** Implement `GeneratedTool` dataclass and base structure
   - Fields: `name`, `code`, `pattern_name`, `acquisition_type`, `metadata`
   - Validation logic

2. **[120 min]** Implement BUILD path (internal tool generation)
   - `_build_tool()` - Use Claude API to generate Python code
   - `_generate_class_name()` - Convert pattern name to PascalCase
   - Template-based code generation prompt
   - Code extraction from Claude's response

3. **[60 min]** Implement BUY_LIBRARY path (library wrapper)
   - `_acquire_library()` - Generate wrapper around existing library
   - Integration with library features
   - Standardized output format

4. **[30 min]** Add code validation
   - Syntax check (compile generated code)
   - Basic smoke test (instantiate class)
   - Save to `src/level2/tools/generated/`

5. **[30 min]** Manual testing with real pattern
   - Generate tool for "Production Readiness" pattern
   - Verify generated code works
   - Test wrapper for `radon` library

---

## Implementation Details

```python
# src/level2/crawl/tool_acquisition_engine.py

import os
from typing import Dict, Optional
from dataclasses import dataclass
from anthropic import Anthropic

@dataclass
class GeneratedTool:
    """A generated or acquired tool."""
    name: str
    code: str
    pattern_name: str
    acquisition_type: str  # 'build', 'library', 'api'
    metadata: Dict

class ToolAcquisitionEngine:
    """
    Implements the approved acquisition strategy.

    BUILD path:
    - Generate tool code using Claude
    - Write tests
    - Validate functionality

    BUY path:
    - For libraries: Install via pip, generate wrapper
    - For APIs: Store credentials, generate client wrapper
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        self.client = Anthropic(api_key=anthropic_api_key or os.getenv("ANTHROPIC_API_KEY"))

    def acquire_tool(
        self,
        pattern: Dict,
        recommendation: 'BuildVsBuyRecommendation',
        approval: 'ApprovalResponse'
    ) -> GeneratedTool:
        """
        Implement the approved acquisition strategy.

        Returns a working tool ready to be registered.
        """
        if approval.selected_option == 'build':
            return self._build_tool(pattern, recommendation.build_option)
        else:
            # Find the selected buy option
            buy_option = next(
                (opt for opt in recommendation.buy_options
                 if opt.name == approval.selected_option),
                None
            )
            if not buy_option:
                raise ValueError(f"Unknown option: {approval.selected_option}")

            if buy_option.type == 'library':
                return self._acquire_library(pattern, buy_option)
            else:
                return self._acquire_api(pattern, buy_option)

    def _build_tool(
        self,
        pattern: Dict,
        build_option: 'BuildOption'
    ) -> GeneratedTool:
        """
        Generate tool code using Claude API.
        """
        class_name = self._generate_class_name(pattern['name'])

        generation_prompt = f"""Generate a production-quality Python tool that automates this pattern.

# Pattern Information
**Name:** {pattern['name']}
**Description:** {pattern['description']}

# Requirements

1. **Class Structure:**
   - Class name: `{class_name}`
   - Main method: `analyze(self, code: str, file_path: str = None) -> dict`
   - Return format: {{'score': float, 'checks': dict, 'issues': list, 'suggestions': list}}

2. **Functionality:**
   Based on the pattern description, implement checks that detect:
   - What the pattern looks for
   - Common issues related to this pattern
   - Suggestions for improvement

3. **Code Quality:**
   - Include comprehensive docstrings
   - Add type hints
   - Handle edge cases (empty input, None, malformed code)
   - Include example usage in __main__ block

4. **Return Structure:**
   ```python
   {{
       'score': 0.0-1.0,  # Overall score
       'checks': {{  # Individual check results
           'check_name': bool,
           ...
       }},
       'issues': [  # Problems found
           "Description of issue",
           ...
       ],
       'suggestions': [  # Recommendations
           "How to fix issue",
           ...
       ]
   }}
   ```

Generate ONLY the Python code. No explanation, no markdown except code block."""

        message = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=3000,
            temperature=0.3,
            system="You are an expert Python developer generating production-quality tools.",
            messages=[{"role": "user", "content": generation_prompt}]
        )

        tool_code = message.content[0].text

        # Extract Python code from markdown if present
        if "```python" in tool_code:
            tool_code = tool_code.split("```python")[1].split("```")[0].strip()
        elif "```" in tool_code:
            tool_code = tool_code.split("```")[1].split("```")[0].strip()

        # Validate syntax
        try:
            compile(tool_code, '<string>', 'exec')
        except SyntaxError as e:
            raise ValueError(f"Generated code has syntax errors: {e}")

        return GeneratedTool(
            name=class_name,
            code=tool_code,
            pattern_name=pattern['name'],
            acquisition_type='build',
            metadata={
                'build_option': build_option.__dict__,
                'generated_by': 'claude-sonnet-4-5'
            }
        )

    def _acquire_library(
        self,
        pattern: Dict,
        buy_option: 'BuyOption'
    ) -> GeneratedTool:
        """
        Install library and generate wrapper code.
        """
        class_name = self._generate_class_name(pattern['name'])

        wrapper_prompt = f"""Generate a Python wrapper class for the '{buy_option.name}' library.

# Pattern
**Name:** {pattern['name']}
**Description:** {pattern['description']}

# Library
**Name:** {buy_option.name}
**Features:** {', '.join(buy_option.features)}
**Installation:** {buy_option.installation_notes}

# Requirements

1. **Class Structure:**
   - Class name: `{class_name}`
   - Import and wrap '{buy_option.name}' library
   - Main method: `analyze(self, code: str, file_path: str = None) -> dict`
   - Return standardized format: {{'score': float, 'checks': dict, 'issues': list, 'suggestions': list}}

2. **Functionality:**
   - Use {buy_option.name} to perform analysis
   - Convert library output to standardized format
   - Handle library-specific errors gracefully
   - Add meaningful interpretation of results

3. **Error Handling:**
   - Try/except around library calls
   - Fallback to safe defaults if library fails
   - Log errors but don't crash

4. **Example:**
   ```python
   tool = {class_name}()
   result = tool.analyze(code_string)
   # Returns: {{'score': 0.75, 'checks': {{...}}, 'issues': [...], 'suggestions': [...]}}
   ```

Generate ONLY the Python code including import statements. No explanation."""

        message = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            temperature=0.3,
            system="You are an expert Python developer creating library wrappers.",
            messages=[{"role": "user", "content": wrapper_prompt}]
        )

        wrapper_code = message.content[0].text

        if "```python" in wrapper_code:
            wrapper_code = wrapper_code.split("```python")[1].split("```")[0].strip()
        elif "```" in wrapper_code:
            wrapper_code = wrapper_code.split("```")[1].split("```")[0].strip()

        # Validate syntax
        try:
            compile(wrapper_code, '<string>', 'exec')
        except SyntaxError as e:
            raise ValueError(f"Generated wrapper has syntax errors: {e}")

        return GeneratedTool(
            name=class_name,
            code=wrapper_code,
            pattern_name=pattern['name'],
            acquisition_type='library',
            metadata={
                'library_name': buy_option.name,
                'library_cost': buy_option.monthly_cost_usd,
                'features': buy_option.features
            }
        )

    def _acquire_api(
        self,
        pattern: Dict,
        buy_option: 'BuyOption'
    ) -> GeneratedTool:
        """
        Generate API client wrapper.
        """
        # Placeholder for WALK phase
        raise NotImplementedError("API acquisition not yet implemented")

    def _generate_class_name(self, pattern_name: str) -> str:
        """Convert pattern name to PascalCase class name."""
        # Remove special characters, convert to PascalCase
        clean_name = pattern_name.replace('&', 'And').replace('-', ' ')
        words = clean_name.split()
        return ''.join(word.capitalize() for word in words)
```

---

## Success Criteria

- [ ] `ToolAcquisitionEngine` initializes with Anthropic API key
- [ ] `_build_tool()` generates syntactically valid Python code
- [ ] Generated code defines a class with `analyze()` method
- [ ] `_acquire_library()` generates wrapper code with correct imports
- [ ] Generated code compiles without syntax errors
- [ ] Manual test: Generate tool for "Production Readiness" → Code looks reasonable
- [ ] Manual test: Generate wrapper for `radon` → Code includes radon import

---

## Go/No-Go Checkpoint 2.4

**GO if:**
- ✅ Can generate syntactically valid Python code
- ✅ Generated code has correct structure (class + analyze method)
- ✅ Code compiles without errors

**NO-GO if:**
- ❌ Claude API fails consistently
- ❌ Generated code has syntax errors
- ❌ Generated code doesn't match expected structure

**This is a CRITICAL milestone** - if tool generation doesn't work, entire Level 2 CRAWL fails

---

## If NO-GO: Rollback Procedures

1. **Claude API fails:**
   - Check API key is valid
   - Check rate limits
   - Try with temperature=0.1 (more deterministic)
   - **Fallback:** Use hardcoded tool templates instead of generation

2. **Generated code has syntax errors:**
   - Add retry logic (try 3 times)
   - Improve generation prompt with more examples
   - **Fallback:** Manually write 2-3 tools as templates

3. **Generated code doesn't match structure:**
   - Add validation step that checks for `analyze()` method
   - Reject and retry if structure is wrong
   - **Minimum viable:** Accept any code that compiles, fix structure manually

---

## Test Commands

```bash
# Test tool generation
python -c "
import os
from src.level2.crawl.tool_acquisition_engine import ToolAcquisitionEngine, GeneratedTool
from src.level2.crawl.build_vs_buy_analyzer import BuildOption

engine = ToolAcquisitionEngine(api_key=os.getenv('ANTHROPIC_API_KEY'))

pattern = {
    'name': 'Production Readiness',
    'description': 'Check code for tests, type hints, error handling, and documentation'
}

build_option = BuildOption(
    implementation_time_hours=4.0,
    estimated_cost_usd=600.0,
    complexity_score=0.3,
    pros=['Control'],
    cons=['Time'],
    implementation_notes='4h estimate'
)

print('Generating tool...')
tool = engine._build_tool(pattern, build_option)

print(f'Tool name: {tool.name}')
print(f'Code length: {len(tool.code)} chars')
print(f'First 200 chars:\\n{tool.code[:200]}...')

# Try to compile
compile(tool.code, '<string>', 'exec')
print('✓ Code compiles successfully')

# Check for analyze method
if 'def analyze' in tool.code:
    print('✓ Has analyze() method')
else:
    print('✗ Missing analyze() method')
"

# Save generated tool to file for inspection
mkdir -p src/level2/tools/generated
python -c "
import os
from src.level2.crawl.tool_acquisition_engine import ToolAcquisitionEngine
from src.level2.crawl.build_vs_buy_analyzer import BuildOption

engine = ToolAcquisitionEngine(api_key=os.getenv('ANTHROPIC_API_KEY'))

pattern = {
    'name': 'Production Readiness',
    'description': 'Check code for tests, type hints, error handling'
}

build_option = BuildOption(
    implementation_time_hours=4.0,
    estimated_cost_usd=600.0,
    complexity_score=0.3,
    pros=[], cons=[], implementation_notes=''
)

tool = engine._build_tool(pattern, build_option)

with open('src/level2/tools/generated/production_readiness.py', 'w') as f:
    f.write(tool.code)

print('✓ Tool saved to src/level2/tools/generated/production_readiness.py')
print('Review the file to verify code quality')
"
```

---

## Time Checkpoint

**Should complete by:** Hour 15 of implementation
**If running late:**
- Skip wrapper generation, focus on BUILD path only
- Use simpler generation prompts
- Accept imperfect code, plan to refine later

**Critical Path:** This milestone must succeed for CRAWL to continue

---

## Dependencies

**Input:**
- `ApprovalResponse` from Milestone 2.3
- `BuildVsBuyRecommendation` from Milestone 2.2
- Pattern dictionary
- Anthropic API key

**Output:**
- `GeneratedTool` object with working code

**Blocks:**
- Milestone 2.5 (Unified Pipeline needs tools to execute)
- Milestone 2.6 (Evolution Engine needs to register tools)

---

# MILESTONE 2.5: Unified Agent Pipeline

**Goal:** Integrate pattern matching, tool execution, and Claude responses
**Duration:** 4 hours
**Deliverable:** `src/level2/crawl/unified_agent_pipeline.py`

---

## Tasks

1. **[60 min]** Create `ToolRegistry` class
   - Store registered tools
   - Map patterns to tools
   - Load and execute tools dynamically

2. **[90 min]** Implement `UnifiedAgentPipeline` class
   - `process()` - Main entry point
   - `_execute_tools()` - Run tools for matched patterns
   - `_build_prompt()` - Create augmented prompt with tool results
   - Claude API integration

3. **[60 min]** Implement pattern matcher integration
   - Reuse Phase 0 pattern definitions
   - Simple keyword matching for now

4. **[30 min]** End-to-end test
   - Register a generated tool
   - Query triggers pattern
   - Tool executes
   - Claude response includes tool results

---

## Implementation Summary

```python
# src/level2/crawl/unified_agent_pipeline.py

from typing import Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic
import os

class ToolRegistry:
    """Registry of available tools mapped to patterns."""

    def __init__(self):
        self.tools = {}  # pattern_name -> [Tool objects]

    def register(self, tool: 'GeneratedTool', pattern_name: str):
        """Register a tool for a pattern."""
        if pattern_name not in self.tools:
            self.tools[pattern_name] = []

        # Load tool code dynamically
        loaded_tool = self._load_tool(tool)
        self.tools[pattern_name].append(loaded_tool)

    def get_tools_for_pattern(self, pattern_name: str):
        """Get all tools for a pattern."""
        return self.tools.get(pattern_name, [])

    def _load_tool(self, tool: 'GeneratedTool'):
        """Dynamically load and instantiate tool from code."""
        # Execute code in isolated namespace
        namespace = {}
        exec(tool.code, namespace)

        # Find the class (should match tool.name)
        tool_class = namespace.get(tool.name)
        if not tool_class:
            # Find first class in namespace
            tool_class = next(
                (v for v in namespace.values() if isinstance(v, type)),
                None
            )

        if not tool_class:
            raise ValueError(f"No class found in generated code for {tool.name}")

        # Instantiate and return
        return tool_class()

class UnifiedAgentPipeline:
    """
    Combines pattern-based prompting with tool execution.
    """

    def __init__(
        self,
        anthropic_api_key: str,
        tool_registry: ToolRegistry
    ):
        self.tool_registry = tool_registry
        self.client = Anthropic(api_key=anthropic_api_key)

    def process(self, query: str, code: str = None) -> dict:
        """
        Process user query through pattern + tool pipeline.

        Args:
            query: User's question
            code: Optional code to analyze

        Returns:
            dict with 'answer', 'patterns_applied', 'tools_used', 'tool_results'
        """
        # Step 1: Match patterns (simplified for CRAWL)
        patterns = self._match_patterns(query)

        # Step 2: Execute tools for matched patterns
        tool_results = {}
        for pattern_name in patterns:
            tools = self.tool_registry.get_tools_for_pattern(pattern_name)
            for tool in tools:
                try:
                    result = tool.analyze(code or query)
                    tool_results[f"{pattern_name}_tool"] = result
                except Exception as e:
                    tool_results[f"{pattern_name}_tool"] = {
                        'error': str(e),
                        'score': 0.0
                    }

        # Step 3: Build augmented prompt
        prompt = self._build_prompt(query, code, patterns, tool_results)

        # Step 4: Claude API call
        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            'answer': response.content[0].text,
            'patterns_applied': patterns,
            'tools_used': list(tool_results.keys()),
            'tool_results': tool_results,
            'metadata': {
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
        }

    def _match_patterns(self, query: str) -> List[str]:
        """Simple keyword-based pattern matching."""
        query_lower = query.lower()
        patterns = []

        # Hardcoded pattern keywords (from Phase 0)
        pattern_keywords = {
            'Production Readiness': ['test', 'production', 'ready', 'deploy', 'error handling'],
            'Gap Analysis': ['missing', 'gap', 'what about', 'incomplete'],
            'Tradeoff Analysis': ['vs', 'versus', 'compare', 'alternative', 'option'],
            # Add more as needed
        }

        for pattern_name, keywords in pattern_keywords.items():
            if any(kw in query_lower for kw in keywords):
                patterns.append(pattern_name)

        return patterns

    def _build_prompt(
        self,
        query: str,
        code: Optional[str],
        patterns: List[str],
        tool_results: Dict
    ) -> str:
        """Build augmented prompt with patterns and tool results."""
        prompt_parts = []

        # System context
        prompt_parts.append("You are an expert coding assistant.")

        # Pattern context
        if patterns:
            prompt_parts.append("\nApply these learned patterns:")
            for pattern in patterns:
                prompt_parts.append(f"- {pattern}")

        # Tool results
        if tool_results:
            prompt_parts.append("\n\nAUTOMATED ANALYSIS RESULTS:")
            for tool_name, result in tool_results.items():
                if 'error' in result:
                    prompt_parts.append(f"\n{tool_name}: Error - {result['error']}")
                    continue

                prompt_parts.append(f"\n{tool_name}:")
                prompt_parts.append(f"  Score: {result.get('score', 0):.0%}")

                checks = result.get('checks', {})
                if checks:
                    prompt_parts.append("  Checks:")
                    for check, passed in checks.items():
                        symbol = "✓" if passed else "✗"
                        prompt_parts.append(f"    {symbol} {check}")

                issues = result.get('issues', [])
                if issues:
                    prompt_parts.append("  Issues found:")
                    for issue in issues:
                        prompt_parts.append(f"    - {issue}")

            prompt_parts.append("\nYOUR TASK:")
            prompt_parts.append("1. Interpret these automated results in context")
            prompt_parts.append("2. Prioritize issues by impact")
            prompt_parts.append("3. Provide specific, actionable recommendations")
            prompt_parts.append("4. Explain WHY each issue matters")

        # User query
        prompt_parts.append(f"\n\nUSER QUERY:\n{query}")

        # Code context
        if code:
            prompt_parts.append(f"\n\nCODE TO ANALYZE:\n```python\n{code}\n```")

        return "\n".join(prompt_parts)
```

---

## Success Criteria

- [ ] `ToolRegistry` can register and retrieve tools
- [ ] `UnifiedAgentPipeline` can process a query end-to-end
- [ ] Pattern matching identifies at least 1 pattern for test queries
- [ ] Tools execute successfully for matched patterns
- [ ] Claude response includes interpretation of tool results
- [ ] Test case: Query about "production readiness" → Tool runs → Response includes tool data

---

## Go/No-Go Checkpoint 2.5

**GO if:**
- ✅ End-to-end flow works for at least 1 test case
- ✅ Tool executes and returns structured results
- ✅ Claude response references tool results

**NO-GO if:**
- ❌ Can't load generated tools dynamically
- ❌ Tool execution crashes
- ❌ Claude response ignores tool results

---

## If NO-GO: Rollback Procedures

1. **Can't load tools dynamically:**
   - Use manual imports instead of exec()
   - **Fallback:** Hardcode tool instances, skip registry

2. **Tool execution crashes:**
   - Wrap in try/except, log errors
   - Continue with prompt-only response if tools fail
   - **Minimum viable:** Tools optional, prompt-only works

3. **Claude ignores tool results:**
   - Improve prompt to emphasize tool results
   - Add "CRITICAL: Use the automated analysis above"
   - **Acceptable:** Even if not perfect, keep trying

---

## Test Commands

```bash
# End-to-end integration test
python -c "
import os
from src.level2.crawl.unified_agent_pipeline import UnifiedAgentPipeline, ToolRegistry
from src.level2.crawl.tool_acquisition_engine import ToolAcquisitionEngine, GeneratedTool
from src.level2.crawl.build_vs_buy_analyzer import BuildOption

# Setup
registry = ToolRegistry()
engine = ToolAcquisitionEngine(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Generate a tool
pattern = {
    'name': 'Production Readiness',
    'description': 'Check for tests, type hints, error handling'
}
build_option = BuildOption(4.0, 600.0, 0.3, [], [], '')
tool = engine._build_tool(pattern, build_option)

# Register tool
registry.register(tool, 'Production Readiness')

# Create pipeline
pipeline = UnifiedAgentPipeline(
    anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
    tool_registry=registry
)

# Test query
code = '''
def process_data(data):
    return data.upper()
'''

result = pipeline.process(
    query='Is this code production ready?',
    code=code
)

print('Patterns applied:', result['patterns_applied'])
print('Tools used:', result['tools_used'])
print('Tool results:', result['tool_results'])
print('\\nClaude response:', result['answer'][:300])
"
```

---

## Time Checkpoint

**Should complete by:** Hour 19 of implementation
**If running late:**
- Simplify pattern matching (hardcode 2-3 patterns)
- Skip error handling, assume tools work
- Use basic prompt template

---

## Dependencies

**Input:**
- `GeneratedTool` from Milestone 2.4
- Pattern definitions from Phase 0

**Output:**
- Working end-to-end pipeline

**Blocks:**
- Milestone 2.6 (Evolution Engine uses this pipeline)

---

# MILESTONE 2.6: Capability Evolution Engine

**Goal:** Monitor usage and trigger autonomous tool generation
**Duration:** 3 hours
**Deliverable:** `src/level2/crawl/capability_evolution_engine.py`

---

## Tasks

1. **[90 min]** Implement `CapabilityEvolutionEngine` class
   - `monitor_execution()` - Track patterns without tools
   - `trigger_tool_generation()` - Initiate full workflow
   - Frequency tracking with threshold (default: 3)

2. **[60 min]** Integrate all components
   - Call gap detector
   - Call build vs buy analyzer
   - Call approval workflow
   - Call tool acquisition engine
   - Register generated tool

3. **[30 min]** End-to-end test
   - Simulate 3 queries for same pattern
   - Verify tool generation triggers automatically
   - Verify tool is registered and used on 4th query

---

## Implementation Summary

```python
# src/level2/crawl/capability_evolution_engine.py

from typing import Dict
from collections import defaultdict

class CapabilityEvolutionEngine:
    """
    Monitors pattern matching and tool usage to identify gaps.
    Triggers tool generation when patterns consistently lack tools.
    """

    def __init__(
        self,
        gap_detector,
        build_vs_buy_analyzer,
        approval_workflow,
        tool_acquisition,
        tool_registry,
        threshold: int = 3
    ):
        self.gap_detector = gap_detector
        self.build_vs_buy_analyzer = build_vs_buy_analyzer
        self.approval_workflow = approval_workflow
        self.tool_acquisition = tool_acquisition
        self.tool_registry = tool_registry
        self.threshold = threshold

        # Track how often patterns appear without tools
        self.gap_frequency = defaultdict(int)

    def monitor_execution(self, execution_result: Dict):
        """
        After each execution, check if we should generate tools.
        """
        patterns_without_tools = execution_result.get('patterns_without_tools', [])

        for pattern_name in patterns_without_tools:
            self.gap_frequency[pattern_name] += 1

            # Check if we've hit threshold
            if self.gap_frequency[pattern_name] >= self.threshold:
                print(f"\n🔍 Capability gap detected for '{pattern_name}'")
                print(f"   Triggered {self.gap_frequency[pattern_name]} times")

                # Trigger tool generation
                self.trigger_tool_generation(pattern_name)

                # Reset counter
                self.gap_frequency[pattern_name] = 0

    def trigger_tool_generation(self, pattern_name: str):
        """
        Initiate build vs buy analysis and tool acquisition.
        """
        print(f"\n{'='*80}")
        print(f"INITIATING TOOL ACQUISITION FOR: {pattern_name}")
        print(f"{'='*80}")

        # Get pattern details (would load from patterns.json in real impl)
        pattern = {
            'name': pattern_name,
            'description': f'Automated analysis for {pattern_name}'
        }

        # Step 1: Capability assessment
        print("\n[1/5] Assessing capability gap...")
        capability_status = self.gap_detector.assess_capability(pattern)

        if capability_status.exists:
            print("   ✓ We can build this with existing capabilities")
        else:
            print(f"   ✗ Gap detected: {capability_status.gap_description}")

        # Step 2: Build vs buy analysis
        print("\n[2/5] Analyzing build vs buy options...")
        recommendation = self.build_vs_buy_analyzer.analyze(
            pattern, capability_status
        )
        print(f"   Recommendation: {recommendation.recommendation.value.upper()}")
        print(f"   Confidence: {recommendation.confidence:.0%}")

        # Step 3: Approval workflow
        print("\n[3/5] Checking approval requirements...")
        if self.approval_workflow.needs_approval(recommendation):
            print("   ⚠️  Human approval required")
            approval = self.approval_workflow.request_approval(
                recommendation, pattern
            )
        else:
            print("   ✓ Auto-approved (meets bypass criteria)")
            from src.level2.crawl.approval_workflow import ApprovalResponse
            approval = ApprovalResponse(
                approved=True,
                selected_option=recommendation.recommendation.value,
                auto_approved=True
            )

        if not approval.approved:
            print("\n   ✗ Acquisition rejected")
            return

        # Step 4: Acquire tool
        print(f"\n[4/5] Acquiring tool via '{approval.selected_option}'...")
        try:
            tool = self.tool_acquisition.acquire_tool(
                pattern, recommendation, approval
            )
            print(f"   ✓ Tool '{tool.name}' generated successfully")
        except Exception as e:
            print(f"   ✗ Acquisition failed: {e}")
            return

        # Step 5: Register tool
        print("\n[5/5] Registering tool...")
        self.tool_registry.register(tool, pattern_name)
        print(f"   ✓ Tool registered for pattern '{pattern_name}'")

        print(f"\n{'='*80}")
        print(f"✅ TOOL ACQUISITION COMPLETE")
        print(f"   Future queries matching '{pattern_name}' will use this tool")
        print(f"{'='*80}\n")
```

---

## Success Criteria

- [ ] `CapabilityEvolutionEngine` tracks pattern frequencies
- [ ] Triggers tool generation after threshold (3 occurrences)
- [ ] Successfully runs entire workflow (gap detect → buy vs buy → approval → acquisition → registration)
- [ ] Tool is registered and available for future use
- [ ] Test: Simulate 3 queries for "Gap Analysis" → Tool generated on 3rd query → 4th query uses tool

---

## Go/No-Go Checkpoint 2.6

**GO if:**
- ✅ Frequency tracking works
- ✅ Tool generation workflow completes successfully
- ✅ Generated tool is registered and usable

**NO-GO if:**
- ❌ Workflow fails at any step
- ❌ Tool registration doesn't work
- ❌ Threshold never triggers

---

## If NO-GO: Rollback Procedures

1. **Workflow fails:**
   - Identify which step failed (1-5)
   - Debug that component individually
   - **Fallback:** Manual tool generation for now

2. **Tool registration broken:**
   - Debug ToolRegistry.register()
   - Check tool code execution
   - **Minimum viable:** Store tools, manual integration later

3. **Threshold never triggers:**
   - Lower threshold to 1 for testing
   - Add debug logging to see frequency counts
   - **Quick fix:** Manually call trigger_tool_generation()

---

## Test Commands

```bash
# Integration test
python -c "
import os
from src.level2.crawl.capability_evolution_engine import CapabilityEvolutionEngine
from src.level2.crawl.capability_gap_detector import CapabilityGapDetector
from src.level2.crawl.build_vs_buy_analyzer import BuildVsBuyAnalyzer
from src.level2.crawl.approval_workflow import ApprovalWorkflow
from src.level2.crawl.tool_acquisition_engine import ToolAcquisitionEngine
from src.level2.crawl.unified_agent_pipeline import ToolRegistry

# Setup all components
registry = ToolRegistry()
gap_detector = CapabilityGapDetector(registry)
analyzer = BuildVsBuyAnalyzer()
workflow = ApprovalWorkflow()
acquisition = ToolAcquisitionEngine(os.getenv('ANTHROPIC_API_KEY'))

# Create evolution engine with threshold=2 for testing
evolution = CapabilityEvolutionEngine(
    gap_detector=gap_detector,
    build_vs_buy_analyzer=analyzer,
    approval_workflow=workflow,
    tool_acquisition=acquisition,
    tool_registry=registry,
    threshold=2  # Lower for testing
)

# Simulate execution results
for i in range(3):
    print(f'\\n=== Query {i+1} ===')
    execution_result = {
        'patterns_without_tools': ['Gap Analysis']
    }
    evolution.monitor_execution(execution_result)

print('\\n✓ Test complete - tool should have been generated on query 2')
"
```

---

## Time Checkpoint

**Should complete by:** Hour 22 of implementation
**If running late:**
- Skip threshold logic, always trigger immediately
- Skip logging/print statements
- Focus on making workflow run once

---

## Dependencies

**Input:**
- All previous milestones (2.1-2.5)

**Output:**
- Autonomous tool generation system

**Blocks:**
- Milestone 2.7 (Final testing)

---

# MILESTONE 2.7: Testing & Validation

**Goal:** Comprehensive system test with real patterns
**Duration:** 2 hours
**Deliverable:** Working Level 2 CRAWL system + test results

---

## Tasks

1. **[30 min]** Create test script
   - Load 3 patterns from Phase 0
   - Create test queries
   - Expected outputs

2. **[60 min]** Run full system test
   - Query 1: "Is my code production ready?" (no tool yet)
   - Query 2: Same query (frequency: 2)
   - Query 3: Same query (frequency: 3, triggers tool generation)
   - Query 4: Same query (uses generated tool)

3. **[30 min]** Document results
   - Screenshot/log of tool generation workflow
   - Before/after comparison (with vs without tools)
   - Save generated tools to repository

---

## Test Script

```bash
# tests/test_level2_crawl_integration.py

import os
import pytest
from src.level2.crawl.capability_evolution_engine import CapabilityEvolutionEngine
from src.level2.crawl.capability_gap_detector import CapabilityGapDetector
from src.level2.crawl.build_vs_buy_analyzer import BuildVsBuyAnalyzer
from src.level2.crawl.approval_workflow import ApprovalWorkflow
from src.level2.crawl.tool_acquisition_engine import ToolAcquisitionEngine
from src.level2.crawl.unified_agent_pipeline import UnifiedAgentPipeline, ToolRegistry

def test_full_crawl_workflow():
    """
    End-to-end test of Level 2 CRAWL.

    1. Query triggers pattern matching
    2. No tool exists initially
    3. After threshold queries, tool is generated
    4. Future queries use the generated tool
    """
    # Setup
    registry = ToolRegistry()
    gap_detector = CapabilityGapDetector(registry)
    analyzer = BuildVsBuyAnalyzer()
    workflow = ApprovalWorkflow()
    acquisition = ToolAcquisitionEngine(os.getenv('ANTHROPIC_API_KEY'))

    evolution = CapabilityEvolutionEngine(
        gap_detector=gap_detector,
        build_vs_buy_analyzer=analyzer,
        approval_workflow=workflow,
        tool_acquisition=acquisition,
        tool_registry=registry,
        threshold=3
    )

    pipeline = UnifiedAgentPipeline(
        anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
        tool_registry=registry
    )

    test_code = '''
def calculate_total(items):
    return sum(items)
'''

    # Query 1: No tool yet
    print("\n=== QUERY 1: No tool ===")
    result1 = pipeline.process(
        query="Is this code production ready?",
        code=test_code
    )
    assert 'Production Readiness' in result1['patterns_applied']
    assert len(result1['tools_used']) == 0

    # Monitor - frequency 1
    evolution.monitor_execution({
        'patterns_without_tools': ['Production Readiness']
    })

    # Query 2: Still no tool
    print("\n=== QUERY 2: Still no tool ===")
    result2 = pipeline.process(
        query="Check if this is production ready",
        code=test_code
    )
    assert len(result2['tools_used']) == 0

    # Monitor - frequency 2
    evolution.monitor_execution({
        'patterns_without_tools': ['Production Readiness']
    })

    # Query 3: Triggers tool generation
    print("\n=== QUERY 3: TRIGGERING TOOL GENERATION ===")
    # Monitor - frequency 3, should trigger
    evolution.monitor_execution({
        'patterns_without_tools': ['Production Readiness']
    })

    # Verify tool was registered
    tools = registry.get_tools_for_pattern('Production Readiness')
    assert len(tools) > 0, "Tool should have been generated and registered"

    # Query 4: Uses generated tool
    print("\n=== QUERY 4: Using generated tool ===")
    result4 = pipeline.process(
        query="Is this production ready?",
        code=test_code
    )
    assert len(result4['tools_used']) > 0, "Should use generated tool"
    assert result4['tool_results'] is not None

    print("\n✅ FULL CRAWL WORKFLOW TEST PASSED")
    print(f"   Tool generated: {tools[0].__class__.__name__}")
    print(f"   Tool results: {result4['tool_results']}")

if __name__ == '__main__':
    test_full_crawl_workflow()
```

---

## Success Criteria

- [ ] Test script runs without errors
- [ ] Tool generation workflow triggers on 3rd query
- [ ] Generated tool is registered in registry
- [ ] 4th query uses the generated tool
- [ ] Tool results appear in response
- [ ] Claude's response references tool results
- [ ] Generated tool code is saved to `src/level2/tools/generated/`

---

## Go/No-Go Checkpoint 2.7 (FINAL)

**GO if:**
- ✅ All 7 success criteria met
- ✅ Full workflow runs end-to-end
- ✅ Generated tools work correctly

**Level 2 CRAWL is COMPLETE** ✅

**NO-GO if:**
- ❌ Test fails at any step
- ❌ Generated tool doesn't execute
- ❌ Workflow breaks during integration

**Level 2 CRAWL is INCOMPLETE** ❌ - Debug and retry

---

## Final Test Command

```bash
# Run full integration test
pytest tests/test_level2_crawl_integration.py -v -s

# If pytest not available, run directly
python tests/test_level2_crawl_integration.py
```

---

## Time Checkpoint

**Should complete by:** Hour 24 of implementation (3 days total)

---

# PHASE COMPLETE: Level 2 CRAWL

**Congratulations!** If all checkpoints passed, you have:

✅ **Built 7 core components:**
1. Capability Gap Detector
2. Build vs Buy Analyzer
3. Approval Workflow
4. Tool Acquisition Engine
5. Unified Agent Pipeline
6. Capability Evolution Engine
7. Full Integration Tests

✅ **Demonstrated autonomous tool generation:**
- Pattern detection → Gap analysis → Build vs buy → Approval → Tool generation → Tool registration → Tool usage

✅ **Created a self-evolving system:**
- System monitors its own capabilities
- Identifies gaps automatically
- Generates tools to fill gaps
- Uses generated tools in future queries

---

## Next Steps

### Option 1: Deploy and Use CRAWL
- Test with real patterns from Phase 0
- Generate tools for all 10 patterns
- Collect usage data for WALK phase

### Option 2: Proceed to WALK Phase
- External library search (PyPI API integration)
- External API search (RapidAPI integration)
- Tool memory and learning from usage
- Cost tracking and budget management

### Option 3: Document and Demo
- Create demo video showing tool generation
- Write blog post about autonomous capability evolution
- Share with community

---

## Files Created

```
src/level2/crawl/
├── __init__.py
├── capability_gap_detector.py
├── build_vs_buy_analyzer.py
├── approval_workflow.py
├── tool_acquisition_engine.py
├── unified_agent_pipeline.py
└── capability_evolution_engine.py

config/
└── approval_settings.yaml

src/level2/tools/generated/
└── (generated tools will be saved here)

tests/
└── test_level2_crawl_integration.py
```

---

**Document Status:** Complete
**Last Updated:** 2025-01-15
**Version:** 1.0
