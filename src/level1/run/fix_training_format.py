"""
Fix Training Data Format

Ensures all conversations end with an assistant message,
as required by OpenAI fine-tuning API.

Usage:
    python -m src.level1.run.fix_training_format
"""

import json
from pathlib import Path


def validate_and_fix_example(example: dict) -> dict | None:
    """
    Validate and fix a training example.

    Returns None if example cannot be fixed (e.g., no assistant messages)
    """
    messages = example.get("messages", [])

    if not messages:
        return None

    # Check if last message is from assistant
    if messages[-1]["role"] == "assistant":
        return example  # Already valid

    # If last message is user, we need to remove trailing user messages
    # until we find an assistant message
    while messages and messages[-1]["role"] != "assistant":
        messages.pop()

    # If no assistant messages left, skip this example
    if not messages or messages[-1]["role"] != "assistant":
        return None

    # Return fixed example
    example["messages"] = messages
    return example


def fix_training_file(input_file: Path, output_file: Path):
    """Fix all examples in a training file"""
    print(f"Processing {input_file.name}...")

    examples = []
    fixed_count = 0
    removed_count = 0
    valid_count = 0

    # Read and fix examples
    with open(input_file, 'r') as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue

            example = json.loads(line)
            original_msg_count = len(example.get("messages", []))

            fixed_example = validate_and_fix_example(example)

            if fixed_example is None:
                removed_count += 1
                print(f"   ⚠️  Example {i}: Removed (no assistant messages)")
            elif len(fixed_example["messages"]) < original_msg_count:
                examples.append(fixed_example)
                fixed_count += 1
                print(f"   ✓ Example {i}: Fixed ({original_msg_count} → {len(fixed_example['messages'])} messages)")
            else:
                examples.append(fixed_example)
                valid_count += 1

    # Save fixed examples
    with open(output_file, 'w') as f:
        for example in examples:
            f.write(json.dumps(example) + '\n')

    print(f"\n✅ {input_file.name} processed:")
    print(f"   Valid: {valid_count}")
    print(f"   Fixed: {fixed_count}")
    print(f"   Removed: {removed_count}")
    print(f"   Total output: {len(examples)}")


def main():
    """Main execution"""
    print("🔧 Fixing Training Data Format")
    print("=" * 60)

    project_root = Path(__file__).parent.parent.parent.parent

    # Fix training file
    train_input = project_root / "data/finetuning/train.jsonl"
    train_output = project_root / "data/finetuning/train_fixed.jsonl"

    fix_training_file(train_input, train_output)

    # Fix validation file
    print("\n" + "-" * 60)
    val_input = project_root / "data/finetuning/validation.jsonl"
    val_output = project_root / "data/finetuning/validation_fixed.jsonl"

    fix_training_file(val_input, val_output)

    print("\n" + "=" * 60)
    print("✅ Fixed files saved:")
    print(f"   {train_output}")
    print(f"   {val_output}")
    print("\nReplace original files:")
    print(f"   mv {train_output} {train_input}")
    print(f"   mv {val_output} {val_input}")


if __name__ == '__main__':
    main()
