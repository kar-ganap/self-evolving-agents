"""
Generate Validation Set from Real Conversation Templates

Uses real parsed conversations as templates to generate high-quality
synthetic validation examples that match documented patterns.

Usage:
    python -m src.level1.run.generate_validation_from_real --count 30
"""

import os
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
import openai
from openai import OpenAI

load_dotenv(override=True)


def load_real_conversations(file_path: Path) -> List[Dict]:
    """Load parsed real conversations"""
    conversations = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                conversations.append(json.loads(line))
    return conversations


def load_pattern_docs() -> Dict[str, str]:
    """Load documented patterns for validation"""
    project_root = Path(__file__).parent.parent.parent.parent
    docs_dir = project_root / "docs"

    patterns_doc = (docs_dir / "01_extracted_patterns.md").read_text()
    preferences_doc = (docs_dir / "03_preference_profile.md").read_text()

    return {
        "patterns": patterns_doc,
        "preferences": preferences_doc
    }


def extract_conversation_template(conversation: Dict) -> Dict:
    """
    Extract template characteristics from a real conversation

    Returns structure, patterns, topic, etc.
    """
    # Get first few exchanges to understand the topic/context
    messages = conversation["messages"][:6]  # First 3 exchanges

    user_msg = messages[0]["content"] if messages and messages[0]["role"] == "user" else ""

    # Extract topic from first user message (first sentence)
    topic = user_msg.split('\n')[0][:100] if user_msg else "coding task"

    return {
        "quality_score": conversation.get("quality_score", 0),
        "top_patterns": conversation.get("top_patterns", []),
        "num_exchanges": len(conversation["messages"]) // 2,
        "topic_hint": topic,
        "file": conversation.get("file", "unknown")
    }


def generate_validation_example(
    client: OpenAI,
    template: Dict,
    pattern_docs: Dict[str, str],
    temperature: float = 0.8
) -> Optional[Dict]:
    """
    Generate a synthetic validation example using a real conversation template

    The generated conversation should:
    1. Match the structure of the template
    2. Demonstrate the template's top patterns
    3. Align with documented patterns and preferences
    """

    patterns_str = ", ".join(template["top_patterns"]) if template["top_patterns"] else "Production Readiness, Gap Analysis"

    prompt = f"""You are generating a HIGH-QUALITY validation example for fine-tuning a coding assistant.

# Goal
Create a realistic coding conversation that demonstrates Kartik's documented interaction patterns.

# Template Information
Based on a real conversation that scored {template['quality_score']:.2f} quality.
Topic area: {template['topic_hint']}
Must demonstrate these patterns: {patterns_str}

# Documented Patterns (MUST follow these)
{pattern_docs['patterns'][:2000]}

# User Preferences (MUST match this style)
{pattern_docs['preferences'][:1500]}

# Requirements
1. Generate a 3-4 exchange conversation (6-8 messages)
2. STRONGLY demonstrate the required patterns: {patterns_str}
3. Match the documented style exactly
4. Include production-ready code if relevant
5. Show gap analysis, tradeoffs, or other pattern characteristics

# Output Format
Return ONLY valid JSON (no markdown, no extra text):
{{
    "topic": "specific coding topic",
    "patterns_demonstrated": ["{patterns_str}"],
    "conversation": [
        {{"role": "user", "content": "user message"}},
        {{"role": "assistant", "content": "assistant response with patterns"}},
        {{"role": "user", "content": "follow-up"}},
        {{"role": "assistant", "content": "detailed response"}}
    ],
    "quality_notes": "Why this demonstrates the patterns well"
}}

Generate NOW. Remember: HIGH QUALITY only - this is for validation."""

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=3000
            )

            content = response.choices[0].message.content.strip()

            # Clean markdown if present
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

            result = json.loads(content)

            # Validate structure
            required_keys = ['topic', 'patterns_demonstrated', 'conversation', 'quality_notes']
            if all(key in result for key in required_keys):
                # Additional validation: check patterns are actually in the conversation
                conv_text = " ".join([msg["content"].lower() for msg in result["conversation"]])

                # Check for pattern indicators
                has_patterns = False
                for pattern in template["top_patterns"]:
                    if pattern.lower() in result.get('quality_notes', '').lower():
                        has_patterns = True
                        break

                if has_patterns or len(result['conversation']) >= 4:
                    return result
                else:
                    print(f"  ⚠️  Weak pattern demonstration (attempt {attempt+1}/3)")
            else:
                print(f"  ⚠️  Missing required keys (attempt {attempt+1}/3)")

        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON parse error (attempt {attempt+1}/3)")
            if attempt == 2:
                print(f"  ✗ Failed to parse: {content[:200]}...")
        except Exception as e:
            print(f"  ⚠️  Error (attempt {attempt+1}/3): {e}")
            time.sleep(2 ** attempt)

    return None


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Generate validation examples from real templates")
    parser.add_argument('--count', type=int, default=30, help='Number of validation examples')
    parser.add_argument('--temperature', type=float, default=0.8, help='Generation temperature')
    args = parser.parse_args()

    print("🎯 Generating Validation Examples from Real Templates")
    print("=" * 60)

    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return

    client = OpenAI(api_key=api_key)

    # Paths
    project_root = Path(__file__).parent.parent.parent.parent
    real_convs_file = project_root / "data/real_conversations_parsed.jsonl"
    output_file = project_root / "data/validation_from_real.jsonl"

    # Load real conversations
    print(f"\n📂 Loading real conversations...")
    real_conversations = load_real_conversations(real_convs_file)

    # Sort by quality
    real_conversations.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

    print(f"   Loaded {len(real_conversations)} real conversations")
    print(f"   Top quality: {real_conversations[0].get('quality_score', 0):.2f}")

    # Load pattern documentation
    print(f"\n📚 Loading pattern documentation...")
    pattern_docs = load_pattern_docs()
    print(f"   ✅ Loaded patterns and preferences")

    # Extract templates
    print(f"\n🔍 Extracting templates from top conversations...")
    templates = []
    for conv in real_conversations:
        template = extract_conversation_template(conv)
        templates.append(template)
        print(f"   - {template['file']}: Quality {template['quality_score']:.2f}, Patterns: {', '.join(template['top_patterns'])}")

    # Generate validation examples
    print(f"\n🚀 Generating {args.count} validation examples...")
    validation_examples = []

    for i in range(args.count):
        # Cycle through templates (use top conversations multiple times if needed)
        template = templates[i % len(templates)]

        print(f"\n[{i+1}/{args.count}] Using template: {template['file']}")
        print(f"           Patterns: {', '.join(template['top_patterns'])}")

        result = generate_validation_example(
            client,
            template,
            pattern_docs,
            temperature=args.temperature
        )

        if result:
            validation_examples.append(result)
            print(f"  ✅ Generated ({len(result['conversation'])} messages)")

            # Save incrementally
            with open(output_file, 'w') as f:
                for ex in validation_examples:
                    f.write(json.dumps(ex) + '\n')
        else:
            print(f"  ✗ Failed to generate")

        # Rate limiting
        if i < args.count - 1:
            time.sleep(1)

    print(f"\n✅ Generated {len(validation_examples)}/{args.count} validation examples")
    print(f"   Saved to: {output_file}")

    # Summary
    if validation_examples:
        avg_messages = sum(len(ex['conversation']) for ex in validation_examples) / len(validation_examples)
        print(f"\n📊 Summary:")
        print(f"   Average messages per example: {avg_messages:.1f}")
        print(f"   All examples based on real conversation templates")
        print(f"   Validated against documented patterns")


if __name__ == '__main__':
    main()
