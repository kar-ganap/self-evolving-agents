"""
Create Train/Validation Split (Milestone 1.14c)

Combines synthetic and real conversations, creates proper split:
- Training: Synthetic conversations
- Validation: High-quality real conversations (for early stopping)

Usage:
    python -m src.level1.run.create_train_val_split
"""

import json
import random
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv(override=True)


def load_synthetic_data(file_path: Path) -> List[Dict]:
    """Load synthetic training data"""
    examples = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    return examples


def load_validation_examples(file_path: Path) -> List[Dict]:
    """Load validation examples (already in proper format)"""
    examples = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    return examples


def convert_validation_to_training_format(validation_example: Dict, system_prompt: str) -> Dict:
    """
    Convert validation example to OpenAI format

    Validation example format (from generated or hand-crafted):
    {
        "topic": "...",
        "patterns_demonstrated": [...],  # or "patterns_applied"
        "conversation": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."},
            ...
        ],
        "quality_notes": "..."  # or "learning_notes"
    }

    Output format (OpenAI):
    {
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."},
            ...
        ]
    }
    """
    # Extract conversation messages
    messages = validation_example.get("conversation", [])

    # Add system prompt
    formatted_messages = [{"role": "system", "content": system_prompt}]
    formatted_messages.extend(messages)

    return {"messages": formatted_messages}


def create_system_prompt() -> str:
    """System prompt with learned patterns"""
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


def main():
    """Main execution"""
    print("🔀 Creating Train/Validation Split")
    print("=" * 60)

    # Paths
    project_root = Path(__file__).parent.parent.parent.parent
    synthetic_file = project_root / "data/synthetic/combined_finetuning.jsonl"
    validation_real_file = project_root / "data/validation_from_real.jsonl"
    handcrafted_file = project_root / "data/handcrafted_examples.jsonl"
    train_output = project_root / "data/finetuning/train.jsonl"
    val_output = project_root / "data/finetuning/validation.jsonl"

    # Create output directory
    train_output.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    print(f"\n📂 Loading data...")
    synthetic_examples = load_synthetic_data(synthetic_file)
    validation_real = load_validation_examples(validation_real_file)
    handcrafted = load_validation_examples(handcrafted_file)

    print(f"   Synthetic training examples: {len(synthetic_examples)}")
    print(f"   Validation from real templates: {len(validation_real)}")
    print(f"   Hand-crafted validation examples: {len(handcrafted)}")

    # Create system prompt
    system_prompt = create_system_prompt()

    # Convert validation examples to training format
    print(f"\n🔄 Converting validation examples...")
    validation_examples = []

    # Convert validation from real templates
    for val_ex in validation_real:
        example = convert_validation_to_training_format(val_ex, system_prompt)
        validation_examples.append(example)

    # Convert hand-crafted examples
    for val_ex in handcrafted:
        example = convert_validation_to_training_format(val_ex, system_prompt)
        validation_examples.append(example)

    print(f"   Converted {len(validation_examples)} validation examples")
    print(f"     - {len(validation_real)} from real conversation templates")
    print(f"     - {len(handcrafted)} hand-crafted examples")

    # Create splits
    print(f"\n✂️  Creating splits...")

    # Training set: All synthetic data
    train_set = synthetic_examples.copy()

    # Validation set: All validation examples
    validation_set = validation_examples.copy()

    print(f"   Training set: {len(train_set)} examples (100% synthetic)")
    print(f"   Validation set: {len(validation_set)} examples")
    print(f"     - {len(validation_real)} generated from real templates")
    print(f"     - {len(handcrafted)} hand-crafted examples")

    # Calculate stats
    def estimate_tokens(examples):
        total = 0
        for ex in examples:
            for msg in ex["messages"]:
                total += len(msg["content"]) // 4
        return total

    train_tokens = estimate_tokens(train_set)
    val_tokens = estimate_tokens(validation_set)

    print(f"\n📊 Dataset Statistics:")
    print(f"   Training tokens: ~{train_tokens:,}")
    print(f"   Validation tokens: ~{val_tokens:,}")
    print(f"   Total tokens: ~{train_tokens + val_tokens:,}")

    # Cost estimate
    training_cost_per_epoch = train_tokens * 0.000025  # $25/1M tokens
    print(f"\n💰 Estimated Cost:")
    print(f"   Per epoch: ~${training_cost_per_epoch:.2f}")
    print(f"   With 3 epochs: ~${training_cost_per_epoch * 3:.2f}")
    print(f"   Note: Early stopping may reduce epochs if validation plateaus")

    # Save splits
    print(f"\n💾 Saving splits...")
    with open(train_output, 'w') as f:
        for example in train_set:
            f.write(json.dumps(example) + '\n')
    print(f"   ✅ Training: {train_output}")

    with open(val_output, 'w') as f:
        for example in validation_set:
            f.write(json.dumps(example) + '\n')
    print(f"   ✅ Validation: {val_output}")

    # Print sample
    print(f"\n📋 Sample Validation Example:")
    print("-" * 60)
    if validation_set:
        sample = validation_set[0]
        print(f"Messages: {len(sample['messages'])}")
        print(f"System: {sample['messages'][0]['content'][:80]}...")
        print(f"User: {sample['messages'][1]['content'][:100]}...")
        print(f"Assistant: {sample['messages'][2]['content'][:150]}...")

    print(f"\n✅ Ready for fine-tuning!")
    print(f"\nNext step: Upload and start training")
    print(f"   python -m src.level1.run.start_finetuning")


if __name__ == '__main__':
    main()
