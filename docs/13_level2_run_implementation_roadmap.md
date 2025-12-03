# Level 2 RUN: Detailed Implementation Roadmap
## Fine-Tuning for Autonomous Tool Acquisition Decisions

**Document Purpose:** Step-by-step implementation guide with go/no-go checkpoints, validation tests, and rollback procedures for Level 2 RUN phase.

**Created:** 2025-01-16
**Status:** ✅ COMPLETE (Moderate Success)
**Completed:** 2025-12-03

## Completion Summary

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Category accuracy | 85% | 75% | ⚠️ Moderate |
| Build vs buy (build category) | 60% | 60% | ✅ Met |
| Training examples | 100 | ~100 | ✅ Met |
| Improvement over baseline | +15% | +10% | ⚠️ Moderate |

**Fine-tuned Model:** `ft:gpt-4.1-2025-04-14:personal:tool-acquisition-v2:CiaQ8u8b`

**Key Outcomes:**
- Fine-tuned model achieves 75% accuracy vs 65% baseline (+10%)
- Significant improvement on `build` category: 20% → 60% (+40%)
- Perfect 100% on `paid_api` and `no_gap` categories
- System integration complete with `BuildVsBuyAnalyzer`

**Prerequisites:**
- Phase 0 complete (base GPT-4.1 + system prompting = 80% pattern adherence)
- Level 2 CRAWL complete (milestones 2.1-2.7)
- Level 2 WALK complete (milestones 2.8-2.13)

---

## Executive Summary

### Goal
Fine-tune GPT-4.1 to autonomously:
1. Detect capability gaps from patterns
2. Make build vs buy decisions with reasoning
3. Recommend tool acquisitions with confidence scores
4. Learn from tool usage outcomes

### Key Insight from Phase 0
Base GPT-4.1 already outperforms fine-tuned GPT-4.1 for pattern application (80% vs 64.4%). Level 2 RUN focuses on **tool acquisition decision-making**, NOT general pattern application. This is a different task with different training objectives.

### Success Criteria
| Metric | Minimum | Target | Stretch |
|--------|---------|--------|---------|
| Gap detection accuracy | 70% | 85% | 95% |
| Build vs buy match rate | 60% vs human | 80% vs human | 90% vs human |
| Training examples | 100 | 200 | 300+ |
| Auto-approval rate increase | 10% | 25% | 40% |

### Time Estimate
- Training data generation: 15-20 hours
- Fine-tuning setup & execution: 3-5 hours
- Validation & integration: 5-8 hours
- **Total**: 23-33 hours (3-4 working days)

---

## Quick Reference: Milestone Overview

| Milestone | Duration | Risk | Deliverable | Status |
|-----------|----------|------|-------------|--------|
| **2.14** | 6h | Medium | Training data generator | ✅ Complete |
| **2.15** | 4h | Low | Example quality validator | ✅ Complete |
| **2.16** | 5h | Medium | Fine-tuning pipeline | ✅ Complete |
| **2.17** | 3h | Medium | Evaluation framework | ✅ Complete |
| **2.18** | 4h | High | System integration | ✅ Complete |
| **2.19** | 2h | Low | Testing & validation | ✅ Complete |

**Total Time:** 24 hours (3 working days)
**Actual Time:** ~20 hours
**Risk Level:** Mitigated - fine-tuning provided moderate improvement

---

# MILESTONE 2.14: Training Data Generation

**Goal:** Generate high-quality training examples for tool acquisition decisions
**Duration:** 6 hours
**Deliverable:** `src/level2/run/training_data_generator.py`

---

## Tradeoff Analysis: Data Quality vs Quantity

### Option A: Human-Curated Examples (High Quality, Low Quantity)
**Pros:**
- Highest quality, captures real decision-making
- No hallucination risk
- Authentic reasoning patterns

**Cons:**
- Very time-consuming (30min per example)
- Limited to ~20-30 examples realistically
- Expensive ($150/hour human time)

**Estimate:** 20 examples, $300 cost

### Option B: Synthetic Generation with GPT-4o (Medium Quality, High Quantity)
**Pros:**
- Can generate 100+ examples quickly
- Diverse scenarios
- Low cost (~$5 for 200 examples)

**Cons:**
- Risk of hallucination/poor reasoning
- May inherit GPT-4o biases
- Requires validation

**Estimate:** 200 examples, $5 cost

### Option C: Hybrid Approach (Balanced)
**Pros:**
- 20 human-curated seed examples
- 100 synthetic examples based on seeds
- Validation layer catches bad examples

**Cons:**
- Still requires some human time
- Two-stage process

**Estimate:** 120 examples, $100 cost

**Recommendation:** Option C (Hybrid Approach)
**Reasoning:** Based on Phase 0 experience, synthetic data worked well but quality ceiling limited fine-tuned model. Hybrid approach gets best of both worlds.

---

## Tasks

### 1. [90 min] Create seed examples manually

**Process:**
1. Review past CRAWL/WALK execution logs
2. Extract 20 real capability gaps and decisions
3. Document reasoning for each decision

**Example Format:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a tool acquisition advisor. Analyze patterns to determine if tools are needed, recommend build vs buy, and provide confidence scores."
    },
    {
      "role": "user",
      "content": "Pattern: Production Readiness\nDescription: Check code for tests, error handling, type hints, docs\nCurrent capabilities: Can parse AST, can read files\nQuery: Should we build/acquire a tool for this pattern?"
    },
    {
      "role": "assistant",
      "content": "# Capability Gap Analysis\n\n**Gap Exists:** Yes\n**Confidence:** 0.85\n\n## Reasoning\nWhile we can parse AST and read files, we lack:\n- Automated test detection (vs manual inspection)\n- Coverage calculation\n- Consistent scoring across projects\n\n## Build vs Buy Recommendation\n\n**Recommendation:** BUY (External Library)\n**Confidence:** 0.90\n\n### Analysis\n\n**Build Option:**\n- Est. time: 12 hours\n- Cost: $1,800 (at $150/hour)\n- Features: Custom to our needs\n- Maintenance: Ongoing burden\n\n**Buy Options:**\n1. **pytest-cov** (RECOMMENDED)\n   - Cost: Free\n   - Features: Coverage reporting, multiple formats\n   - Maturity: 0.95 (battle-tested)\n   - Setup time: 30 min\n\n2. **coverage.py**\n   - Cost: Free\n   - Features: Lower-level coverage API\n   - Maturity: 0.98\n   - Setup time: 60 min\n\n### Decision\nAcquire pytest-cov. Free, mature, saves 11.5 hours vs building.\n\n**Auto-approve:** Yes (free library, high maturity)"
    }
  ]
}
```

**Go Criteria:** 20 seed examples documented with clear reasoning

**No-Go:** If can't find 20 real examples, abort - not enough real-world data

---

### 2. [120 min] Implement synthetic data generator

Create `src/level2/run/training_data_generator.py`:

```python
"""
Training Data Generator for Level 2 RUN

Generates synthetic examples of:
1. Capability gap detection
2. Build vs buy analysis
3. Tool acquisition recommendations
"""

from typing import List, Dict
import json
from pathlib import Path
from openai import OpenAI

class TrainingDataGenerator:
    """Generate training data for tool acquisition fine-tuning."""

    def __init__(self, api_key: str, seed_examples_path: Path):
        self.client = OpenAI(api_key=api_key)
        self.seed_examples = self._load_seed_examples(seed_examples_path)

    def generate_examples(
        self,
        count: int,
        temperature: float = 0.8
    ) -> List[Dict]:
        """
        Generate synthetic training examples.

        Args:
            count: Number of examples to generate
            temperature: Sampling temperature (0.7-0.9 for diversity)

        Returns:
            List of training examples in OpenAI format
        """
        examples = []

        for i in range(count):
            # Rotate through seed examples for variety
            seed = self.seed_examples[i % len(self.seed_examples)]

            # Generate variation
            prompt = self._build_generation_prompt(seed)

            response = self.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "You are a training data generator for tool acquisition AI."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=1500
            )

            generated_example = self._parse_response(response.choices[0].message.content)
            examples.append(generated_example)

        return examples
```

**Go Criteria:** Generator produces 10 synthetic examples that validate successfully

**No-Go:** If >50% of synthetic examples fail validation, revisit generation prompts

---

### 3. [90 min] Create example categories

Generate examples across these categories:

**Category 1: Clear Gap + Free Library Available (30 examples)**
- Pattern has gap
- Free library exists
- Should recommend BUY
- Auto-approve: Yes

**Category 2: Clear Gap + Paid API Available (20 examples)**
- Pattern has gap
- Paid API exists ($10-50/month)
- Should recommend BUY with human approval
- Auto-approve: No

**Category 3: No Gap Detected (20 examples)**
- Pattern requirements already met
- Should recommend NO TOOL NEEDED
- Prevents over-acquisition

**Category 4: Build Recommended (15 examples)**
- Pattern has gap
- No good external options OR
- Build is significantly cheaper/better
- Should recommend BUILD

**Category 5: Ambiguous Cases (15 examples)**
- Multiple viable options
- Should provide analysis with lower confidence
- Require human decision

**Go Criteria:** At least 80 examples across all 5 categories

**No-Go:** If any category has <10 examples, data is unbalanced

---

### 4. [60 min] Validation & deduplication

Create `src/level2/run/validate_training_data.py`:

```python
"""Validate training data quality for Level 2 RUN."""

def validate_example(example: Dict) -> Tuple[bool, List[str]]:
    """
    Validate a training example.

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    # Check structure
    if "messages" not in example:
        issues.append("Missing 'messages' key")
        return False, issues

    messages = example["messages"]

    # Check message count (system + user + assistant)
    if len(messages) != 3:
        issues.append(f"Expected 3 messages, got {len(messages)}")

    # Check roles
    expected_roles = ["system", "user", "assistant"]
    actual_roles = [m["role"] for m in messages]
    if actual_roles != expected_roles:
        issues.append(f"Role order should be {expected_roles}, got {actual_roles}")

    # Check assistant response structure
    assistant_content = messages[2]["content"]

    required_sections = [
        "Capability Gap Analysis",
        "Build vs Buy Recommendation",
        "Confidence:"
    ]

    for section in required_sections:
        if section not in assistant_content:
            issues.append(f"Missing required section: {section}")

    # Check confidence scores are in range
    if "Confidence:" in assistant_content:
        # Extract confidence value
        import re
        confidence_matches = re.findall(r'Confidence:\s*(0\.\d+)', assistant_content)
        for conf in confidence_matches:
            if not (0.0 <= float(conf) <= 1.0):
                issues.append(f"Confidence {conf} out of range [0, 1]")

    return len(issues) == 0, issues
```

**Validation Checks:**
1. Format correctness (OpenAI messages format)
2. Required sections present (Gap Analysis, Build vs Buy, Confidence)
3. Confidence scores in [0, 1] range
4. Decision matches recommendation
5. Deduplication (< 80% similarity to other examples)

**Go Criteria:** >90% of generated examples pass validation

**No-Go:** If <80% pass, regenerate with better prompts

---

## Milestone Completion Checklist

- [ ] 20 human-curated seed examples created
- [ ] Synthetic generator implemented and tested
- [ ] 100+ total examples generated (20 seed + 80+ synthetic)
- [ ] Validation framework created
- [ ] >90% of examples pass validation
- [ ] Examples saved to `data/level2_run_training/train.jsonl`
- [ ] Category distribution verified (all 5 categories covered)

**Go Decision:** Proceed to 2.15 if all checklist items complete

**No-Go Decision:** If <80 total examples or <80% validation pass rate, spend another 2-3 hours improving generation quality before proceeding

---

# MILESTONE 2.15: Quality Validation & Train/Val Split

**Goal:** Ensure training data quality and create proper splits
**Duration:** 4 hours
**Deliverable:** Validated train/val datasets

---

## Tasks

### 1. [120 min] Manual quality review

**Process:**
1. Sample 20 random examples (10% of dataset)
2. Score each on 1-5 scale for:
   - Reasoning quality
   - Decision correctness
   - Confidence calibration
   - Instruction following

**Acceptance Criteria:**
- Average score ≥ 4.0
- No scores of 1 (completely wrong)
- <10% scores of 2 (poor quality)

**Go:** If criteria met, proceed
**No-Go:** If criteria not met, regenerate poor-quality examples

---

### 2. [60 min] Automated validation suite

Implement comprehensive checks:

```python
def validate_dataset(examples: List[Dict]) -> Dict:
    """Run full validation suite on dataset."""

    results = {
        'total': len(examples),
        'passed': 0,
        'failed': 0,
        'issues_by_type': defaultdict(int),
        'confidence_distribution': [],
        'category_distribution': defaultdict(int)
    }

    for ex in examples:
        is_valid, issues = validate_example(ex)

        if is_valid:
            results['passed'] += 1
        else:
            results['failed'] += 1
            for issue in issues:
                results['issues_by_type'][issue] += 1

        # Extract confidence scores
        conf_scores = extract_confidence_scores(ex)
        results['confidence_distribution'].extend(conf_scores)

        # Categorize example
        category = categorize_example(ex)
        results['category_distribution'][category] += 1

    return results
```

**Go:** >90% pass rate
**No-Go:** <85% pass rate, investigate and fix

---

### 3. [60 min] Create train/validation split

**Strategy:**
- 80% train, 20% validation
- Stratified by category (maintain distribution)
- Shuffle with fixed seed for reproducibility

```python
def create_train_val_split(
    examples: List[Dict],
    val_ratio: float = 0.2,
    seed: int = 42
) -> Tuple[List[Dict], List[Dict]]:
    """Create stratified train/validation split."""

    # Group by category
    by_category = defaultdict(list)
    for ex in examples:
        category = categorize_example(ex)
        by_category[category].append(ex)

    train_examples = []
    val_examples = []

    # Split each category
    for category, cat_examples in by_category.items():
        random.seed(seed)
        random.shuffle(cat_examples)

        split_idx = int(len(cat_examples) * (1 - val_ratio))
        train_examples.extend(cat_examples[:split_idx])
        val_examples.extend(cat_examples[split_idx:])

    return train_examples, val_examples
```

**Output:**
- `data/level2_run_training/train.jsonl`
- `data/level2_run_training/validation.jsonl`

**Go:** Both files created with expected counts
**No-Go:** If split is unbalanced (category distribution >10% different between train/val)

---

### 4. [60 min] Baseline evaluation

Before fine-tuning, test base GPT-4.1 on validation set:

```python
def evaluate_base_model(val_examples: List[Dict]) -> Dict:
    """Evaluate base GPT-4.1 on tool acquisition task."""

    results = {
        'gap_detection_accuracy': 0.0,
        'build_vs_buy_match_rate': 0.0,
        'confidence_calibration': 0.0
    }

    # Test on validation set
    for ex in val_examples:
        user_prompt = ex['messages'][1]['content']
        expected_response = ex['messages'][2]['content']

        # Get base model response
        actual_response = get_base_model_response(user_prompt)

        # Compare
        results = update_metrics(results, expected_response, actual_response)

    return results
```

**Expected Baseline:**
- Gap detection: ~60-70% (base model can detect obvious gaps)
- Build vs buy: ~40-50% (harder, requires cost analysis)

**Go:** Baseline established, document metrics
**No-Go:** N/A (informational only)

---

## Milestone Completion Checklist

- [ ] Manual quality review completed (avg score ≥ 4.0)
- [ ] Automated validation passed (>90%)
- [ ] Train/val split created (80/20)
- [ ] Category distribution balanced in both splits
- [ ] Baseline evaluation completed
- [ ] Metrics documented in `data/level2_run_training/baseline_metrics.json`

---

# MILESTONE 2.16: Fine-Tuning Pipeline

**Goal:** Fine-tune GPT-4.1 on tool acquisition task
**Duration:** 5 hours
**Deliverable:** Fine-tuned model

---

## Lessons from Phase 0

### What Went Wrong
1. **Training data quality ceiling**: GPT-4o-generated data limited fine-tuned model
2. **Insufficient examples**: 201 examples for 10 patterns (~20 per pattern)
3. **Over-learning artifacts**: Model learned to ask questions too much

### What to Do Differently
1. **Use GPT-4.1 for generation**: Better quality teacher
2. **More examples per decision type**: 20+ per category
3. **Explicit anti-patterns**: Include examples of when NOT to suggest tools
4. **Confidence calibration**: Train on uncertainty

---

## Tasks

### 1. [60 min] Prepare training files

```bash
# Upload to OpenAI
uv run python -m src.level2.run.upload_training_data
```

Verify format:
```python
def verify_training_format(file_path: Path) -> bool:
    """Verify file is in correct OpenAI fine-tuning format."""

    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                ex = json.loads(line)

                # Check structure
                assert "messages" in ex
                assert len(ex["messages"]) == 3
                assert ex["messages"][0]["role"] == "system"
                assert ex["messages"][1]["role"] == "user"
                assert ex["messages"][2]["role"] == "assistant"

            except Exception as e:
                print(f"Line {line_num}: {e}")
                return False

    return True
```

**Go:** Both train and validation files pass format check
**No-Go:** Fix format issues before uploading

---

### 2. [30 min] Start fine-tuning job

```python
def start_finetuning_job(
    train_file_id: str,
    val_file_id: str,
    model: str = "gpt-4.1-2025-04-14"
) -> str:
    """Start OpenAI fine-tuning job."""

    from openai import OpenAI
    client = OpenAI()

    job = client.fine_tuning.jobs.create(
        training_file=train_file_id,
        validation_file=val_file_id,
        model=model,
        hyperparameters={
            "n_epochs": 3,  # Start conservative
            "batch_size": "auto",
            "learning_rate_multiplier": "auto"
        },
        suffix="tool-acquisition-v1"
    )

    return job.id
```

**Expected Training Time:** 30-90 minutes (depends on example count)

**Go:** Job starts successfully
**No-Go:** If job fails, check file format and quotas

---

### 3. [180 min] Monitor training

Create monitoring script:

```python
def monitor_finetuning(job_id: str, check_interval: int = 60):
    """Monitor fine-tuning job progress."""

    from openai import OpenAI
    import time

    client = OpenAI()

    while True:
        job = client.fine_tuning.jobs.retrieve(job_id)

        print(f"Status: {job.status}")

        if job.status == "succeeded":
            print(f"✓ Fine-tuning complete!")
            print(f"Model: {job.fine_tuned_model}")
            return job.fine_tuned_model

        elif job.status == "failed":
            print(f"✗ Fine-tuning failed: {job.error}")
            return None

        # Show metrics if available
        if hasattr(job, 'metrics'):
            print(f"Metrics: {job.metrics}")

        time.sleep(check_interval)
```

**Go:** Training completes successfully
**No-Go:** If training fails, check error logs and retry with adjusted hyperparameters

---

### 4. [90 min] Hyperparameter tuning (if needed)

If initial training doesn't improve over baseline:

**Try:**
1. Increase epochs (3 → 5)
2. Adjust learning rate (try 0.5x or 2x)
3. Add more training data (generate 50 more examples)

**Decision Tree:**
```
Initial training complete
  ├─ Validation loss decreasing → KEEP
  ├─ Validation loss flat → ADD MORE DATA
  └─ Validation loss increasing → REDUCE EPOCHS or LEARNING RATE
```

**Go:** Validation metrics improve over baseline
**No-Go:** If multiple attempts fail to improve, document findings and recommend staying with base GPT-4.1

---

## Milestone Completion Checklist

- [ ] Training files prepared and uploaded
- [ ] Fine-tuning job started
- [ ] Training completed successfully
- [ ] Fine-tuned model ID documented
- [ ] Validation loss < baseline (or decision made to not use fine-tuned model)

---

# MILESTONE 2.17: Evaluation Framework

**Goal:** Rigorously compare fine-tuned vs base model
**Duration:** 3 hours
**Deliverable:** Evaluation script and comparison report

---

## Tasks

### 1. [90 min] Create evaluation script

```python
def evaluate_model(
    model_name: str,
    test_examples: List[Dict]
) -> Dict:
    """
    Evaluate model on tool acquisition task.

    Metrics:
    1. Gap detection accuracy (binary: gap or no gap)
    2. Build vs buy match rate (3-way: build, buy, none)
    3. Confidence calibration (are 0.8 predictions correct 80% of time?)
    4. Auto-approval accuracy (when model says auto-approve, is it correct?)
    """

    results = {
        'gap_detection': {'tp': 0, 'fp': 0, 'tn': 0, 'fn': 0},
        'build_vs_buy': {'correct': 0, 'total': 0},
        'confidence_bins': defaultdict(list),
        'auto_approve': {'correct': 0, 'total': 0}
    }

    for ex in test_examples:
        user_prompt = ex['messages'][1]['content']
        expected = ex['messages'][2]['content']

        # Get model prediction
        predicted = get_model_response(model_name, user_prompt)

        # Parse responses
        expected_gap = parse_gap_detection(expected)
        predicted_gap = parse_gap_detection(predicted)

        expected_decision = parse_decision(expected)
        predicted_decision = parse_decision(predicted)

        expected_conf = parse_confidence(expected)
        predicted_conf = parse_confidence(predicted)

        # Update metrics
        if expected_gap == predicted_gap:
            if expected_gap:
                results['gap_detection']['tp'] += 1
            else:
                results['gap_detection']['tn'] += 1
        else:
            if predicted_gap:
                results['gap_detection']['fp'] += 1
            else:
                results['gap_detection']['fn'] += 1

        if expected_decision == predicted_decision:
            results['build_vs_buy']['correct'] += 1
        results['build_vs_buy']['total'] += 1

        # Confidence calibration
        results['confidence_bins'][round(predicted_conf, 1)].append(
            1 if expected_decision == predicted_decision else 0
        )

    return compute_final_metrics(results)
```

**Go:** Evaluation runs successfully on both base and fine-tuned models
**No-Go:** Fix parsing issues if evaluation fails

---

### 2. [60 min] Run head-to-head comparison

Compare on 3 datasets:
1. **Validation set** (seen during training)
2. **Test set** (held-out, never seen)
3. **Real-world examples** (from actual CRAWL/WALK execution logs)

**Expected Results:**

| Metric | Base GPT-4.1 | Fine-tuned (Target) |
|--------|--------------|---------------------|
| Gap detection | 65-75% | 80-90% |
| Build vs buy | 45-55% | 75-85% |
| Confidence calibration | Poor | Good |

**Go:** Fine-tuned model outperforms base on ≥2 of 3 metrics
**No-Go:** If fine-tuned doesn't improve, document and recommend base model

---

### 3. [30 min] Generate comparison report

Output format:
```markdown
# Level 2 RUN: Model Comparison Report

**Date:** 2025-01-16
**Base Model:** gpt-4.1-2025-04-14
**Fine-tuned Model:** ft:gpt-4.1-2025-04-14:personal:tool-acquisition-v1:XXXXX

## Results Summary

### Gap Detection
- Base: 70.0% accuracy
- Fine-tuned: 85.0% accuracy
- **Improvement:** +15.0%

### Build vs Buy Decisions
- Base: 50.0% match rate
- Fine-tuned: 80.0% match rate
- **Improvement:** +30.0%

### Confidence Calibration
- Base: RMSE = 0.25
- Fine-tuned: RMSE = 0.12
- **Improvement:** -0.13

## Recommendation

✓ **USE FINE-TUNED MODEL**

Fine-tuned model shows consistent improvement across all metrics.
Expected to reduce human approval requests by ~25%.

## Appendix: Per-Category Performance
[Detailed breakdown...]
```

**Go:** Report generated and saved
**No-Go:** N/A

---

## Milestone Completion Checklist

- [ ] Evaluation framework implemented
- [ ] Base model evaluated
- [ ] Fine-tuned model evaluated
- [ ] Comparison report generated
- [ ] Decision documented (use fine-tuned or stay with base)

---

# MILESTONE 2.18: System Integration

**Goal:** Integrate fine-tuned model into Level 2 system
**Duration:** 4 hours
**Deliverable:** Working end-to-end system

---

## Integration Points

### 1. Update Capability Gap Detector

Modify `src/level2/crawl/capability_gap_detector.py`:

```python
class CapabilityGapDetector:
    def __init__(
        self,
        model: str = "ft:gpt-4.1-2025-04-14:personal:tool-acquisition-v1:XXXXX",
        use_fine_tuned: bool = True
    ):
        self.model = model if use_fine_tuned else "gpt-4.1-2025-04-14"
        self.client = OpenAI()

    def assess_capability(self, pattern: Dict) -> CapabilityStatus:
        """Use fine-tuned model to assess capability gap."""

        prompt = self._build_assessment_prompt(pattern)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2  # Low temperature for consistency
        )

        return self._parse_response(response.choices[0].message.content)
```

---

### 2. Update Build vs Buy Analyzer

Modify `src/level2/crawl/build_vs_buy_analyzer.py`:

```python
class BuildVsBuyAnalyzer:
    def __init__(
        self,
        model: str = "ft:gpt-4.1-2025-04-14:personal:tool-acquisition-v1:XXXXX",
        use_fine_tuned: bool = True
    ):
        self.model = model if use_fine_tuned else "gpt-4.1-2025-04-14"

    def analyze(
        self,
        pattern: Dict,
        external_options: List[BuyOption]
    ) -> BuildVsBuyAnalysis:
        """Use fine-tuned model to recommend build vs buy."""

        prompt = self._build_analysis_prompt(pattern, external_options)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        return self._parse_response(response.choices[0].message.content)
```

---

### 3. Add Configuration

Create `config/level2_run_settings.yaml`:

```yaml
# Level 2 RUN Configuration

fine_tuning:
  enabled: true
  model_id: "ft:gpt-4.1-2025-04-14:personal:tool-acquisition-v1:XXXXX"
  fallback_model: "gpt-4.1-2025-04-14"

  # Confidence thresholds
  auto_approve_threshold: 0.85
  require_human_approval_threshold: 0.60
  reject_threshold: 0.40

evaluation:
  run_comparison: true
  log_decisions: true
  save_trajectories: true

monitoring:
  track_accuracy: true
  alert_on_low_confidence: true
  alert_threshold: 0.50
```

---

## Tasks

### 1. [120 min] Integration implementation

Steps:
1. Update CapabilityGapDetector
2. Update BuildVsBuyAnalyzer
3. Add configuration loading
4. Add model fallback logic
5. Add logging

**Go:** All components updated, tests pass
**No-Go:** If integration breaks existing tests, rollback and fix

---

### 2. [60 min] End-to-end testing

Test complete workflow:
1. Pattern input → Gap detection
2. External search → Build vs buy analysis
3. Recommendation → Approval decision
4. Tool acquisition → Integration

**Test Cases:**
- Free library available (should auto-approve)
- Paid API available (should require approval)
- No external options (should analyze build)
- No gap detected (should skip acquisition)

**Go:** All test cases pass
**No-Go:** Debug failures before proceeding

---

### 3. [60 min] A/B testing framework

Add ability to compare base vs fine-tuned:

```python
class ABTestingConfig:
    """Configuration for A/B testing fine-tuned vs base model."""

    def __init__(self, rollout_percentage: float = 0.5):
        self.rollout_percentage = rollout_percentage

    def should_use_fine_tuned(self, request_id: str) -> bool:
        """Deterministically route request to fine-tuned or base."""
        import hashlib
        hash_val = int(hashlib.md5(request_id.encode()).hexdigest(), 16)
        return (hash_val % 100) < (self.rollout_percentage * 100)
```

**Benefits:**
- Gradual rollout
- Real-world comparison
- Easy rollback if issues

**Go:** A/B testing framework working
**No-Go:** N/A (optional feature)

---

## Milestone Completion Checklist

- [ ] CapabilityGapDetector updated to use fine-tuned model
- [ ] BuildVsBuyAnalyzer updated to use fine-tuned model
- [ ] Configuration file created
- [ ] End-to-end tests passing
- [ ] A/B testing framework (optional) implemented
- [ ] Documentation updated

---

# MILESTONE 2.19: Testing & Validation

**Goal:** Comprehensive testing of Level 2 RUN system
**Duration:** 2 hours
**Deliverable:** All tests passing, system ready for use

---

## Test Suite

### 1. Unit Tests

```python
# tests/level2/run/test_finetuned_gap_detector.py

def test_gap_detection_with_finetuned_model():
    """Test gap detection uses fine-tuned model."""
    detector = CapabilityGapDetector(use_fine_tuned=True)

    pattern = {
        'name': 'Test Coverage Analysis',
        'description': 'Analyze test coverage'
    }

    status = detector.assess_capability(pattern)

    assert status is not None
    assert 0.0 <= status.confidence <= 1.0
    assert status.gap_description is not None

def test_build_vs_buy_with_finetuned_model():
    """Test build vs buy analysis uses fine-tuned model."""
    analyzer = BuildVsBuyAnalyzer(use_fine_tuned=True)

    pattern = {'name': 'Test Coverage', 'description': 'Coverage analysis'}
    external_options = [
        BuyOption(
            source="pytest-cov",
            acquisition_type=AcquisitionType.LIBRARY,
            cost_per_month=0.0,
            maturity_score=0.95
        )
    ]

    analysis = analyzer.analyze(pattern, external_options)

    assert analysis.recommendation in ['build', 'buy', 'none']
    assert 0.0 <= analysis.confidence <= 1.0
```

---

### 2. Integration Tests

```python
# tests/level2/run/test_end_to_end_run.py

def test_end_to_end_with_finetuned_model():
    """Test complete workflow with fine-tuned model."""

    # Setup
    orchestrator = UnifiedWALKOrchestrator(
        enable_cost_tracking=True,
        enable_tool_memory=True,
        use_fine_tuned=True
    )

    pattern = {
        'name': 'API Documentation Generation',
        'description': 'Generate API docs from code'
    }

    missing_capabilities = [
        'Parse docstrings',
        'Generate markdown',
        'Create API reference'
    ]

    # Execute
    result = orchestrator.acquire_external_resource(
        pattern=pattern,
        missing_capabilities=missing_capabilities
    )

    # Verify
    assert result.success is True
    assert result.source in [AcquisitionSource.LIBRARY, AcquisitionSource.API]
    assert result.tool_name is not None
```

---

### 3. Regression Tests

Ensure fine-tuned model doesn't break existing functionality:

```python
def test_backward_compatibility():
    """Test that fine-tuned model works with existing code."""

    # Test with base model
    detector_base = CapabilityGapDetector(use_fine_tuned=False)
    result_base = detector_base.assess_capability(test_pattern)

    # Test with fine-tuned model
    detector_ft = CapabilityGapDetector(use_fine_tuned=True)
    result_ft = detector_ft.assess_capability(test_pattern)

    # Both should return valid results
    assert result_base is not None
    assert result_ft is not None
```

---

## Final Validation

### Performance Benchmarks

Run on validation set and log:
```json
{
  "timestamp": "2025-01-16T10:30:00Z",
  "model": "ft:gpt-4.1-2025-04-14:personal:tool-acquisition-v1:XXXXX",
  "validation_set_size": 40,
  "metrics": {
    "gap_detection_accuracy": 0.85,
    "build_vs_buy_match_rate": 0.80,
    "avg_confidence": 0.75,
    "auto_approval_accuracy": 0.90
  },
  "comparison_to_base": {
    "gap_detection": "+15%",
    "build_vs_buy": "+30%",
    "confidence_calibration": "improved"
  }
}
```

---

## Milestone Completion Checklist

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Regression tests passing
- [ ] Performance benchmarks documented
- [ ] System ready for production use
- [ ] Documentation updated
- [ ] Metrics logged to `data/level2_run_results/final_validation.json`

---

# Success Criteria & Go/No-Go Decision

## Overall Success Criteria

### Minimum Success (Go for Production)
- [ ] Training data: ≥100 examples
- [ ] Fine-tuning: Job completed successfully
- [ ] Gap detection: ≥70% accuracy
- [ ] Build vs buy: ≥60% match rate vs human decisions
- [ ] All integration tests passing

### Target Success
- [ ] Training data: ≥200 examples
- [ ] Gap detection: ≥85% accuracy
- [ ] Build vs buy: ≥80% match rate
- [ ] Auto-approval rate increase: ≥25%
- [ ] Confidence calibration: RMSE < 0.15

### Stretch Success
- [ ] Training data: ≥300 examples
- [ ] Gap detection: ≥95% accuracy
- [ ] Build vs buy: ≥90% match rate
- [ ] Auto-approval rate increase: ≥40%
- [ ] A/B testing showing consistent improvement

---

## Final Decision Framework

### Scenario 1: Fine-tuned model improves on ALL metrics
**Decision:** ✅ Deploy fine-tuned model, retire base model for tool acquisition
**Action:** Update default config to use fine-tuned model

### Scenario 2: Fine-tuned model improves on SOME metrics
**Decision:** ✅ Deploy with A/B testing (50/50 split)
**Action:** Monitor for 1 week, then decide based on real-world performance

### Scenario 3: Fine-tuned model shows NO improvement
**Decision:** ⚠️ Document findings, keep base model
**Action:** Save training data for future attempts, investigate why fine-tuning didn't help

### Scenario 4: Fine-tuned model REGRESSES
**Decision:** ❌ Abort, use base model
**Action:** Document failure, investigate root cause (data quality? overfitting?)

---

## Risk Mitigation

### Rollback Plan
If fine-tuned model causes issues in production:
1. Set `config/level2_run_settings.yaml`: `fine_tuning.enabled: false`
2. System automatically falls back to base GPT-4.1
3. No code changes required

### Monitoring
Track these metrics in production:
- Decision quality (via human feedback)
- Auto-approval accuracy
- Cost impact (fine-tuned model may be more expensive)
- Latency

---

## Appendix: Key Differences from Phase 0

| Aspect | Phase 0 (Pattern Application) | Level 2 RUN (Tool Acquisition) |
|--------|-------------------------------|--------------------------------|
| **Task** | Apply 10 patterns to general coding questions | Detect gaps and recommend tool acquisition |
| **Training Data** | 201 examples across 10 patterns | 100-200 examples across 5 decision categories |
| **Base Model Performance** | 80% pattern adherence | 45-55% build vs buy match rate |
| **Fine-tuning Goal** | Improve pattern application | Improve decision-making accuracy |
| **Success Metric** | Pattern adherence % | Build vs buy match rate |
| **Outcome (Phase 0)** | Base model outperformed fine-tuned (80% vs 64%) | TBD |

**Key Learning:** Fine-tuning works best when base model performs poorly on the task. Phase 0 failed because base GPT-4.1 was already excellent at pattern application. Level 2 RUN has better chance of success because base model struggles with structured decision-making (45-55% baseline).

---

**Document Status:** Ready for Implementation
**Last Updated:** 2025-01-16
**Next Review:** After Milestone 2.14 completion
