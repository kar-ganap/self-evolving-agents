"""
Generate Additional High-Quality Training Examples with OpenAI

Focus on:
- Comprehensive first responses
- Balanced pattern coverage
- Single-shot Q&A format

Usage:
    python -m src.level1.run.generate_additional_examples --count 80
"""

import os
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from .prompt_library import get_prompts_for_provider, EXPANDED_PROMPTS

load_dotenv(override=True)


def create_system_prompt_with_frontload():
    """Enhanced system prompt with frontloading instruction"""
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

CRITICAL: When responding to a new task or query, FRONTLOAD your analysis:

1. Start with comprehensive thinking using the patterns above
2. Identify gaps, tradeoffs, gotchas UPFRONT
3. Provide structured analysis BEFORE suggesting solutions
4. Do NOT ask clarifying questions unless the query is genuinely ambiguous
5. For technical questions, explain mechanisms and context first

Your FIRST response should demonstrate pattern application. Apply these patterns naturally without explicitly mentioning them."""


def generate_example(client: OpenAI, prompt: str, pattern: str) -> dict:
    """Generate a single comprehensive example"""
    system_prompt = create_system_prompt_with_frontload()

    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=1500
    )

    assistant_response = response.choices[0].message.content

    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": assistant_response}
        ],
        "metadata": {
            "target_pattern": pattern,
            "prompt_type": "targeted"
        }
    }


def main():
    """Generate additional examples"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=80, help='Number of examples to generate')
    args = parser.parse_args()

    print(f"🎯 Generating {args.count} Additional Training Examples (OpenAI GPT-4o)")
    print("=" * 60)

    # Load API key
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                api_key = line.split('=', 1)[1].split('#')[0].strip()
                break

    client = OpenAI(api_key=api_key)

    # Calculate how many per pattern
    num_patterns = len(EXPANDED_PROMPTS)
    per_pattern = args.count // num_patterns

    generated = []

    for pattern in EXPANDED_PROMPTS.keys():
        # Get OpenAI-specific prompts (odd indices: 0, 2, 4, 6...)
        prompts = get_prompts_for_provider("openai", pattern)
        print(f"\n🔄 Generating {per_pattern} examples for: {pattern}")
        print(f"   Using {len(prompts)} unique OpenAI prompts")

        for i in range(per_pattern):
            prompt = prompts[i % len(prompts)]

            try:
                example = generate_example(client, prompt, pattern)
                generated.append(example)
                print(f"  [{i+1}/{per_pattern}] ✓ Generated")
            except Exception as e:
                print(f"  [{i+1}/{per_pattern}] ✗ Error: {e}")

    # Save
    project_root = Path(__file__).parent.parent.parent.parent
    output_file = project_root / "data/finetuning/train_additional.jsonl"

    with open(output_file, 'w') as f:
        for example in generated:
            # Remove metadata before saving (just for tracking)
            clean_example = {"messages": example["messages"]}
            f.write(json.dumps(clean_example) + '\n')

    print(f"\n💾 Saved: {output_file}")
    print(f"   Examples generated: {len(generated)}")

    # Now merge with existing train_v2
    print(f"\n🔗 Merging with existing training data...")

    existing_file = project_root / "data/finetuning/train_v2.jsonl"
    existing = []

    with open(existing_file, 'r') as f:
        for line in f:
            if line.strip():
                existing.append(json.loads(line))

    print(f"   Existing examples: {len(existing)}")
    print(f"   New examples: {len(generated)}")

    merged_file = project_root / "data/finetuning/train_v3.jsonl"

    with open(merged_file, 'w') as f:
        for example in existing + generated:
            f.write(json.dumps(example) + '\n')

    print(f"\n✅ Merged file: {merged_file}")
    print(f"   Total examples: {len(existing) + len(generated)}")


if __name__ == '__main__':
    main()
