# Level 2: Unified Tool-Prompt Synergy Architecture
## Autonomous Capability Evolution with Build vs Buy Analysis

**Document Purpose:** Comprehensive architecture for Level 2 that unifies pattern-based prompting with autonomous tool generation and acquisition. This document describes how tools and prompts work together synergistically, not in competition.

**Created:** 2025-01-14
**Status:** Planning - Ready for Implementation

---

## Table of Contents

1. [Core Philosophy](#core-philosophy)
2. [Unified Architecture Overview](#unified-architecture-overview)
3. [The Synergy: Tools + Prompts](#the-synergy-tools--prompts)
4. [Decision Framework](#decision-framework)
5. [Implementation Components](#implementation-components)
6. [Concrete Examples](#concrete-examples)
7. [Evolution Cycle](#evolution-cycle)
8. [Configuration & Approval Workflow](#configuration--approval-workflow)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Success Metrics](#success-metrics)

---

## Core Philosophy

### The Unified Principle

**Pattern Detection → Capability Assessment → Gap Analysis → Acquisition Strategy → Automation**

Every learned pattern represents a **desired capability**. The system continuously evaluates:

1. **Do we have this capability?** (Present vs Gap)
2. **If gap:** Build internally vs Acquire externally
3. **Cost/benefit analysis** with approval workflow
4. **Automate** the capability as a tool

### Key Insight: Complementary Layers

Tools and prompts are **not separate paths** - they are **complementary layers** that work together:

- **Tools** = Data gathering, mechanical checking, deterministic operations
- **Prompts** = Reasoning, synthesis, creative insight, context-dependent advice

**The Magic:** Tools provide facts and data, prompts provide interpretation and recommendations.

---

## Unified Architecture Overview

### The Complete Flow

```
User Query
    ↓
Pattern Matcher (identifies relevant patterns)
    ↓
    ├─→ Patterns WITHOUT tools → Augmented Prompt → Claude API
    │                                 ↓
    └─→ Patterns WITH tools ──────→ Tool Execution
                                      ↓
                              Tool Results (data)
                                      ↓
                              Augmented Prompt (includes tool results)
                                      ↓
                                  Claude API
                                      ↓
                                  Response
```

### Level 1 vs Level 2 Architecture

**Level 1 (Memory-Augmented Prompting):**
```
User Query → Pattern Matcher → Augmented Prompt → Claude API → Response
```
- Agent learns patterns
- Agent applies patterns via prompts
- **Architecture is static**

**Level 2 (Tool-Augmented Evolution):**
```
User Query → Pattern Matcher → Tool Execution + Augmented Prompt → Response
                     ↓
            Capability Gap Detection
                     ↓
            Build vs Buy Analysis
                     ↓
            Tool Generation/Acquisition
                     ↓
            Tool Registry (Evolving)
```
- Agent learns patterns
- Agent **creates/acquires tools** to automate patterns
- Tools provide data, prompts provide reasoning
- **Architecture evolves** - new capabilities added autonomously

---

## The Synergy: Tools + Prompts

### Core Synergy Patterns

#### Pattern 1: Tool as Data Gatherer, Prompt as Interpreter

**Example: Production Readiness Pattern**

**Without Tools (Level 1):**
```
Prompt: "Check for tests, error handling, type hints, docs..."
Claude: "Looking at your code, I notice:
- Missing error handling for file operations (line 23)
- No type hints on the process_data function
- Docstring is missing examples..."
```

**Problems:**
- Slow (requires full code analysis)
- Inconsistent (might miss mechanical checks)
- Verbose (explains obvious things)

**With Tools (Level 2):**
```
Tool Execution:
ProductionReadinessChecker.analyze(code)
→ Returns: {
    'score': 0.62,
    'checks': {
        'has_tests': False,
        'has_error_handling': True,
        'has_type_hints': False,
        'has_docstring': True,
        'has_logging': False
    },
    'issues': [
        'No test file found for module.py',
        'Missing type hints in process_data()',
        'No logging statements detected'
    ],
    'file_stats': {
        'lines': 157,
        'functions': 8,
        'test_coverage': 0
    }
}

Augmented Prompt:
"AUTOMATED ANALYSIS RESULTS:
Score: 62/100
Checks: [tool results]

YOUR TASK:
1. Interpret these results in context
2. Prioritize issues by impact
3. Provide specific, actionable recommendations
4. Explain WHY each issue matters for production"

Claude Response:
"The automated analysis shows a 62/100 score. Here's what needs attention, prioritized by risk:

HIGH PRIORITY:
1. Zero test coverage (0%) - Production blocker
   - Why: 157 lines with 8 functions means significant logic risk
   - Action: Start with test_process_data() - covers the core workflow
   - Quick win: Add 3 tests for happy path, error case, edge case

MEDIUM PRIORITY:
2. Missing type hints in process_data()
   - Why: This appears to be a core function (referenced 5 times)
   - Action: Add -> Dict[str, Any] return type
   - Benefit: Catches type errors at development time
..."
```

**Benefits:**
- Tool provides **facts** (62/100, missing tests, 0% coverage)
- Claude provides **insight** (prioritization, context, "why", specific actions)
- **Faster** - Tool does mechanical work, Claude focuses on reasoning
- **More accurate** - Tool catches 100% of mechanical issues
- **Better UX** - Structured data + natural language explanation

#### Pattern 2: Tool as Validator, Prompt as Advisor

**Example: Precision Policing Pattern**

```
Tool: PrecisionValidator
- Detects vague claims: "always", "never", "all", "completely"
- Returns: {
    'vague_claims': [
        {'line': 15, 'text': 'This always works', 'confidence': 0.9},
        {'line': 23, 'text': 'completely safe', 'confidence': 0.85}
    ]
  }

Prompt receives tool output:
"The precision validator flagged 2 vague claims:

Line 15: 'This always works'
- Problem: Absolute claim without conditions
- Better: 'This works for valid inputs (strings < 1000 chars)'
- Why: Helps users understand limitations

Line 23: 'completely safe'
- Problem: Security claim without threat model
- Better: 'Safe against XSS when used with sanitized input'
- Why: Explicit about security boundary"
```

**Synergy:** Tool finds imprecise language, prompt rewrites with context.

#### Pattern 3: Tool as Complexity Detector, Prompt as Refactoring Guide

**Example: Complexity Analysis Pattern**

```
Tool: ComplexityAnalyzer (using radon library)
- Calculates cyclomatic complexity
- Returns: {
    'process_data': {'complexity': 15, 'rank': 'C'},
    'validate_input': {'complexity': 8, 'rank': 'B'},
    'overall': 11.5
  }

Prompt receives tool output:
"Your process_data() function has complexity 15 (Rank C - high risk).

REFACTORING STRATEGY:
1. Extract validation (lines 23-45) → validate_inputs()
   - Reduces complexity by ~4 points
   - Makes validation reusable

2. Extract error handling (lines 67-89) → handle_processing_error()
   - Reduces complexity by ~3 points
   - Improves readability

After refactoring, estimated complexity: 6 (Rank A).

Start with step 1 - it's mechanical and low-risk."
```

**Synergy:** Tool quantifies complexity, prompt suggests specific refactoring with effort estimates.

---

## Decision Framework

### The Complete Decision Tree

```
Pattern Detected
    ↓
Capability Assessment
    ↓
┌─────────────────────┐
│ Capability Exists?  │
└─────────────────────┘
    ↓           ↓
   YES         NO (Gap Detected)
    ↓           ↓
Automate    Build vs Buy Analysis
              ↓
    ┌─────────────────────────────────────────┐
    │  BUILD (Internal)   │  BUY (External)   │
    ├─────────────────────┼───────────────────┤
    │ Pros:               │ Pros:             │
    │ - Full control      │ - Immediate       │
    │ - No dependencies   │ - Tested/proven   │
    │ - No API costs      │ - Feature-rich    │
    │ - Custom fit        │ - Maintained      │
    │                     │                   │
    │ Cons:               │ Cons:             │
    │ - Time to build     │ - API costs       │
    │ - Maintenance       │ - Rate limits     │
    │ - May be complex    │ - Dependencies    │
    │ - Limited features  │ - Less control    │
    └─────────────────────┴───────────────────┘
              ↓
    Human Approval Gate (configurable)
              ↓
    Implementation & Tool Creation
              ↓
    Add to Tool Registry
              ↓
    Future queries use this tool
```

### Decision Criteria

**Good Tool Candidates (Automate These):**

1. **Repetitive** - Triggers frequently (priority 1 patterns)
2. **Mechanical** - Can be automated with rules
3. **Deterministic** - Clear pass/fail criteria
4. **Checkable** - Objective validation possible

**Examples:**
- ✅ Production readiness checks (tests, error handling, type hints)
- ✅ Gap analysis (what's missing from a checklist)
- ✅ Precision validation (overly broad claims)
- ✅ Complexity analysis (cyclomatic complexity)

**Bad Tool Candidates (Keep as Prompts):**

1. **Creative** - Requires reasoning and judgment
2. **Subjective** - No clear right answer
3. **Contextual** - Depends heavily on situation
4. **Rare** - Only triggers occasionally

**Examples:**
- ❌ Tradeoff analysis (requires deep reasoning)
- ❌ Challenging logic (context-dependent)
- ❌ Brutal accuracy (creative insight)
- ❌ Mechanistic explanations (teaching skill)

---

## Implementation Components

### 1. Capability Gap Detector

```python
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class CapabilityStatus:
    """Result of capability assessment."""
    exists: bool
    confidence: float
    current_tools: List[str]  # Tools we have that partially address this
    gap_description: str      # What's missing

class CapabilityGapDetector:
    """
    Analyzes patterns to determine if we have the capability.

    Uses a knowledge base of known capabilities:
    - Code analysis: AST parsing, linting, formatting
    - Data retrieval: Local files, databases, caching
    - External data: APIs, web scraping, real-time feeds
    """

    def __init__(self, tool_registry: 'ToolRegistry'):
        self.tool_registry = tool_registry
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
        - "analyze code complexity" → ['ast_parsing', 'metrics_calculation']
        """
        description = pattern.get('description', '').lower()
        capabilities = []

        # Code analysis capabilities
        if any(kw in description for kw in ['parse', 'analyze', 'ast', 'syntax']):
            capabilities.append('code_analysis')

        # External data capabilities
        if any(kw in description for kw in ['fetch', 'api', 'real-time', 'external']):
            capabilities.append('external_api')

        # File system capabilities
        if any(kw in description for kw in ['file', 'directory', 'path']):
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
                'libraries': ['pandas', 'json', 'csv'],
                'complexity': 'low',
                'description': 'Data manipulation and transformation'
            },
            # External capabilities we DON'T have yet
            # These will trigger build vs buy analysis
        }
```

### 2. Build vs Buy Analyzer

```python
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
        gap: CapabilityStatus
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
        gap: CapabilityStatus
    ) -> BuildOption:
        """
        Estimate cost and complexity of building internally.
        """
        # Extract complexity from pattern description
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
        gap: CapabilityStatus
    ) -> List[BuyOption]:
        """
        Search for external libraries and APIs that provide this capability.

        In a real implementation, this would:
        1. Search PyPI for relevant libraries
        2. Search RapidAPI, APIs.guru for APIs
        3. Use LLM to match pattern description to available options
        """
        # Placeholder - in real implementation, use actual search
        options = []

        description = pattern.get('description', '').lower()

        # Example: Code complexity analysis
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

        # Example: Real-time market data
        if 'market' in description or 'stock' in description:
            options.extend([
                BuyOption(
                    name='Alpha Vantage API',
                    type='api',
                    monthly_cost_usd=49.99,
                    one_time_cost_usd=0.0,
                    features=[
                        'Real-time quotes',
                        'Historical data',
                        'Technical indicators',
                        'Forex and crypto'
                    ],
                    limitations=[
                        'Rate limit: 5 calls/min (free), 75 calls/min (paid)',
                        'US markets focus'
                    ],
                    pros=[
                        'Immediate availability',
                        '99.9% uptime SLA',
                        'Comprehensive data',
                        'Well-documented'
                    ],
                    cons=[
                        'Ongoing cost: $49.99/month',
                        'Rate limits on free tier',
                        'Vendor lock-in'
                    ],
                    installation_notes='API key required, RESTful endpoints'
                ),
                BuyOption(
                    name='yfinance',
                    type='library',
                    monthly_cost_usd=0.0,
                    one_time_cost_usd=0.0,
                    features=[
                        'Historical market data',
                        'Company fundamentals',
                        'Options chains'
                    ],
                    limitations=[
                        'Not officially supported by Yahoo',
                        'May break with API changes',
                        'No guaranteed uptime'
                    ],
                    pros=[
                        'Free',
                        'Easy to use',
                        'Popular (10k+ stars)'
                    ],
                    cons=[
                        'Unofficial scraper',
                        'Rate limiting',
                        'No SLA'
                    ],
                    installation_notes='pip install yfinance'
                )
            ])

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

### 3. Approval Workflow Manager

```python
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
        recommendation: BuildVsBuyRecommendation
    ) -> bool:
        """
        Check if this recommendation needs human approval.

        Returns True if approval required, False if can proceed automatically.
        """
        # Check bypass conditions
        bypass_rules = self.config['approval_rules']['bypass_conditions']

        if recommendation.recommendation == AcquisitionStrategy.BUY_LIBRARY:
            # Check if it's a free library
            selected_option = next(
                (opt for opt in recommendation.buy_options
                 if opt.type == 'library' and opt.monthly_cost_usd == 0),
                None
            )
            if selected_option:
                # Free library - check dependency count
                max_deps = next(
                    (rule['max_dependencies']
                     for rule in bypass_rules
                     if rule['type'] == 'free_library'),
                    5
                )
                # In real implementation, check actual dependencies
                # For now, assume free libraries are low-dependency
                return False  # Auto-approve free libraries

        if recommendation.recommendation == AcquisitionStrategy.BUILD:
            # Check if it's simple enough to bypass
            build_option = recommendation.build_option

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
                if recommendation.recommendation == AcquisitionStrategy.BUY_API:
                    selected = recommendation.buy_options[0]
                    if selected.monthly_cost_usd > 0:
                        return True  # Require approval for subscriptions

            if rule['type'] == 'external_api':
                if recommendation.recommendation == AcquisitionStrategy.BUY_API:
                    return True  # Require approval for external APIs

            if rule['type'] == 'complex_build':
                if recommendation.recommendation == AcquisitionStrategy.BUILD:
                    build_option = recommendation.build_option
                    time_limit = rule['min_implementation_time']
                    if build_option.implementation_time_hours * 3600 >= time_limit:
                        return True  # Require approval for complex builds

            if rule['type'] == 'high_cost':
                total_cost = recommendation.total_cost_analysis.get(
                    recommendation.recommendation.value,
                    float('inf')
                )
                if total_cost >= rule['monthly_cost']:
                    return True  # Require approval for high-cost options

        return True  # Default: require approval

    def request_approval(
        self,
        recommendation: BuildVsBuyRecommendation,
        pattern: Dict
    ) -> ApprovalResponse:
        """
        Present recommendation to human for approval.

        In a real implementation, this would:
        - Display recommendation in CLI/UI
        - Send email/Slack notification
        - Wait for user response
        - Handle timeout with default action
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
            print(f"\n  Pros:")
            for pro in recommendation.build_option.pros:
                print(f"    + {pro}")
            print(f"  Cons:")
            for con in recommendation.build_option.cons:
                print(f"    - {con}")

        if recommendation.buy_options:
            print("\n" + "-"*80)
            print("EXTERNAL OPTIONS:")
            for i, option in enumerate(recommendation.buy_options, 1):
                print(f"\n  {i}. {option.name} ({option.type})")
                print(f"     Cost: ${option.monthly_cost_usd}/month")
                print(f"     Features: {len(option.features)}")
                for feature in option.features[:3]:
                    print(f"       - {feature}")
                if len(option.features) > 3:
                    print(f"       ... and {len(option.features) - 3} more")

        print("\n" + "="*80)
        print("APPROVE THIS ACQUISITION?")
        print("  [y] Yes, proceed with recommendation")
        print("  [b] Choose BUILD option")
        for i, option in enumerate(recommendation.buy_options, 1):
            print(f"  [{i}] Choose {option.name}")
        print("  [n] No, cancel")
        print("="*80)

        # Get user input
        choice = input("\nYour choice: ").strip().lower()

        if choice == 'y':
            selected = recommendation.recommendation.value
            if selected == 'build':
                selected_name = 'build'
            else:
                selected_name = recommendation.buy_options[0].name

            return ApprovalResponse(
                approved=True,
                selected_option=selected_name,
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

### 4. Tool Acquisition Engine

```python
import anthropic
from typing import Dict, Optional

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
    - Handle authentication, rate limiting, error handling
    """

    def __init__(self, anthropic_api_key: str):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)

    def acquire_tool(
        self,
        pattern: Dict,
        recommendation: BuildVsBuyRecommendation,
        approval: ApprovalResponse
    ) -> 'GeneratedTool':
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
        build_option: BuildOption
    ) -> 'GeneratedTool':
        """
        Generate tool code using Claude API.

        Similar to the tool generator from Level 2 CRAWL docs.
        """
        class_name = self._generate_class_name(pattern['name'])

        generation_prompt = f"""Generate a production-quality Python tool that automates this pattern.

# Pattern Information
**Name:** {pattern['name']}
**Description:** {pattern['description']}

# Requirements

1. **Class Structure:**
   - Class name: `{class_name}`
   - Main method: `analyze(self, code: str) -> dict`
   - Return format: {{'score': float, 'checks': dict, 'issues': list, 'suggestions': list}}

2. **Functionality:**
   Based on the pattern description, implement checks that detect:
   - What the pattern looks for
   - Common issues related to this pattern
   - Suggestions for improvement

3. **Code Quality:**
   - Include comprehensive docstrings
   - Add type hints
   - Handle edge cases (empty input, None, etc.)
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

# Template to Follow

{pattern.get('template', 'N/A')}

Generate ONLY the Python code. No explanation, no markdown except code block.
"""

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

        return GeneratedTool(
            name=class_name,
            code=tool_code,
            pattern_name=pattern['name'],
            acquisition_type='build',
            metadata={
                'build_option': build_option,
                'generated_by': 'claude-sonnet-4-5'
            }
        )

    def _acquire_library(
        self,
        pattern: Dict,
        buy_option: BuyOption
    ) -> 'GeneratedTool':
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
   - Main method: `analyze(self, code: str) -> dict`
   - Return standardized format: {{'score': float, 'checks': dict, 'issues': list, 'suggestions': list}}

2. **Functionality:**
   - Use {buy_option.name} to perform analysis
   - Convert library output to standardized format
   - Handle library-specific errors gracefully
   - Add meaningful interpretation of results

3. **Example:**
   ```python
   tool = {class_name}()
   result = tool.analyze(code_string)
   # Returns: {{'score': 0.75, 'checks': {{...}}, 'issues': [...], 'suggestions': [...]}}
   ```

Generate ONLY the Python code including import statements.
"""

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
        buy_option: BuyOption
    ) -> 'GeneratedTool':
        """
        Generate API client wrapper.
        """
        class_name = self._generate_class_name(pattern['name'])

        # Similar to library wrapper but for API
        # Would include authentication, rate limiting, error handling
        # Placeholder for now
        raise NotImplementedError("API acquisition not yet implemented")

    def _generate_class_name(self, pattern_name: str) -> str:
        """Convert pattern name to PascalCase class name."""
        clean_name = pattern_name.replace('&', 'And').replace('-', ' ')
        words = clean_name.split()
        return ''.join(word.capitalize() for word in words)

@dataclass
class GeneratedTool:
    """A generated or acquired tool."""
    name: str
    code: str
    pattern_name: str
    acquisition_type: str  # 'build', 'library', 'api'
    metadata: Dict
```

### 5. Unified Agent Pipeline

```python
from typing import Dict, List, Optional
from datetime import datetime
import anthropic

class UnifiedAgentPipeline:
    """
    Combines pattern-based prompting with tool execution.

    Flow:
    1. Match patterns to query
    2. For each pattern:
       - Check if tools exist
       - Execute tools to gather data
       - Collect tool results
    3. Build augmented prompt with:
       - Pattern templates
       - Tool results (if any)
       - Original query
    4. Send to Claude API
    5. Return response (enriched with tool insights)
    """

    def __init__(
        self,
        anthropic_api_key: str,
        pattern_matcher: 'PatternMatcher',
        tool_registry: 'ToolRegistry',
        capability_evolution: 'CapabilityEvolutionEngine'
    ):
        self.pattern_matcher = pattern_matcher
        self.tool_registry = tool_registry
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.capability_evolution = capability_evolution

    def process(self, query: str, context: dict = None) -> dict:
        """
        Process user query through pattern + tool pipeline.
        """
        # Step 1: Match patterns
        patterns = self.pattern_matcher.match(query, context)

        # Step 2: Execute tools for matched patterns
        tool_results = {}
        patterns_without_tools = []

        for pattern in patterns:
            tools = self.tool_registry.get_tools_for_pattern(pattern.name)

            if tools:
                # Execute tools
                for tool in tools:
                    result = tool.execute(context)
                    tool_results[tool.name] = result
            else:
                # No tools for this pattern - capability gap
                patterns_without_tools.append(pattern)

        # Step 3: Build augmented prompt
        prompt = self._build_prompt(
            query=query,
            patterns=patterns,
            tool_results=tool_results,
            context=context
        )

        # Step 4: Claude API call
        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Step 5: Monitor for capability gaps
        execution_result = {
            'answer': response.content[0].text,
            'patterns_applied': [p.name for p in patterns],
            'tools_used': list(tool_results.keys()),
            'tool_data': tool_results,
            'patterns_without_tools': [p.name for p in patterns_without_tools],
            'metadata': {
                'query': query,
                'timestamp': datetime.now(),
                'model': "claude-sonnet-4-5"
            }
        }

        # Feed back to capability evolution
        self.capability_evolution.monitor_execution(execution_result)

        return execution_result

    def _build_prompt(
        self,
        query: str,
        patterns: List,
        tool_results: Dict,
        context: dict
    ) -> str:
        """
        Build augmented prompt with patterns and tool results.
        """
        prompt_parts = []

        # Add system context
        prompt_parts.append("You are an expert coding assistant.")

        # Add pattern context
        if patterns:
            prompt_parts.append("\nApply these learned patterns:")
            for pattern in patterns:
                prompt_parts.append(f"- {pattern.name}: {pattern.description}")

        # Add tool results (if any)
        if tool_results:
            prompt_parts.append("\n\nAUTOMATED ANALYSIS RESULTS:")
            for tool_name, result in tool_results.items():
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
            prompt_parts.append("2. Prioritize issues by impact and effort")
            prompt_parts.append("3. Provide specific, actionable recommendations")
            prompt_parts.append("4. Explain WHY each issue matters")

        # Add user query
        prompt_parts.append(f"\n\nUSER QUERY:\n{query}")

        # Add code context if provided
        if context and 'code' in context:
            prompt_parts.append(f"\n\nCODE:\n{context['code']}")

        return "\n".join(prompt_parts)
```

### 6. Capability Evolution Engine

```python
from typing import Dict
from collections import defaultdict

class CapabilityEvolutionEngine:
    """
    Monitors pattern matching and tool usage to identify gaps.
    Triggers tool generation when patterns consistently lack tools.
    """

    def __init__(
        self,
        gap_detector: CapabilityGapDetector,
        build_vs_buy_analyzer: BuildVsBuyAnalyzer,
        approval_workflow: ApprovalWorkflow,
        tool_acquisition: ToolAcquisitionEngine,
        tool_registry: 'ToolRegistry',
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

        # Get pattern details (would load from patterns.json)
        pattern = {'name': pattern_name, 'description': '...'}  # Placeholder

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
            tool = self.tool_acquisition.acquire(
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

## Concrete Examples

### Example 1: Production Readiness Pattern (Present Capability)

**Scenario:** Pattern exists, no tool yet, can be built internally

```
User Query: "Review this function for production readiness"

Step 1: Pattern Matcher
→ Matches "Production Readiness" pattern

Step 2: Tool Check
→ No tool exists for this pattern
→ Capability gap detected

Step 3: Capability Assessment
→ Can we check for tests, type hints, error handling?
→ YES - We have code analysis capabilities (AST parsing)

Step 4: Build vs Buy
→ BUILD Option:
   - Time: 4 hours
   - Cost: $600
   - Pros: Full control, no dependencies

→ BUY Options:
   - pylint: Free library, linting only
   - mypy: Free library, type checking only
   - No single library covers all checks

→ Recommendation: BUILD
   - Reasoning: Need custom checks specific to our patterns
   - No external tool covers: tests + types + error handling + docs

Step 5: Approval
→ Bypass criteria: Simple internal code (complexity: 0.3)
→ Auto-approved

Step 6: Tool Generation
→ Generate ProductionReadinessChecker class
→ Code:
   ```python
   import ast
   import os

   class ProductionReadinessChecker:
       def analyze(self, code: str, file_path: str = None) -> dict:
           # Parse AST
           tree = ast.parse(code)

           # Check for tests
           has_tests = self._check_for_tests(file_path)

           # Check type hints
           has_type_hints = self._check_type_hints(tree)

           # Check error handling
           has_error_handling = self._check_error_handling(tree)

           # Check docstrings
           has_docstrings = self._check_docstrings(tree)

           # Calculate score
           checks = {
               'has_tests': has_tests,
               'has_type_hints': has_type_hints,
               'has_error_handling': has_error_handling,
               'has_docstrings': has_docstrings
           }
           score = sum(checks.values()) / len(checks)

           # Generate issues and suggestions
           issues = []
           suggestions = []

           if not has_tests:
               issues.append("No test file found")
               suggestions.append("Create test file with pytest")

           if not has_type_hints:
               issues.append("Missing type hints")
               suggestions.append("Add type hints to function signatures")

           return {
               'score': score,
               'checks': checks,
               'issues': issues,
               'suggestions': suggestions
           }
   ```

Step 7: Register Tool
→ Tool added to registry for "Production Readiness" pattern

Step 8: Next Query
User: "Review this other function for production readiness"
→ Pattern matches
→ Tool exists!
→ Execute ProductionReadinessChecker
→ Get structured results
→ Augmented prompt includes tool results
→ Claude provides prioritized recommendations
```

### Example 2: Code Complexity Pattern (Free Library Available)

**Scenario:** Pattern exists, no tool yet, free library available

```
User Query: "Is this function too complex?"

Step 1-3: [Same as Example 1]
→ Pattern: Complexity Analysis
→ No tool exists
→ Capability gap detected

Step 4: Build vs Buy
→ BUILD Option:
   - Time: 8 hours (cyclomatic complexity algorithm)
   - Cost: $1,200

→ BUY Options:
   - radon: Free library, MIT license
     Features: Cyclomatic complexity, maintainability index, Halstead metrics
     Pros: Battle-tested, rich features, free
     Cons: Additional dependency

→ Recommendation: BUY (radon library)
   - Reasoning: Free, proven, more features than we'd build
   - Cost comparison: $0 vs $1,200

Step 5: Approval
→ Bypass criteria: Free library
→ Auto-approved

Step 6: Tool Acquisition
→ Generate wrapper for radon library
→ Code:
   ```python
   from radon.complexity import cc_visit
   from radon.metrics import mi_visit

   class ComplexityAnalyzer:
       def analyze(self, code: str) -> dict:
           # Calculate complexity using radon
           complexity_results = cc_visit(code)
           maintainability = mi_visit(code, multi=True)

           # Find highest complexity function
           max_complexity = 0
           complex_functions = []

           for result in complexity_results:
               if result.complexity > max_complexity:
                   max_complexity = result.complexity

               if result.complexity >= 10:
                   complex_functions.append({
                       'name': result.name,
                       'complexity': result.complexity,
                       'rank': result.rank
                   })

           # Determine if too complex
           is_complex = max_complexity >= 10

           # Calculate score (inverse of complexity)
           score = max(0, 1 - (max_complexity / 20))

           return {
               'score': score,
               'checks': {
                   'acceptable_complexity': not is_complex,
                   'has_maintainability_index': len(maintainability) > 0
               },
               'issues': [
                   f"Function '{f['name']}' has complexity {f['complexity']} (Rank {f['rank']})"
                   for f in complex_functions
               ],
               'suggestions': [
                   "Refactor functions with complexity >= 10",
                   "Extract nested logic into separate functions",
                   "Simplify conditional branches"
               ],
               'metadata': {
                   'max_complexity': max_complexity,
                   'complex_functions': complex_functions,
                   'maintainability': maintainability
               }
           }
   ```

Step 7: Register Tool
→ Tool registered with metadata:
   - Library: radon
   - Cost: Free
   - Installation: pip install radon
```

### Example 3: Real-Time Market Data (Paid API Required)

**Scenario:** Pattern exists, no tool yet, requires external API

```
User Query: "What's the current sentiment on AAPL stock?"

Step 1-3: [Same as previous]
→ Pattern: Real-Time Market Analysis
→ No tool exists
→ Capability gap: Can't fetch real-time market data

Step 4: Build vs Buy
→ BUILD Option:
   - Time: 40 hours (web scraping, parsing, reliability)
   - Cost: $6,000
   - Pros: No ongoing cost
   - Cons: May break, unreliable, maintenance burden

→ BUY Options:
   1. Alpha Vantage API
      - Cost: $49.99/month (or free with limits)
      - Features: Real-time quotes, historical, indicators
      - Pros: Reliable, well-documented, SLA
      - Cons: Ongoing cost, rate limits

   2. yfinance library
      - Cost: Free
      - Features: Historical data, basic quotes
      - Pros: Free, easy to use
      - Cons: Unofficial scraper, no SLA, may break

→ Recommendation: BUY (yfinance for now, Alpha Vantage if needed)
   - Reasoning: Start with free option, upgrade if limits hit
   - Cost: $0/month (yfinance) with option to upgrade

Step 5: Approval
→ Bypass criteria: Free library
→ BUT: yfinance is a web scraper (may be unreliable)
→ REQUIRES APPROVAL

Approval Workflow:
╔═══════════════════════════════════════════════════════════════╗
║ TOOL ACQUISITION APPROVAL REQUEST                             ║
╠═══════════════════════════════════════════════════════════════╣
║ Pattern: Real-Time Market Analysis                            ║
║                                                                ║
║ Recommendation: BUY (yfinance library)                        ║
║ Confidence: 75%                                                ║
║                                                                ║
║ Reasoning:                                                     ║
║ Free option available with basic features. Can upgrade to     ║
║ Alpha Vantage ($49.99/mo) if reliability is an issue.         ║
║                                                                ║
║ COST ANALYSIS (12-month):                                     ║
║   build: $6,000.00                                             ║
║   yfinance: $0.00                                              ║
║   Alpha Vantage: $599.88                                       ║
║                                                                ║
║ EXTERNAL OPTIONS:                                             ║
║   1. yfinance (library)                                        ║
║      Cost: $0/month                                            ║
║      Features: Historical data, basic quotes, fundamentals     ║
║      ⚠️  WARNING: Unofficial scraper, no reliability guarantee ║
║                                                                ║
║   2. Alpha Vantage API (api)                                   ║
║      Cost: $49.99/month                                        ║
║      Features: Real-time quotes, historical, indicators        ║
║      ✓ 99.9% uptime SLA, well-documented                       ║
║                                                                ║
║ APPROVE THIS ACQUISITION?                                     ║
║   [y] Yes, proceed with yfinance (free)                        ║
║   [1] Choose yfinance                                          ║
║   [2] Choose Alpha Vantage (paid)                              ║
║   [b] Build internally                                         ║
║   [n] No, cancel                                               ║
╚═══════════════════════════════════════════════════════════════╝

User Input: y

→ Approved: yfinance library

Step 6: Tool Acquisition
→ Generate wrapper for yfinance
→ Code handles rate limiting, errors, data formatting

Step 7: Tool Memory
→ Store metadata:
   - Canonical use: "Fetch market data for stocks"
   - Edge cases: "May fail during market hours (rate limits), unofficial API"
   - Cost: Free
   - Reliability: Medium (unofficial scraper)
   - Fallback: "Recommend Alpha Vantage if failures occur"
```

---

## Evolution Cycle

### The Four Iterations

```
Iteration 1: Pure Prompting (Level 1)
─────────────────────────────────────
User: "Check for tests"
→ Pattern Matcher: "Production Readiness" pattern
→ Augmented Prompt: "Look for test files, check coverage..."
→ Claude: "I don't see test files. You should add tests for..."

Limitations:
- Slow (full code analysis by LLM)
- Inconsistent (might miss mechanical checks)
- No data collection

Iteration 2: Manual Tool Creation
──────────────────────────────────
User: "Check for tests"
→ Pattern detected
→ Developer manually writes TestChecker tool
→ Tool: {'has_tests': False, 'test_files': [], 'coverage': 0}
→ Augmented Prompt includes tool results
→ Claude: "The automated analysis shows 0% coverage. Priority: Add tests for core functions..."

Improvements:
- Faster (tool handles mechanical work)
- Consistent (tool always checks)
- Data-driven (structured results)

Limitations:
- Manual tool creation (developer time)
- Tools don't evolve automatically

Iteration 3: Automated Tool Generation (Level 2 CRAWL)
───────────────────────────────────────────────────────
User: "Check for code duplication"
→ Pattern detected
→ No tool exists
→ Capability gap detected (frequency: 3)
→ Build vs Buy Analysis:
   - Can detect duplication? NO
   - Search external options...
   - Found: 'radon' library (free, clone detection)
→ Approval: Bypass (free library)
→ Tool Generator: Creates DuplicationDetector (wraps radon)
→ Tool Registry: Adds to available tools
→ Tool: {'duplicates': [...], 'similarity_scores': [...]}
→ Augmented Prompt includes results
→ Claude: "Found 3 duplicate blocks. Refactor by extracting shared logic to utils.py..."

Improvements:
- Autonomous tool creation
- Build vs buy decision-making
- No developer intervention

Iteration 4: Tool Memory & Learning (Level 2 WALK)
───────────────────────────────────────────────────
User: "Audit this API endpoint for security issues"
→ Pattern detected: Security Analysis
→ No tool exists
→ Capability gap
→ Build vs Buy:
   - Search: 'bandit' (free, Python security scanner)
   - vs 'Snyk API' ($99/mo, comprehensive security)
→ Approval: Select 'bandit' (free)
→ Tool Generated: SecurityAuditor (wraps bandit)
→ Tool Memory: Store metadata
   {
     'canonical_use': 'Security audit for Python code',
     'edge_cases': 'Doesn't catch logic flaws, only known patterns',
     'cost': 0,
     'performance': '~100ms for 1000 lines',
     'reliability': 'High (battle-tested)',
     'limitations': [
       'Python only',
       'No custom security rules',
       'False positives on intentional code'
     ]
   }

→ Future queries:
   User: "Check this endpoint for SQL injection"
   → Pattern: Security Analysis
   → Tool exists: SecurityAuditor
   → Tool Memory: "Good for security checks, but doesn't catch logic flaws"
   → Execute tool
   → Results + Memory → Augmented Prompt

Improvements:
- Tools remember their strengths/weaknesses
- System learns when to use which tool
- Automatic tool selection based on context
```

---

## Configuration & Approval Workflow

### Configuration File: `config/approval_settings.yaml`

```yaml
approval_rules:
  # Bypass conditions (auto-approve)
  bypass_conditions:
    - type: free_library
      max_dependencies: 5  # Don't auto-install if it pulls in >5 deps
      description: "Free Python libraries with <5 dependencies"

    - type: internal_code
      max_complexity_score: 0.7  # Bypass if simple to implement
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
  method: "cli_prompt"  # Options: "cli_prompt", "email", "slack", "api_callback"
  timeout: 3600  # seconds to wait for approval
  default_on_timeout: "reject"  # Options: "reject", "approve"

  # Email configuration (if method: "email")
  email:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    from_address: "agent@example.com"
    to_addresses:
      - "developer@example.com"

  # Slack configuration (if method: "slack")
  slack:
    webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    channel: "#agent-approvals"

# Cost configuration
cost_settings:
  hourly_dev_rate: 150.00  # USD per hour for build cost estimation
  monthly_budget: 200.00   # Maximum monthly spend on external services
  warn_threshold: 0.8      # Warn when approaching 80% of budget

# Tool generation settings
tool_generation:
  model: "claude-sonnet-4-5-20250929"
  temperature: 0.3  # Low temperature for consistent code generation
  max_tokens: 3000
  validation:
    run_syntax_check: true
    require_docstrings: true
    require_type_hints: true
    require_tests: false  # Generate tools without tests initially

# Capability gap detection
gap_detection:
  threshold: 3  # Trigger tool generation after 3 occurrences
  window_hours: 24  # Reset counter after 24 hours of inactivity
  patterns_to_monitor:
    - "Production Readiness"
    - "Gap Analysis"
    - "Complexity Analysis"
    - "Precision Policing"
    # Add more patterns as they're learned
```

---

## Implementation Roadmap

### Phase 1: Level 2 CRAWL (Week 1 - Foundation)

**Goal:** Prove the concept of autonomous tool generation with build vs buy

**Deliverables:**
1. `capability_gap_detector.py` - Assess if we can fulfill pattern requirements
2. `build_vs_buy_analyzer.py` - Compare internal vs external options
3. `approval_workflow.py` - Human-in-loop approval with bypass rules
4. `tool_acquisition_engine.py` - Generate/acquire tools
5. `unified_agent_pipeline.py` - Integrate tools + prompts
6. `capability_evolution_engine.py` - Monitor and trigger tool generation
7. `config/approval_settings.yaml` - Configuration file

**Success Criteria:**
- ✅ System detects 3 capability gaps from learned patterns
- ✅ Build vs buy analysis produces recommendations for all 3
- ✅ At least 1 tool auto-approved and generated
- ✅ At least 1 tool requires human approval (demonstrating workflow)
- ✅ Generated tools work and provide structured output
- ✅ Future queries use the generated tools

**Time Estimate:** 20-30 hours

---

### Phase 2: Level 2 WALK (Week 2-3 - External Integration)

**Goal:** Expand to external API/library discovery and integration

**Deliverables:**
1. `external_search.py` - Search PyPI, RapidAPI, APIs.guru
2. `library_analyzer.py` - Evaluate library quality, dependencies, licenses
3. `api_wrapper_generator.py` - Generate API client wrappers with auth, rate limiting
4. `tool_memory.py` - Store and learn from tool usage patterns
5. Enhanced approval workflow with cost tracking

**New Capabilities:**
- Search external libraries automatically
- Search external APIs with pricing comparison
- Generate API wrappers with authentication
- Track tool usage and performance
- Learn when to use which tool

**Success Criteria:**
- ✅ System finds and evaluates external libraries (PyPI)
- ✅ System finds and evaluates external APIs (RapidAPI)
- ✅ At least 1 library wrapper generated and working
- ✅ Tool memory tracks canonical uses and limitations
- ✅ Cost tracking prevents budget overruns

**Time Estimate:** 30-40 hours

---

### Phase 3: Level 2 RUN (Week 4+ - Fine-Tuning Integration)

**Goal:** Fine-tune model to recognize tool opportunities and make decisions

**Deliverables:**
1. Training data generation:
   - Pattern → Capability assessment examples
   - Build vs buy decision examples
   - Tool usage examples with outcomes
2. Fine-tuning pipeline integration
3. Model that suggests tools autonomously
4. Confidence scoring for recommendations

**Training Data Types:**
- 50+ examples of capability gap detection
- 30+ examples of build vs buy decisions with reasoning
- 100+ examples of tool usage with success/failure outcomes
- 20+ examples of when NOT to build a tool

**Success Criteria:**
- ✅ Fine-tuned model detects capability gaps without explicit rules
- ✅ Model makes build vs buy recommendations with reasoning
- ✅ Model learns from tool usage patterns
- ✅ Reduced need for human approval (better auto-decisions)

**Time Estimate:** 40-50 hours + fine-tuning time (integrated with Level 1 RUN)

---

## Success Metrics

### Level 2 CRAWL Success

**Minimum:**
- 1 working tool generated autonomously
- Build vs buy analysis working
- Approval workflow functioning

**Target:**
- 3 tools generated (1 auto-approved, 2 with human approval)
- Tools provide accurate, structured results
- Future queries use generated tools successfully

**Stretch:**
- 5+ tools covering main patterns
- Tools catch issues that prompts alone missed
- Measurable speed improvement (tools execute in <1s)

---

### Level 2 WALK Success

**Minimum:**
- External library search working
- 1 library wrapper generated and functioning
- Tool memory storing metadata

**Target:**
- 2+ external libraries integrated
- API search working (finds 3+ API options per query)
- Tool memory improving tool selection (usage-based)

**Stretch:**
- 10+ tools in registry (mix of built and acquired)
- Cost tracking prevents budget overruns
- Tool performance metrics guide future acquisitions

---

### Level 2 RUN Success

**Minimum:**
- Training data generated (50+ examples)
- Fine-tuning includes tool generation data
- Model suggests tools with reasoning

**Target:**
- Fine-tuned model makes accurate build vs buy decisions (>80% match human choice)
- Auto-approval rate increases (fewer human interventions needed)
- Model learns from tool outcomes

**Stretch:**
- Fully autonomous tool evolution
- Model predicts tool performance before acquisition
- Self-correcting: Replaces poor tools with better options

---

## Appendix A: Complete Synergy Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        USER QUERY                            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
            ┌──────────────────────┐
            │   Pattern Matcher     │
            │  (10 learned patterns)│
            └──────────┬────────────┘
                       ↓
        ┌──────────────┴──────────────┐
        ↓                              ↓
┌───────────────┐              ┌──────────────┐
│ Patterns WITH │              │ Patterns     │
│    tools      │              │ WITHOUT tools│
└───────┬───────┘              └──────┬───────┘
        ↓                              ↓
┌───────────────┐              ┌──────────────┐
│ Execute Tools │              │ Gap Detection│
│ (mechanical)  │              │ (opportunity)│
└───────┬───────┘              └──────┬───────┘
        │                              ↓
        │                      ┌──────────────┐
        │                      │  Capability  │
        │                      │  Assessment  │
        │                      └──────┬───────┘
        │                              ↓
        │                      ┌──────────────┐
        │                      │Build vs Buy  │
        │                      │ Analysis     │
        │                      └──────┬───────┘
        │                              ↓
        │                      ┌──────────────┐
        │                      │  Approval    │
        │                      │  Workflow    │
        │                      └──────┬───────┘
        │                              ↓
        │                      ┌──────────────┐
        │                      │Tool Generator│
        │                      │& Acquisition │
        │                      └──────┬───────┘
        │                              ↓
        │                      ┌──────────────┐
        │                      │ Add to       │
        │                      │Tool Registry │
        │                      └──────────────┘
        │
        └──────────────┬───────────────┘
                       ↓
            ┌──────────────────────┐
            │  Prompt Builder      │
            │                      │
            │ Combines:            │
            │ - Pattern templates  │
            │ - Tool results (data)│
            │ - Original query     │
            └──────────┬───────────┘
                       ↓
            ┌──────────────────────┐
            │    Claude API        │
            │  (reasoning layer)   │
            └──────────┬───────────┘
                       ↓
            ┌──────────────────────┐
            │   Final Response     │
            │                      │
            │ - Tool data          │
            │ - Claude reasoning   │
            │ - Recommendations    │
            └──────────────────────┘
                       ↓
            ┌──────────────────────┐
            │ Capability Evolution │
            │   (feedback loop)    │
            │                      │
            │ - Monitor gaps       │
            │ - Track frequency    │
            │ - Trigger generation │
            └──────────────────────┘
```

---

## Appendix B: Key Design Decisions

### 1. Why Unified Architecture?

**Problem:** Tools and prompts could be separate systems, leading to:
- Duplication (prompt checking what tool already checked)
- Inconsistency (tool says one thing, prompt says another)
- Poor UX (user gets raw tool output without interpretation)

**Solution:** Unified pipeline where:
- Tools provide structured data
- Prompts interpret and contextualize that data
- User gets both facts (from tools) and insight (from prompts)

---

### 2. Why Build vs Buy Analysis?

**Problem:** Always building internally is slow and limited. Always using external tools creates dependencies and costs.

**Solution:** Systematic analysis of:
- Cost (development time vs subscription)
- Features (what we'd build vs what exists)
- Reliability (our code vs battle-tested libraries)
- Control (full ownership vs vendor dependency)

**Benefit:** Data-driven decisions, not gut feeling

---

### 3. Why Human Approval for Some Acquisitions?

**Problem:** Fully autonomous tool acquisition could:
- Exceed budget (expensive APIs)
- Add bad dependencies (unmaintained libraries)
- Make poor decisions (build when better option exists)

**Solution:** Configurable approval workflow:
- Auto-approve: Free libraries, simple builds
- Require approval: Paid APIs, complex builds, high-cost options
- Show analysis: Cost, features, pros/cons, recommendations

**Benefit:** Human oversight for important decisions, automation for obvious ones

---

### 4. Why Capability Gap Detection with Threshold?

**Problem:** Generating a tool after first mention wastes effort if pattern rarely appears.

**Solution:** Track pattern frequency:
- Threshold: 3 occurrences before triggering tool generation
- Window: 24-hour reset (don't count old occurrences)
- Override: User can manually request tool generation

**Benefit:** Tools generated for frequently-used patterns, not one-offs

---

### 5. Why Tool Memory?

**Problem:** Without memory, system doesn't learn from tool usage:
- Can't identify unreliable tools
- Can't learn when to use which tool
- Can't warn about tool limitations

**Solution:** Store metadata for each tool:
- Canonical use cases (when to use)
- Edge cases (when NOT to use)
- Performance metrics (speed, accuracy)
- Cost tracking (API usage)
- Success rate (does it help?)

**Benefit:** System gets smarter over time, learns tool strengths/weaknesses

---

## Conclusion

This unified Level 2 architecture combines the best of both worlds:

**Tools provide:**
- Fast, mechanical checking
- Structured, consistent data
- Objective measurements

**Prompts provide:**
- Contextual interpretation
- Prioritized recommendations
- Creative insight and reasoning

**Together they create:**
- Faster responses (tools pre-process)
- More accurate analysis (tools don't miss things)
- Better UX (data + interpretation)
- Autonomous evolution (build vs buy, approval workflow)
- Cost-conscious decisions (systematic analysis)
- Learning system (tool memory, usage patterns)

The system starts with pure prompting (Level 1), gradually accumulates tools (Level 2 CRAWL), learns to acquire external capabilities (Level 2 WALK), and eventually fine-tunes to make autonomous decisions (Level 2 RUN).

**Next Step:** Begin Level 2 CRAWL implementation with the 201 training examples as our pattern knowledge base.

---

## Data Management & File Locations

### Current Training Data

**Primary Training Data:**
- **Location:** `data/finetuning/train_v3.jsonl`
- **Content:** 201 examples (51 real conversations + 150 synthetic)
- **Status:** Generated, exists locally, NOT committed to git
- **Quality Metrics:**
  - 65% unique prompts (131/201)
  - 95% unique responses (191/201)
  - Covers 10 identified patterns

**Synthetic Data Generation:**
- **OpenAI outputs:** `data/synthetic/openai/*.jsonl`
- **Gemini outputs:** `data/synthetic/gemini/*.jsonl`
- **Intermediate files:** `data/finetuning/train_additional_*.jsonl`

### Source Code Locations

**Level 1 Fine-tuning Infrastructure:**
- **Prompt Library:** `src/level1/run/prompt_library.py`
  - 150 unique prompts across 10 patterns
  - Disjoint distribution: OpenAI gets even indices, Gemini gets odd indices
- **Synthetic Generation:**
  - OpenAI: `src/level1/run/generate_additional_examples.py`
  - Gemini: `src/level1/run/generate_additional_examples_gemini.py`
- **Data Processing:**
  - Validation: `src/level1/run/validate_finetuning_data.py`
  - Splitting: `src/level1/run/create_train_val_split.py`
  - Extraction: `src/level1/run/extract_handcrafted_examples.py`
- **Fine-tuning:**
  - Start: `src/level1/run/start_finetuning.py`
  - Monitor: `src/level1/run/monitor_finetuning.py`

**Level 2 Components (Planned):**
- **Tool Generation:** `src/level2/tools/` (to be created)
- **Capability Detection:** `src/level2/capabilities/` (to be created)
- **Build vs Buy Analysis:** `src/level2/analysis/` (to be created)

### Documentation

**Planning Documents:**
- `docs/03_preference_profile.md` - 10 identified patterns
- `docs/04_training_implementation_plan.md` - Original Level 1 plan
- `docs/05_level2_architectural_changes.md` - Level 2 self-modification vision
- `docs/06_detailed_implementation_roadmap.md` - Milestone-based roadmap
- `docs/07_level2_detailed_roadmap.md` - Detailed L2.1-L2.10 milestones
- `docs/08_synthetic_data_generation.md` - Synthetic data guide
- `docs/09_level2_unified_architecture.md` - This document (unified Level 2 architecture)

**Real Conversations (Pattern Source):**
- `data/conversations/` - Original user conversations used for pattern extraction

### Git Repository Structure

**Branch:** `exploratory`
**Remote:** `https://github.com/kar-ganap/self-evolving-agents`

**Committed:**
- All source code (`src/level1/`, `src/common/`)
- All documentation (`docs/*.md`)
- Infrastructure scripts (`scripts/`)

**NOT Committed (in .gitignore):**
- Training data (`data/finetuning/*.jsonl`)
- Synthetic data (`data/synthetic/**/*.jsonl`)
- API keys (`.env`)
- Model outputs and intermediate files

### Data Versioning Strategy

**Current Approach:**
- Training data versioned by filename: `train_v1.jsonl`, `train_v2.jsonl`, `train_v3.jsonl`
- Git tracks code and documentation only
- Data files stay local (too large, contains sensitive patterns)

**Future Considerations (Level 2):**
- Tool registry will need persistent storage
- Tool usage metrics should be tracked
- Approval decisions should be logged
- Consider using DVC or similar for data versioning if needed

---

**Document Status:** Ready for Implementation
**Last Updated:** 2025-01-14
**Version:** 1.1
