"""
Evaluate fine-tuned model vs baseline on held-out test set.

Compares:
- gpt-4.1-2025-04-14 (baseline)
- ft:gpt-4.1-2025-04-14:personal:tool-acquisition-v2:CiaQ8u8b (fine-tuned)

Usage:
    uv run python -m src.level2.run.eval_finetuned
    uv run python -m src.level2.run.eval_finetuned --model fine-tuned  # Eval only fine-tuned
    uv run python -m src.level2.run.eval_finetuned --model baseline    # Eval only baseline
"""

import json
import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any

from dotenv import load_dotenv
from openai import OpenAI


BASELINE_MODEL = "gpt-4.1-2025-04-14"
FINETUNED_MODEL = "ft:gpt-4.1-2025-04-14:personal:tool-acquisition-v2:CiaQ8u8b"

# JSON schema for structured output
EVAL_RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "tool_acquisition_decision",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "analysis": {
                    "type": "string",
                    "description": "Brief analysis of the capability gap and options"
                },
                "category": {
                    "type": "string",
                    "enum": ["free_library", "paid_api", "build", "no_gap", "ambiguous"],
                    "description": "The recommendation category"
                },
                "auto_approve": {
                    "type": "string",
                    "enum": ["yes", "no", "conditional"],
                    "description": "Whether to auto-approve this acquisition"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief reasoning for the decision"
                }
            },
            "required": ["analysis", "category", "auto_approve", "reasoning"],
            "additionalProperties": False
        }
    }
}


@dataclass
class EvalResult:
    """Result of evaluating a single example."""
    pattern: str
    expected_category: str
    predicted_category: str
    category_correct: bool
    expected_auto_approve: str
    predicted_auto_approve: str
    auto_approve_correct: bool


@dataclass
class EvalMetrics:
    """Aggregated evaluation metrics."""
    model: str
    total: int = 0
    category_correct: int = 0
    auto_approve_correct: int = 0
    by_category: Dict[str, Dict[str, int]] = field(default_factory=dict)
    results: List[EvalResult] = field(default_factory=list)

    @property
    def category_accuracy(self) -> float:
        return self.category_correct / self.total if self.total > 0 else 0.0

    @property
    def auto_approve_accuracy(self) -> float:
        return self.auto_approve_correct / self.total if self.total > 0 else 0.0


def extract_pattern_name(example: Dict[str, Any]) -> str:
    """Extract pattern name from user message."""
    user_content = example["messages"][1]["content"]
    for line in user_content.split("\n"):
        if line.startswith("Pattern:"):
            return line.replace("Pattern:", "").strip()
    return "Unknown"


def extract_category(content: str) -> str:
    """Extract category from assistant response content."""
    content_upper = content.upper()

    # Find the Recommendation line in Decision section
    rec_line = ""
    for line in content.split("\n"):
        line_lower = line.lower()
        # Match various recommendation formats
        if ("recommendation:" in line_lower or "primary recommendation:" in line_lower) and "gap" not in line_lower and "refine" not in line_lower:
            rec_line = line.upper()
            break

    # Check for DO NOT ACQUIRE / no gap
    if "DO NOT ACQUIRE" in rec_line:
        return "no_gap"

    # Check for paid API (buy + paid) - check BEFORE build
    if "BUY" in rec_line and "PAID" in rec_line:
        return "paid_api"

    # Check for free library (buy + free/open-source) - check BEFORE build
    if "BUY" in rec_line:
        if "FREE" in rec_line or "OPEN-SOURCE" in rec_line or "OPEN SOURCE" in rec_line:
            return "free_library"
        # "buy" without "paid" or "free" - likely free library
        if "PAID" not in rec_line:
            # But check if it's actually a build recommendation
            if rec_line.strip().startswith("- **RECOMMENDATION:** BUILD") or rec_line.strip().startswith("RECOMMENDATION: BUILD"):
                return "build"
            if "CONDITIONAL" in rec_line:
                return "ambiguous"
            return "free_library"

    # Check for BUILD recommendation (only if not already categorized as buy)
    if "BUILD" in rec_line and "BUY" not in rec_line:
        if "CONDITIONAL" in rec_line:
            return "ambiguous"
        return "build"

    # Fallback checks on full content
    if "DO NOT ACQUIRE" in content_upper:
        return "no_gap"

    # Check for clarifying questions = ambiguous
    if "CLARIFYING QUESTIONS" in content_upper or "PLEASE ANSWER THESE" in content_upper:
        return "ambiguous"

    return "unknown"


def extract_auto_approve(content: str) -> str:
    """Extract auto-approve status from response."""
    content_lower = content.lower()

    for line in content.split("\n"):
        line_lower = line.lower()
        if "auto-approve:" in line_lower or "auto-approve**:" in line_lower:
            if "yes" in line_lower and "no" not in line_lower.split("yes")[0]:
                return "yes"
            elif "no" in line_lower:
                return "no"
            elif "conditional" in line_lower or "n/a" in line_lower:
                return "conditional"

    return "unknown"


def infer_expected_category(messages: List[Dict]) -> str:
    """Infer expected category from the assistant response."""
    assistant_content = messages[-1]['content']
    return extract_category(assistant_content)


def infer_expected_auto_approve(messages: List[Dict]) -> str:
    """Infer expected auto-approve from the assistant response."""
    assistant_content = messages[-1]['content']
    return extract_auto_approve(assistant_content)


STRUCTURED_SYSTEM_PROMPT = """You are a tool acquisition advisor. Analyze the pattern and respond with a JSON decision.

Categories:
- free_library: Use a free/open-source library
- paid_api: Use a paid API service
- build: Build custom solution internally
- no_gap: No capability gap - existing stdlib/tools sufficient
- ambiguous: Need clarification or conditional recommendation

Auto-approve:
- yes: Safe to auto-approve (low risk, reversible)
- no: Requires human review (high cost, security sensitive)
- conditional: Depends on specific conditions"""


def evaluate_example(
    client: OpenAI,
    example: Dict[str, Any],
    model: str
) -> EvalResult:
    """Evaluate a single example using structured output."""
    # Get expected values from test set
    expected_category = infer_expected_category(example["messages"])
    expected_auto_approve = infer_expected_auto_approve(example["messages"])
    pattern = extract_pattern_name(example)

    # Build messages with structured output instruction
    user_content = example["messages"][1]["content"]
    messages = [
        {"role": "system", "content": STRUCTURED_SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.0,
        max_tokens=2000,
        response_format=EVAL_RESPONSE_SCHEMA
    )

    # Parse structured JSON response
    predicted_response = response.choices[0].message.content
    try:
        result = json.loads(predicted_response)
        predicted_category = result.get("category", "unknown")
        predicted_auto_approve = result.get("auto_approve", "unknown")
    except json.JSONDecodeError:
        predicted_category = "unknown"
        predicted_auto_approve = "unknown"

    return EvalResult(
        pattern=pattern,
        expected_category=expected_category,
        predicted_category=predicted_category,
        category_correct=(expected_category == predicted_category),
        expected_auto_approve=expected_auto_approve,
        predicted_auto_approve=predicted_auto_approve,
        auto_approve_correct=(expected_auto_approve == predicted_auto_approve),
    )


def run_evaluation(
    client: OpenAI,
    test_path: Path,
    model: str,
    model_label: str
) -> EvalMetrics:
    """Run evaluation on test set."""
    examples = []
    with open(test_path, 'r') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    print(f"\nEvaluating {model_label} ({model})")
    print(f"Test set: {len(examples)} examples")
    print("=" * 60)

    metrics = EvalMetrics(model=model_label)

    for i, example in enumerate(examples):
        pattern = extract_pattern_name(example)
        print(f"[{i+1}/{len(examples)}] {pattern}...", end=" ", flush=True)

        result = evaluate_example(client, example, model)
        metrics.results.append(result)
        metrics.total += 1

        if result.category_correct:
            metrics.category_correct += 1
        if result.auto_approve_correct:
            metrics.auto_approve_correct += 1

        # Track by category
        cat = result.expected_category
        if cat not in metrics.by_category:
            metrics.by_category[cat] = {"total": 0, "correct": 0}
        metrics.by_category[cat]["total"] += 1
        if result.category_correct:
            metrics.by_category[cat]["correct"] += 1

        status = "Y" if result.category_correct else "X"
        print(f"{status} (exp: {result.expected_category}, got: {result.predicted_category})")

    return metrics


def print_comparison(baseline_metrics: EvalMetrics, finetuned_metrics: EvalMetrics):
    """Print comparison report."""
    print("\n" + "=" * 70)
    print("EVALUATION COMPARISON")
    print("=" * 70)

    print("\n{:<25} {:>15} {:>15} {:>12}".format(
        "Metric", "Baseline", "Fine-tuned", "Delta"
    ))
    print("-" * 70)

    # Category accuracy
    b_acc = baseline_metrics.category_accuracy
    f_acc = finetuned_metrics.category_accuracy
    delta = f_acc - b_acc
    print("{:<25} {:>14.1%} {:>14.1%} {:>+11.1%}".format(
        "Category Accuracy", b_acc, f_acc, delta
    ))

    # Auto-approve accuracy
    b_auto = baseline_metrics.auto_approve_accuracy
    f_auto = finetuned_metrics.auto_approve_accuracy
    delta = f_auto - b_auto
    print("{:<25} {:>14.1%} {:>14.1%} {:>+11.1%}".format(
        "Auto-approve Accuracy", b_auto, f_auto, delta
    ))

    print("\nAccuracy by Category:")
    print("-" * 70)

    all_categories = set(baseline_metrics.by_category.keys()) | set(finetuned_metrics.by_category.keys())
    for cat in sorted(all_categories):
        b_data = baseline_metrics.by_category.get(cat, {"total": 0, "correct": 0})
        f_data = finetuned_metrics.by_category.get(cat, {"total": 0, "correct": 0})

        b_acc = b_data["correct"] / b_data["total"] if b_data["total"] > 0 else 0
        f_acc = f_data["correct"] / f_data["total"] if f_data["total"] > 0 else 0
        delta = f_acc - b_acc

        print("{:<25} {:>14.0%} {:>14.0%} {:>+11.0%}".format(
            cat, b_acc, f_acc, delta
        ))

    # Show improvements and regressions
    print("\nDetailed Results:")
    print("-" * 70)

    improvements = []
    regressions = []

    for b_res, f_res in zip(baseline_metrics.results, finetuned_metrics.results):
        if not b_res.category_correct and f_res.category_correct:
            improvements.append(f_res.pattern)
        elif b_res.category_correct and not f_res.category_correct:
            regressions.append(f_res.pattern)

    if improvements:
        print(f"\nImprovements (baseline wrong -> fine-tuned correct): {len(improvements)}")
        for p in improvements:
            print(f"  + {p}")

    if regressions:
        print(f"\nRegressions (baseline correct -> fine-tuned wrong): {len(regressions)}")
        for p in regressions:
            print(f"  - {p}")


def save_results(baseline: EvalMetrics, finetuned: EvalMetrics, output_path: Path):
    """Save evaluation results to JSON."""
    results = {
        "baseline": {
            "model": BASELINE_MODEL,
            "total": baseline.total,
            "category_accuracy": baseline.category_accuracy,
            "auto_approve_accuracy": baseline.auto_approve_accuracy,
            "by_category": baseline.by_category,
        },
        "finetuned": {
            "model": FINETUNED_MODEL,
            "total": finetuned.total,
            "category_accuracy": finetuned.category_accuracy,
            "auto_approve_accuracy": finetuned.auto_approve_accuracy,
            "by_category": finetuned.by_category,
        },
        "improvement": {
            "category_accuracy": finetuned.category_accuracy - baseline.category_accuracy,
            "auto_approve_accuracy": finetuned.auto_approve_accuracy - baseline.auto_approve_accuracy,
        }
    }

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate fine-tuned vs baseline model")
    parser.add_argument("--test-path", type=Path,
                       default=Path("data/finetuning/test_holdout.jsonl"),
                       help="Path to held-out test set")
    parser.add_argument("--output", type=Path,
                       default=Path("data/finetuning/eval_comparison.json"),
                       help="Output path for results")
    parser.add_argument("--model", choices=["both", "baseline", "fine-tuned"],
                       default="both", help="Which model(s) to evaluate")

    args = parser.parse_args()

    # Load environment
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path, override=True)

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if not args.test_path.exists():
        print(f"Error: Test file not found: {args.test_path}")
        return 1

    baseline_metrics = None
    finetuned_metrics = None

    if args.model in ["both", "baseline"]:
        baseline_metrics = run_evaluation(
            client, args.test_path, BASELINE_MODEL, "Baseline"
        )

    if args.model in ["both", "fine-tuned"]:
        finetuned_metrics = run_evaluation(
            client, args.test_path, FINETUNED_MODEL, "Fine-tuned"
        )

    if baseline_metrics and finetuned_metrics:
        print_comparison(baseline_metrics, finetuned_metrics)
        save_results(baseline_metrics, finetuned_metrics, args.output)
    elif baseline_metrics:
        print(f"\nBaseline Category Accuracy: {baseline_metrics.category_accuracy:.1%}")
    elif finetuned_metrics:
        print(f"\nFine-tuned Category Accuracy: {finetuned_metrics.category_accuracy:.1%}")

    return 0


if __name__ == "__main__":
    exit(main())
