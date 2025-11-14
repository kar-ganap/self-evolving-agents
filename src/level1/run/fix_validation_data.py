"""
Fix Validation Data - Same approach as training

Usage:
    python -m src.level1.run.fix_validation_data
"""

import json
from pathlib import Path
import sys

# Import the same functions from fix_training_data_v2
sys.path.append(str(Path(__file__).parent))
from fix_training_data_v2 import (
    get_first_assistant_response,
    is_comprehensive_response,
    extract_first_response_only,
    update_system_prompt
)


def main():
    """Fix validation data"""
    print("🔧 Fixing Validation Data")
    print("=" * 60)

    project_root = Path(__file__).parent.parent.parent.parent

    # Load current validation data
    val_file = project_root / "data/finetuning/validation.jsonl"

    print(f"\n📂 Loading: {val_file}")

    validation_data = []
    with open(val_file, 'r') as f:
        for line in f:
            if line.strip():
                validation_data.append(json.loads(line))

    print(f"   Original examples: {len(validation_data)}")

    # Process examples
    filtered_data = []
    stats = {
        'too_short': 0,
        'too_many_questions': 0,
        'not_structured': 0,
        'ends_with_question': 0,
        'kept': 0
    }

    for example in validation_data:
        # Extract first response only
        first_response_example = extract_first_response_only(example)

        # Get the first assistant response
        first_response = get_first_assistant_response(first_response_example)

        if not first_response:
            continue

        # Check if comprehensive
        if len(first_response) < 300:
            stats['too_short'] += 1
            continue

        question_marks = first_response.count('?')
        if question_marks > 3:
            stats['too_many_questions'] += 1
            continue

        pattern_indicators = ['✓', '✗', '⚠️', '###', '**', '```', '1.', '2.', 'vs', 'pros', 'cons']
        has_indicators = sum(1 for ind in pattern_indicators if ind in first_response)

        if has_indicators < 2:
            stats['not_structured'] += 1
            continue

        last_100 = first_response[-100:]
        if last_100.count('?') > 0 and last_100.count('.') < 2:
            stats['ends_with_question'] += 1
            continue

        # Update system prompt with frontload instruction
        updated_messages = update_system_prompt(first_response_example['messages'])

        filtered_data.append({'messages': updated_messages})
        stats['kept'] += 1

    print(f"\n📊 Filtering Stats:")
    print(f"   ✓ Kept:                  {stats['kept']}")
    print(f"   ✗ Too short (< 300):     {stats['too_short']}")
    print(f"   ✗ Too many questions:    {stats['too_many_questions']}")
    print(f"   ✗ Not structured:        {stats['not_structured']}")
    print(f"   ✗ Ends with question:    {stats['ends_with_question']}")

    # Save filtered data
    output_file = project_root / "data/finetuning/validation_v2.jsonl"

    with open(output_file, 'w') as f:
        for example in filtered_data:
            f.write(json.dumps(example) + '\n')

    print(f"\n💾 Saved: {output_file}")
    print(f"   Examples: {len(filtered_data)}")

    # Check if we have enough data
    if len(filtered_data) < 20:
        print(f"\n⚠️  WARNING: Only {len(filtered_data)} examples after filtering!")
        print("   Minimum recommended: 20 examples")
    else:
        print(f"\n✅ Good: {len(filtered_data)} examples")

    return len(filtered_data)


if __name__ == '__main__':
    count = main()
    sys.exit(0 if count >= 20 else 1)
