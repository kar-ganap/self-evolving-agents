"""
Extract Hand-Crafted Examples from 02_synthetic_conversations.md

These are high-quality examples specifically created to demonstrate patterns.
Perfect for validation set.

Usage:
    python -m src.level1.run.extract_handcrafted_examples
"""

import re
import json
from pathlib import Path
from typing import List, Dict


def extract_examples_from_markdown(md_file: Path) -> List[Dict]:
    """
    Extract conversation examples from 02_synthetic_conversations.md

    Format:
    ## Synthetic Conversation N: Topic
    ### ❌ Generic Claude Response
    ...
    ### ✅ Response Matching User's Patterns
    **User:** ...
    **Claude:** or **Assistant:** ...
    """
    with open(md_file, 'r') as f:
        content = f.read()

    examples = []

    # Split by synthetic conversation sections
    conv_pattern = r'## Synthetic Conversation \d+:?\s*(.+?)\n(.*?)(?=## Synthetic Conversation \d+:|$)'
    matches = re.finditer(conv_pattern, content, re.DOTALL)

    for match in matches:
        title = match.group(1).strip()
        full_content = match.group(2).strip()

        # Extract only the "✅ Response Matching User's Patterns" section
        pattern_match = re.search(r'### ✅ Response Matching User\'s Patterns\s*(.*?)(?=###|##|$)', full_content, re.DOTALL)

        if not pattern_match:
            continue

        example_content = pattern_match.group(1).strip()

        # Extract user/claude messages
        messages = []

        # Find all User/Claude/Assistant pairs
        user_pattern = r'\*\*User:?\*\*\s*(.*?)(?=\*\*(?:Claude|Assistant):?|\*\*User:|###|$)'
        assistant_pattern = r'\*\*(?:Claude|Assistant):?\*\*\s*(.*?)(?=\*\*User:?|\*\*(?:Claude|Assistant):|###|$)'

        # Get all messages in order
        all_matches = []

        for user_match in re.finditer(user_pattern, example_content, re.DOTALL):
            all_matches.append(('user', user_match.start(), user_match.group(1).strip()))

        for asst_match in re.finditer(assistant_pattern, example_content, re.DOTALL):
            all_matches.append(('assistant', asst_match.start(), asst_match.group(1).strip()))

        # Sort by position
        all_matches.sort(key=lambda x: x[1])

        # Build message list
        for role, _, msg_content in all_matches:
            if msg_content:
                # Clean up the content
                msg_content = msg_content.strip()
                # Remove extra markdown formatting
                msg_content = re.sub(r'\n{3,}', '\n\n', msg_content)
                # Remove markdown code block markers if they're at start/end
                msg_content = msg_content.strip()

                if msg_content:
                    messages.append({
                        "role": role,
                        "content": msg_content
                    })

        if len(messages) >= 2:  # At least one exchange
            examples.append({
                "topic": title,
                "patterns_applied": ["Multiple patterns"],  # These examples show multiple
                "conversation": messages,
                "source": "hand-crafted",
                "learning_notes": f"Hand-crafted example: {title}"
            })

    return examples


def main():
    """Main execution"""
    print("📚 Extracting Hand-Crafted Examples")
    print("=" * 60)

    # Paths
    project_root = Path(__file__).parent.parent.parent.parent
    md_file = project_root / "docs/02_synthetic_conversations.md"
    output_file = project_root / "data/handcrafted_examples.jsonl"

    if not md_file.exists():
        print(f"❌ File not found: {md_file}")
        return

    # Extract examples
    print(f"\n📄 Processing {md_file.name}...")
    examples = extract_examples_from_markdown(md_file)

    print(f"\n✅ Extracted {len(examples)} examples")

    # Print summary
    for i, ex in enumerate(examples, 1):
        num_msgs = len(ex["conversation"])
        pattern = ex["patterns_applied"][0] if ex["patterns_applied"] else "Unknown"
        print(f"   {i}. {pattern}: {num_msgs} messages")

    # Save
    print(f"\n💾 Saving to {output_file}...")
    with open(output_file, 'w') as f:
        for ex in examples:
            f.write(json.dumps(ex) + '\n')

    print(f"✅ Saved {len(examples)} hand-crafted examples")

    # Show sample
    if examples:
        print(f"\n📋 Sample Example:")
        print("-" * 60)
        sample = examples[0]
        print(f"Pattern: {sample['patterns_applied'][0]}")
        print(f"Messages: {len(sample['conversation'])}")
        print(f"User: {sample['conversation'][0]['content'][:100]}...")
        print(f"Assistant: {sample['conversation'][1]['content'][:150]}...")


if __name__ == '__main__':
    main()
