"""
Baseline evaluation for tool acquisition decision model.

Evaluates gpt-4.1-2025-04-14 on the validation set before fine-tuning.

Usage:
    uv run python -m src.level2.run.baseline_eval
"""

import json
import re
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI


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
    expected_tools: List[str]
    predicted_tools: List[str]
    tool_overlap: float  # Jaccard similarity
    raw_response: str


@dataclass
class EvalMetrics:
    """Aggregated evaluation metrics."""
    total: int = 0
    category_correct: int = 0
    auto_approve_correct: int = 0
    tool_overlap_sum: float = 0.0
    by_category: Dict[str, Dict[str, int]] = field(default_factory=dict)
    results: List[EvalResult] = field(default_factory=list)

    @property
    def category_accuracy(self) -> float:
        return self.category_correct / self.total if self.total > 0 else 0.0

    @property
    def auto_approve_accuracy(self) -> float:
        return self.auto_approve_correct / self.total if self.total > 0 else 0.0

    @property
    def avg_tool_overlap(self) -> float:
        return self.tool_overlap_sum / self.total if self.total > 0 else 0.0


def extract_pattern_name(example: Dict[str, Any]) -> str:
    """Extract pattern name from user message."""
    user_content = example["messages"][1]["content"]
    for line in user_content.split("\n"):
        if line.startswith("Pattern:"):
            return line.replace("Pattern:", "").strip()
    return "Unknown"


def extract_category(content: str) -> str:
    """Extract category from assistant response."""
    content_upper = content.upper()

    # Look for explicit recommendation line first
    recommendation_match = None
    for line in content.split("\n"):
        if "RECOMMENDATION:" in line.upper():
            recommendation_match = line.upper()
            break

    if "DO NOT ACQUIRE" in content_upper:
        return "no_gap"

    # Check for BUILD recommendation (even if "Buy Options Evaluated" is mentioned)
    if recommendation_match and "BUILD" in recommendation_match:
        return "build"

    if "CONDITIONAL" in content_upper or "CLARIFYING QUESTIONS NEEDED" in content_upper:
        # Check if it's a paid conditional or truly ambiguous
        if "CANNOT DETERMINE" in content_upper or "NEED MORE INFORMATION" in content_upper:
            return "ambiguous"
        if "/MONTH" in content_upper or "/USER/MONTH" in content_upper:
            return "paid_api"
        return "ambiguous"

    if "/MONTH" in content_upper or "/USER/MONTH" in content_upper:
        return "paid_api"

    if recommendation_match and "BUY" in recommendation_match:
        return "free_library"

    if "BUY" in content_upper or "EXTERNAL LIBRARY" in content_upper:
        return "free_library"

    return "unknown"


def extract_auto_approve(content: str) -> str:
    """Extract auto-approve status from response."""
    content_lower = content.lower()

    # Look for explicit auto-approve line
    for line in content.split("\n"):
        if "auto-approve:" in line.lower():
            line_lower = line.lower()
            if "yes" in line_lower and "no" not in line_lower:
                return "yes"
            elif "no" in line_lower:
                return "no"
            elif "conditional" in line_lower or "n/a" in line_lower:
                return "conditional"

    return "unknown"


def extract_tools(content: str) -> List[str]:
    """Extract recommended tool names from response."""
    tools = []

    # Look for **tool_name** (RECOMMENDED) pattern
    recommended_pattern = r'\*\*([a-zA-Z0-9_-]+)\*\*\s*\(RECOMMENDED\)'
    matches = re.findall(recommended_pattern, content)
    tools.extend(matches)

    # Look for "Acquire X" or "acquire X" pattern
    acquire_pattern = r'[Aa]cquire\s+\*?\*?([a-zA-Z0-9_-]+)\*?\*?'
    matches = re.findall(acquire_pattern, content)
    tools.extend(matches)

    # Deduplicate and lowercase
    return list(set(t.lower() for t in tools if len(t) > 2))


def jaccard_similarity(list1: List[str], list2: List[str]) -> float:
    """Calculate Jaccard similarity between two lists."""
    set1 = set(list1)
    set2 = set(list2)

    if not set1 and not set2:
        return 1.0  # Both empty = perfect match
    if not set1 or not set2:
        return 0.0  # One empty, one not = no match

    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union


def evaluate_example(
    client: OpenAI,
    example: Dict[str, Any],
    model: str = "gpt-4.1-2025-04-14"
) -> EvalResult:
    """Evaluate a single example."""
    # Get expected values from the example
    expected_response = example["messages"][-1]["content"]
    expected_category = extract_category(expected_response)
    expected_auto_approve = extract_auto_approve(expected_response)
    expected_tools = extract_tools(expected_response)
    pattern = extract_pattern_name(example)

    # Run the model
    messages = [
        {"role": "system", "content": example["messages"][0]["content"]},
        {"role": "user", "content": example["messages"][1]["content"]}
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.0,  # Deterministic for eval
        max_tokens=2000
    )

    predicted_response = response.choices[0].message.content
    predicted_category = extract_category(predicted_response)
    predicted_auto_approve = extract_auto_approve(predicted_response)
    predicted_tools = extract_tools(predicted_response)

    return EvalResult(
        pattern=pattern,
        expected_category=expected_category,
        predicted_category=predicted_category,
        category_correct=(expected_category == predicted_category),
        expected_auto_approve=expected_auto_approve,
        predicted_auto_approve=predicted_auto_approve,
        auto_approve_correct=(expected_auto_approve == predicted_auto_approve),
        expected_tools=expected_tools,
        predicted_tools=predicted_tools,
        tool_overlap=jaccard_similarity(expected_tools, predicted_tools),
        raw_response=predicted_response
    )


def run_evaluation(
    val_path: Path,
    model: str = "gpt-4.1-2025-04-14"
) -> EvalMetrics:
    """Run evaluation on validation set."""
    # Load environment
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path, override=True)

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Load validation examples
    examples = []
    with open(val_path, 'r') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    print(f"Evaluating {len(examples)} validation examples with {model}")
    print("=" * 60)

    metrics = EvalMetrics()

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
        metrics.tool_overlap_sum += result.tool_overlap

        # Track by category
        cat = result.expected_category
        if cat not in metrics.by_category:
            metrics.by_category[cat] = {"total": 0, "correct": 0}
        metrics.by_category[cat]["total"] += 1
        if result.category_correct:
            metrics.by_category[cat]["correct"] += 1

        status = "✓" if result.category_correct else "✗"
        print(f"{status} (expected: {result.expected_category}, got: {result.predicted_category})")

    return metrics


def print_report(metrics: EvalMetrics):
    """Print evaluation report."""
    print("\n" + "=" * 60)
    print("BASELINE EVALUATION REPORT")
    print("=" * 60)

    print(f"\nOverall Metrics:")
    print(f"  Category Accuracy:    {metrics.category_accuracy:.1%} ({metrics.category_correct}/{metrics.total})")
    print(f"  Auto-approve Accuracy: {metrics.auto_approve_accuracy:.1%} ({metrics.auto_approve_correct}/{metrics.total})")
    print(f"  Avg Tool Overlap:     {metrics.avg_tool_overlap:.1%}")

    print(f"\nAccuracy by Category:")
    for cat, counts in sorted(metrics.by_category.items()):
        acc = counts["correct"] / counts["total"] if counts["total"] > 0 else 0
        print(f"  {cat}: {acc:.1%} ({counts['correct']}/{counts['total']})")

    # Show errors
    errors = [r for r in metrics.results if not r.category_correct]
    if errors:
        print(f"\nMisclassified Examples ({len(errors)}):")
        for r in errors:
            print(f"  - {r.pattern}")
            print(f"    Expected: {r.expected_category}, Got: {r.predicted_category}")


def save_results(metrics: EvalMetrics, output_path: Path):
    """Save detailed results to JSON."""
    results = {
        "model": "gpt-4.1-2025-04-14",
        "total": metrics.total,
        "category_accuracy": metrics.category_accuracy,
        "auto_approve_accuracy": metrics.auto_approve_accuracy,
        "avg_tool_overlap": metrics.avg_tool_overlap,
        "by_category": metrics.by_category,
        "examples": [
            {
                "pattern": r.pattern,
                "expected_category": r.expected_category,
                "predicted_category": r.predicted_category,
                "category_correct": r.category_correct,
                "expected_auto_approve": r.expected_auto_approve,
                "predicted_auto_approve": r.predicted_auto_approve,
                "auto_approve_correct": r.auto_approve_correct,
                "expected_tools": r.expected_tools,
                "predicted_tools": r.predicted_tools,
                "tool_overlap": r.tool_overlap,
            }
            for r in metrics.results
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: {output_path}")


def main():
    data_dir = Path("data/finetuning")
    val_path = data_dir / "validation.jsonl"
    output_path = data_dir / "baseline_eval_results.json"

    if not val_path.exists():
        print(f"Error: Validation file not found: {val_path}")
        return

    metrics = run_evaluation(val_path, model="gpt-4.1-2025-04-14")
    print_report(metrics)
    save_results(metrics, output_path)


if __name__ == "__main__":
    main()
