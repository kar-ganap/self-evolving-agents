"""
Merge additional synthetic examples into the main training dataset.

Extracts only the NEW synthetic examples (not duplicate seeds) from
train_additional.jsonl and merges them with train_level2_run.jsonl.

Usage:
    uv run python -m src.level2.run.merge_data
"""

import json
from pathlib import Path
from typing import Set, Dict, Any


def extract_pattern_name(example: Dict[str, Any]) -> str:
    """Extract pattern name from user message."""
    user_content = example["messages"][1]["content"]
    for line in user_content.split("\n"):
        if line.startswith("Pattern:"):
            return line.replace("Pattern:", "").strip()
    return ""


def load_seed_patterns(seed_path: Path) -> Set[str]:
    """Load seed pattern names."""
    patterns = set()
    with open(seed_path, 'r') as f:
        for line in f:
            if line.strip():
                ex = json.loads(line)
                patterns.add(extract_pattern_name(ex))
    return patterns


def merge_data(
    original_path: Path,
    additional_path: Path,
    seed_path: Path,
    output_path: Path
) -> Dict[str, int]:
    """Merge additional synthetic examples into original dataset."""
    # Load seed patterns to identify duplicates
    seed_patterns = load_seed_patterns(seed_path)
    print(f"Loaded {len(seed_patterns)} seed patterns")

    # Load original examples
    original_examples = []
    original_patterns = set()
    with open(original_path, 'r') as f:
        for line in f:
            if line.strip():
                ex = json.loads(line)
                original_examples.append(ex)
                original_patterns.add(extract_pattern_name(ex))
    print(f"Loaded {len(original_examples)} original examples")

    # Load additional examples and filter out duplicates
    new_synthetic = []
    skipped = 0
    with open(additional_path, 'r') as f:
        for line in f:
            if line.strip():
                ex = json.loads(line)
                pattern = extract_pattern_name(ex)

                # Skip if it's a seed (duplicate)
                if pattern in seed_patterns:
                    skipped += 1
                    continue

                # Skip if pattern already exists in original
                if pattern in original_patterns:
                    skipped += 1
                    continue

                new_synthetic.append(ex)
                original_patterns.add(pattern)  # Track to avoid duplicates

    print(f"Found {len(new_synthetic)} new synthetic examples")
    print(f"Skipped {skipped} duplicate/seed examples")

    # Merge
    merged = original_examples + new_synthetic

    # Write output
    with open(output_path, 'w') as f:
        for ex in merged:
            f.write(json.dumps(ex) + '\n')

    print(f"\nMerged {len(merged)} total examples to {output_path}")

    return {
        "original": len(original_examples),
        "new_synthetic": len(new_synthetic),
        "skipped": skipped,
        "merged_total": len(merged)
    }


def main():
    data_dir = Path("data/finetuning")

    original_path = data_dir / "train_level2_run.jsonl"
    additional_path = data_dir / "train_additional.jsonl"
    seed_path = data_dir / "seed_examples.jsonl"
    output_path = data_dir / "train_level2_run_v2.jsonl"

    if not original_path.exists():
        print(f"Error: Original file not found: {original_path}")
        return

    if not additional_path.exists():
        print(f"Error: Additional file not found: {additional_path}")
        return

    if not seed_path.exists():
        print(f"Error: Seed file not found: {seed_path}")
        return

    stats = merge_data(original_path, additional_path, seed_path, output_path)

    print("\n" + "=" * 50)
    print("Merge Statistics:")
    print("=" * 50)
    print(f"  Original examples:    {stats['original']}")
    print(f"  New synthetic added:  {stats['new_synthetic']}")
    print(f"  Skipped duplicates:   {stats['skipped']}")
    print(f"  Total merged:         {stats['merged_total']}")


if __name__ == "__main__":
    main()
