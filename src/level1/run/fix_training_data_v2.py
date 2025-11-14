"""
Fix Training Data - Extract First Comprehensive Responses Only

Goal: Keep only the FIRST assistant response from each conversation,
ensuring it's comprehensive and pattern-aware (not a clarifying question).

Usage:
    python -m src.level1.run.fix_training_data_v2
"""

import json
from pathlib import Path
from typing import Dict, List


def get_first_assistant_response(example: Dict) -> str:
    """Extract first assistant message"""
    messages = example.get('messages', [])
    for msg in messages:
        if msg['role'] == 'assistant':
            return msg['content']
    return ""


def is_comprehensive_response(response: str) -> bool:
    """Check if response is comprehensive (not just a question)"""
    # Check length
    if len(response) < 300:
        return False

    # Check if it's mostly questions
    question_marks = response.count('?')
    if question_marks > 3:  # Too many questions
        return False

    # Check for pattern indicators (structured thinking)
    pattern_indicators = ['✓', '✗', '⚠️', '###', '**', '```', '1.', '2.', 'vs', 'pros', 'cons']
    has_indicators = sum(1 for ind in pattern_indicators if ind in response)

    if has_indicators < 2:  # Not enough structure
        return False

    # Check it's not ending with just a question
    last_100 = response[-100:]
    if last_100.count('?') > 0 and last_100.count('.') < 2:
        return False

    return True


def extract_first_response_only(example: Dict) -> Dict:
    """Convert multi-turn to single first response"""
    messages = example.get('messages', [])

    # Find system, first user, first assistant
    new_messages = []
    found_user = False
    found_assistant = False

    for msg in messages:
        if msg['role'] == 'system':
            new_messages.append(msg)
        elif msg['role'] == 'user' and not found_user:
            new_messages.append(msg)
            found_user = True
        elif msg['role'] == 'assistant' and not found_assistant:
            new_messages.append(msg)
            found_assistant = True
            break  # Stop after first assistant response

    return {'messages': new_messages}


def update_system_prompt(messages: List[Dict]) -> List[Dict]:
    """Add explicit frontloading instruction to system prompt"""

    frontload_instruction = """

CRITICAL: When responding to a new task or query, FRONTLOAD your analysis:

1. Start with comprehensive thinking using the patterns above
2. Identify gaps, tradeoffs, gotchas UPFRONT
3. Provide structured analysis BEFORE suggesting solutions
4. Do NOT ask clarifying questions unless the query is genuinely ambiguous
5. For technical questions, explain mechanisms and context first

Your FIRST response should demonstrate pattern application. Multi-turn refinement can follow."""

    updated_messages = []
    for msg in messages:
        if msg['role'] == 'system':
            # Add frontload instruction to existing system prompt
            updated_content = msg['content'] + frontload_instruction
            updated_messages.append({'role': 'system', 'content': updated_content})
        else:
            updated_messages.append(msg)

    return updated_messages


def main():
    """Fix training data"""
    print("🔧 Fixing Training Data - V2")
    print("=" * 60)

    project_root = Path(__file__).parent.parent.parent.parent

    # Load current training data
    train_file = project_root / "data/finetuning/train.jsonl"

    print(f"\n📂 Loading: {train_file}")

    training_data = []
    with open(train_file, 'r') as f:
        for line in f:
            if line.strip():
                training_data.append(json.loads(line))

    print(f"   Original examples: {len(training_data)}")

    # Process examples
    filtered_data = []
    stats = {
        'too_short': 0,
        'too_many_questions': 0,
        'not_structured': 0,
        'ends_with_question': 0,
        'kept': 0
    }

    for example in training_data:
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
    output_file = project_root / "data/finetuning/train_v2.jsonl"

    with open(output_file, 'w') as f:
        for example in filtered_data:
            f.write(json.dumps(example) + '\n')

    print(f"\n💾 Saved: {output_file}")
    print(f"   Examples: {len(filtered_data)}")

    # Check if we have enough data
    if len(filtered_data) < 50:
        print(f"\n⚠️  WARNING: Only {len(filtered_data)} examples after filtering!")
        print("   Minimum recommended: 50 examples")
        print("   Consider relaxing filters or generating more data")
    elif len(filtered_data) > 200:
        print(f"\n✓ Good: {len(filtered_data)} examples (target: 100-200)")
    else:
        print(f"\n✅ Perfect: {len(filtered_data)} examples")

    return len(filtered_data)


if __name__ == '__main__':
    count = main()
    import sys
    sys.exit(0 if count >= 50 else 1)
