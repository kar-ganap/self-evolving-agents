"""
Split training data into train/validation sets, stratified by category.

Ensures 1 cherry-picked seed example per category goes to validation:
- free_library: "Change Impact Analysis" (multi-tool: GitPython + unidiff)
- paid_api: "Production Observability" (Sentry $26/mo, cost justification)
- ambiguous: "Complex Decision Support" (multi-model routing + cost tiers)
- no_gap: "Data Storage" (resist over-engineering to PostgreSQL)
- build: "Problem-Solving Strategy" (meta: loop detection for self-awareness)

Usage:
    uv run python -m src.level2.run.split_data
"""

import json
import random
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any, Set


# Cherry-picked hardest seed examples for validation (by pattern name only)
# These go directly to validation regardless of detected category
VALIDATION_SEED_PATTERNS = {
    "Change Impact Analysis",      # free_library: multi-tool (GitPython + unidiff)
    "Production Observability",    # paid_api: Sentry $26/mo, cost justification
    "Complex Decision Support",    # paid_api: multi-model routing + cost tiers (has CONDITIONAL but is paid)
    "Data Storage",                # no_gap: resist over-engineering to PostgreSQL
    "Problem-Solving Strategy",    # ambiguous: meta loop detection (part tooling, part behavioral)
}


def extract_category(example: Dict[str, Any]) -> str:
    """Extract the category from an example based on its recommendation."""
    assistant_content = example["messages"][-1]["content"]

    if "DO NOT ACQUIRE" in assistant_content:
        return "no_gap"
    elif "CONDITIONAL" in assistant_content or "Clarifying Questions Needed" in assistant_content:
        return "ambiguous"
    elif "BUILD" in assistant_content and "BUY" not in assistant_content:
        return "build"
    elif "/month" in assistant_content or "/user/month" in assistant_content:
        return "paid_api"
    elif "BUY" in assistant_content or "External Library" in assistant_content:
        return "free_library"

    return "unknown"


def extract_pattern_name(example: Dict[str, Any]) -> str:
    """Extract the pattern name from user message."""
    user_content = example["messages"][1]["content"]
    for line in user_content.split("\n"):
        if line.startswith("Pattern:"):
            return line.replace("Pattern:", "").strip()
    return ""


def is_seed_example(example: Dict[str, Any], seed_patterns: Set[str]) -> bool:
    """Check if example is a seed (based on known seed pattern names)."""
    pattern = extract_pattern_name(example)
    return pattern in seed_patterns


def split_data(
    input_path: Path,
    seed_path: Path,
    train_path: Path,
    val_path: Path,
    train_ratio: float = 0.8,
    seed: int = 42
) -> Dict[str, Any]:
    """Split data into train/validation sets with cherry-picked seed examples."""
    random.seed(seed)

    # Load seed examples to identify pattern names
    seed_patterns: Set[str] = set()
    with open(seed_path, 'r') as f:
        for line in f:
            if line.strip():
                ex = json.loads(line)
                seed_patterns.add(extract_pattern_name(ex))

    # Load all examples
    examples = []
    with open(input_path, 'r') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    print(f"Loaded {len(examples)} examples from {input_path}")
    print(f"Identified {len(seed_patterns)} seed patterns")

    # Separate seeds and synthetic
    seeds = [ex for ex in examples if is_seed_example(ex, seed_patterns)]
    synthetic = [ex for ex in examples if not is_seed_example(ex, seed_patterns)]
    print(f"  Seeds: {len(seeds)}, Synthetic: {len(synthetic)}")

    # Find cherry-picked validation seeds (by pattern name only)
    val_examples = []
    remaining_seeds = []

    for ex in seeds:
        pattern = extract_pattern_name(ex)
        if pattern in VALIDATION_SEED_PATTERNS:
            val_examples.append(ex)
            print(f"  -> Validation seed: {pattern}")
        else:
            remaining_seeds.append(ex)

    # Group remaining by category
    by_category: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ex in remaining_seeds + synthetic:
        cat = extract_category(ex)
        by_category[cat].append(ex)

    print("\nCategory distribution (after reserving validation seeds):")
    for cat, exs in sorted(by_category.items()):
        print(f"  {cat}: {len(exs)}")

    # Split remaining 80/20 per category
    train_examples = []

    for cat, cat_examples in by_category.items():
        random.shuffle(cat_examples)
        # Calculate how many more validation examples we need for this category
        # (we already have 1 seed in validation)
        target_val = max(1, int(len(cat_examples) * (1 - train_ratio)))

        val_examples.extend(cat_examples[:target_val])
        train_examples.extend(cat_examples[target_val:])

    # Shuffle final sets
    random.shuffle(train_examples)
    random.shuffle(val_examples)

    # Write output files
    with open(train_path, 'w') as f:
        for ex in train_examples:
            f.write(json.dumps(ex) + '\n')

    with open(val_path, 'w') as f:
        for ex in val_examples:
            f.write(json.dumps(ex) + '\n')

    # Calculate stats
    stats = {
        "total": len(examples),
        "train": len(train_examples),
        "validation": len(val_examples),
        "by_category": {}
    }

    for cat in set(extract_category(ex) for ex in examples):
        train_count = sum(1 for ex in train_examples if extract_category(ex) == cat)
        val_count = sum(1 for ex in val_examples if extract_category(ex) == cat)
        stats["by_category"][cat] = {"train": train_count, "validation": val_count}

    return stats


def main():
    data_dir = Path("data/finetuning")
    input_path = data_dir / "train_level2_run.jsonl"
    seed_path = data_dir / "seed_examples.jsonl"
    train_path = data_dir / "train.jsonl"
    val_path = data_dir / "validation.jsonl"

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return

    if not seed_path.exists():
        print(f"Error: Seed file not found: {seed_path}")
        return

    stats = split_data(input_path, seed_path, train_path, val_path)

    print(f"\n{'='*50}")
    print("Split Statistics:")
    print(f"{'='*50}")
    print(f"Total: {stats['total']} | Train: {stats['train']} | Validation: {stats['validation']}")
    print(f"\nBy category:")
    for cat, counts in sorted(stats["by_category"].items()):
        print(f"  {cat}: train={counts['train']}, val={counts['validation']}")

    print(f"\nCherry-picked validation seeds:")
    for pattern in VALIDATION_SEED_PATTERNS:
        print(f"  - {pattern}")

    print(f"\nOutput files:")
    print(f"  {train_path}")
    print(f"  {val_path}")


if __name__ == "__main__":
    main()
