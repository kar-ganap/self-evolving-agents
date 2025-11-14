"""
Prepare Fine-Tuning Data for OpenAI (Milestone 1.14)

Combines synthetic conversations from OpenAI and Gemini,
converts to OpenAI fine-tuning format, and validates.

Usage:
    python -m src.level1.run.prepare_finetuning_data
"""

import json
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv(override=True)


def load_synthetic_conversations(file_path: Path) -> List[Dict]:
    """Load conversations from JSONL file"""
    conversations = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    conversations.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Warning: Skipping malformed line in {file_path}")
                    continue
    return conversations


def create_system_prompt() -> str:
    """Create system prompt that embeds the learned patterns"""
    return """You are a coding assistant for Kartik, an experienced ML engineer.

You have learned his preferences from analyzing past conversations. Apply these patterns naturally:

1. **Gap Analysis**: Systematically identify what's missing using ✓ ⚠️ ✗ scoring
2. **Tradeoff Analysis**: Compare alternatives with pros/cons before recommending
3. **Production Readiness**: Always include tests, error handling, type hints, docs
4. **Brutal Accuracy**: Challenge logical connections, cut through complexity
5. **Multi-Dimensional Evaluation**: Separate scores for different criteria
6. **Hint-Based Learning**: For debugging, give strategic hints not solutions
7. **Diminishing Returns**: Quantify ROI, identify effort threshold
8. **Mechanistic Understanding**: Explain HOW things work with concrete examples
9. **Context-Dependent Recommendations**: No universal answers, factor constraints
10. **Precision Policing**: Use exact technical terms, add caveats and conditions

Apply these patterns naturally without explicitly mentioning them."""


def convert_to_openai_format(conversation: Dict, system_prompt: str) -> Dict:
    """
    Convert synthetic conversation to OpenAI fine-tuning format

    Input format:
    {
        "topic": "...",
        "patterns_applied": [...],
        "conversation": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."},
            ...
        ],
        "learning_notes": "..."
    }

    Output format:
    {
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."},
            ...
        ]
    }
    """
    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation turns
    for turn in conversation['conversation']:
        messages.append({
            "role": turn['role'],
            "content": turn['content']
        })

    return {"messages": messages}


def validate_format(examples: List[Dict]) -> bool:
    """Validate OpenAI fine-tuning format"""
    print("\n🔍 Validating format...")

    errors = []
    for i, example in enumerate(examples):
        # Check required keys
        if 'messages' not in example:
            errors.append(f"Example {i}: Missing 'messages' key")
            continue

        messages = example['messages']

        # Check minimum length (system + at least 1 turn)
        if len(messages) < 3:
            errors.append(f"Example {i}: Too few messages ({len(messages)})")

        # Check first message is system
        if messages[0]['role'] != 'system':
            errors.append(f"Example {i}: First message must be system role")

        # Check alternating user/assistant
        for j in range(1, len(messages)):
            expected_role = 'user' if j % 2 == 1 else 'assistant'
            if messages[j]['role'] != expected_role:
                errors.append(f"Example {i}, message {j}: Expected {expected_role}, got {messages[j]['role']}")

    if errors:
        print(f"❌ Found {len(errors)} validation errors:")
        for error in errors[:10]:  # Show first 10
            print(f"   - {error}")
        return False

    print(f"✅ All {len(examples)} examples validated successfully")
    return True


def calculate_stats(examples: List[Dict]) -> Dict:
    """Calculate dataset statistics"""
    total_messages = sum(len(ex['messages']) for ex in examples)
    total_tokens = 0  # Approximate

    for ex in examples:
        for msg in ex['messages']:
            # Rough token estimate: ~4 chars per token
            total_tokens += len(msg['content']) // 4

    avg_messages = total_messages / len(examples) if examples else 0
    avg_tokens = total_tokens / len(examples) if examples else 0

    return {
        'total_examples': len(examples),
        'total_messages': total_messages,
        'avg_messages_per_example': round(avg_messages, 1),
        'estimated_total_tokens': total_tokens,
        'estimated_avg_tokens_per_example': round(avg_tokens, 1)
    }


def main():
    """Main execution"""
    print("🚀 Preparing Fine-Tuning Data for OpenAI")
    print("=" * 60)

    # Paths
    project_root = Path(__file__).parent.parent.parent.parent
    synthetic_dir = project_root / "data/synthetic"
    output_file = project_root / "data/synthetic/combined_finetuning.jsonl"

    # Find all synthetic conversation files
    print(f"\n📂 Scanning for synthetic conversation files...")
    openai_files = list((synthetic_dir / "openai").glob("synthetic_conversations_*.jsonl"))
    gemini_files = list((synthetic_dir / "gemini").glob("synthetic_conversations_*.jsonl"))

    print(f"   Found {len(openai_files)} OpenAI files")
    print(f"   Found {len(gemini_files)} Gemini files")

    # Load all conversations
    all_conversations = []

    for file in openai_files:
        convs = load_synthetic_conversations(file)
        print(f"   Loaded {len(convs)} from {file.name}")
        all_conversations.extend(convs)

    for file in gemini_files:
        convs = load_synthetic_conversations(file)
        print(f"   Loaded {len(convs)} from {file.name}")
        all_conversations.extend(convs)

    print(f"\n   Total conversations: {len(all_conversations)}")

    # Create system prompt
    system_prompt = create_system_prompt()

    # Convert to OpenAI format
    print(f"\n🔄 Converting to OpenAI format...")
    training_examples = []
    for conv in all_conversations:
        example = convert_to_openai_format(conv, system_prompt)
        training_examples.append(example)

    print(f"   Converted {len(training_examples)} examples")

    # Validate
    if not validate_format(training_examples):
        print("\n❌ Validation failed. Please fix errors before proceeding.")
        return

    # Calculate statistics
    stats = calculate_stats(training_examples)
    print(f"\n📊 Dataset Statistics:")
    print(f"   Total examples: {stats['total_examples']}")
    print(f"   Average messages per example: {stats['avg_messages_per_example']}")
    print(f"   Estimated total tokens: {stats['estimated_total_tokens']:,}")
    print(f"   Estimated avg tokens per example: {stats['estimated_avg_tokens_per_example']}")

    # Save
    print(f"\n💾 Saving to {output_file}...")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        for example in training_examples:
            f.write(json.dumps(example) + '\n')

    print(f"✅ Saved {len(training_examples)} training examples")

    # Print sample
    print(f"\n📋 Sample Training Example:")
    print("-" * 60)
    sample = training_examples[0]
    print(f"Messages: {len(sample['messages'])}")
    print(f"System: {sample['messages'][0]['content'][:100]}...")
    print(f"User: {sample['messages'][1]['content'][:100]}...")
    print(f"Assistant: {sample['messages'][2]['content'][:150]}...")

    # Cost estimate
    print(f"\n💰 Estimated Training Cost:")
    print(f"   Tokens: ~{stats['estimated_total_tokens']:,}")
    # GPT-4o fine-tuning: $25/1M training tokens
    training_cost = stats['estimated_total_tokens'] * 0.000025
    print(f"   Training cost (GPT-4o): ~${training_cost:.2f}")
    print(f"   Note: Actual cost depends on epochs (default: auto, typically 3-4)")
    print(f"   With 3 epochs: ~${training_cost * 3:.2f}")

    print(f"\n✅ Ready for fine-tuning!")
    print(f"\nNext step: Upload and start fine-tuning")
    print(f"   python -m src.level1.run.start_finetuning")


if __name__ == '__main__':
    main()
