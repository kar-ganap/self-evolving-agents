"""
Parse Real Claude Code Conversations (Milestone 1.14b)

Parses markdown conversation logs, scores against documented patterns,
and cherry-picks the best examples for validation set.

Usage:
    python -m src.level1.run.parse_real_conversations
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple
from dotenv import load_dotenv

load_dotenv(override=True)


# The 10 patterns we're looking for (from 01_extracted_patterns.md)
PATTERN_KEYWORDS = {
    "Gap Analysis": ["missing", "not addressed", "gap", "✓", "✗", "⚠️", "completeness"],
    "Tradeoff Analysis": ["tradeoff", "vs", "versus", "pros", "cons", "alternative", "option a", "option b"],
    "Production Readiness": ["error handling", "edge case", "test", "monitoring", "logging", "production"],
    "Brutal Accuracy": ["connection", "how does", "what does", "have to do with", "address"],
    "Multi-Dimensional Evaluation": ["dimension", "criteria", "score", "separate", "aspect"],
    "Hint-Based Learning": ["hint", "question to consider", "examine", "trace", "debug"],
    "Diminishing Returns": ["roi", "marginal", "worth it", "effort", "value"],
    "Mechanistic Understanding": ["how it works", "step-by-step", "trace", "execution", "mechanism"],
    "Context-Dependent": ["depends on", "context", "scenario", "use case", "constraint"],
    "Precision Policing": ["caveat", "note:", "however", "specifically", "precisely", "exactly"]
}


def parse_markdown_conversation(md_file: Path) -> Dict:
    """
    Parse a markdown conversation file into structured format

    Format:
    ## 👤 User
    content

    ## 🤖 Claude
    content
    """
    with open(md_file, 'r') as f:
        content = f.read()

    # Extract metadata
    session_match = re.search(r'Session ID: ([\w-]+)', content)
    date_match = re.search(r'Date: (\d{4}-\d{2}-\d{2})', content)

    session_id = session_match.group(1) if session_match else md_file.stem
    date = date_match.group(1) if date_match else "unknown"

    # Split by message markers
    messages = []

    # Find all user and claude messages
    user_pattern = r'## 👤 User\s*\n(.*?)(?=## 🤖 Claude|## 👤 User|$)'
    claude_pattern = r'## 🤖 Claude\s*\n(.*?)(?=## 👤 User|## 🤖 Claude|$)'

    # Get all messages in order
    all_matches = []

    for match in re.finditer(user_pattern, content, re.DOTALL):
        all_matches.append(('user', match.start(), match.group(1).strip()))

    for match in re.finditer(claude_pattern, content, re.DOTALL):
        all_matches.append(('assistant', match.start(), match.group(1).strip()))

    # Sort by position to maintain order
    all_matches.sort(key=lambda x: x[1])

    # Build message list
    for role, _, msg_content in all_matches:
        if msg_content:
            messages.append({
                "role": role,
                "content": msg_content
            })

    return {
        "session_id": session_id,
        "date": date,
        "file": md_file.name,
        "messages": messages
    }


def score_conversation_against_patterns(conversation: Dict) -> Dict[str, float]:
    """
    Score a conversation against the 10 documented patterns

    Returns dict of {pattern_name: score} where score is 0-1
    """
    scores = {}

    # Combine all assistant messages for scoring
    assistant_text = " ".join([
        msg["content"].lower()
        for msg in conversation["messages"]
        if msg["role"] == "assistant"
    ])

    for pattern_name, keywords in PATTERN_KEYWORDS.items():
        # Count keyword matches
        matches = sum(1 for keyword in keywords if keyword.lower() in assistant_text)

        # Normalize score (0-1)
        # More matches = higher score, but cap at number of keywords
        score = min(1.0, matches / len(keywords))

        scores[pattern_name] = score

    return scores


def calculate_overall_quality(conversation: Dict, pattern_scores: Dict[str, float]) -> float:
    """
    Calculate overall quality score for a conversation

    Factors:
    - Pattern coverage (how many patterns demonstrated)
    - Pattern strength (how strongly patterns are shown)
    - Conversation length (longer = more examples)
    - Message balance (good back-and-forth)
    """
    # Pattern coverage: how many patterns have score > 0.3
    strong_patterns = sum(1 for score in pattern_scores.values() if score > 0.3)
    coverage_score = strong_patterns / len(PATTERN_KEYWORDS)

    # Pattern strength: average of all pattern scores
    strength_score = sum(pattern_scores.values()) / len(pattern_scores)

    # Length score: prefer conversations with 4-10 exchanges
    num_exchanges = len(conversation["messages"]) // 2
    if 4 <= num_exchanges <= 10:
        length_score = 1.0
    elif num_exchanges < 4:
        length_score = num_exchanges / 4
    else:
        length_score = max(0.5, 10 / num_exchanges)

    # Balance score: check if conversation has good user/assistant balance
    user_msgs = sum(1 for msg in conversation["messages"] if msg["role"] == "user")
    assistant_msgs = sum(1 for msg in conversation["messages"] if msg["role"] == "assistant")
    balance_score = min(user_msgs, assistant_msgs) / max(user_msgs, assistant_msgs, 1)

    # Weighted overall score
    overall = (
        coverage_score * 0.4 +
        strength_score * 0.3 +
        length_score * 0.2 +
        balance_score * 0.1
    )

    return overall


def sanitize_conversation(conversation: Dict) -> Dict:
    """
    Clean/sanitize conversation content

    - Remove very long code blocks (keep first 50 lines)
    - Remove excessive whitespace
    - Keep the substance while reducing noise
    """
    sanitized_messages = []

    for msg in conversation["messages"]:
        content = msg["content"]

        # Truncate very long code blocks
        code_block_pattern = r'```[\w]*\n(.*?)\n```'
        def truncate_code(match):
            code = match.group(1)
            lines = code.split('\n')
            if len(lines) > 50:
                truncated = '\n'.join(lines[:50])
                return f'```\n{truncated}\n... (truncated)\n```'
            return match.group(0)

        content = re.sub(code_block_pattern, truncate_code, content, flags=re.DOTALL)

        # Remove excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)

        sanitized_messages.append({
            "role": msg["role"],
            "content": content.strip()
        })

    return {
        **conversation,
        "messages": sanitized_messages
    }


def main():
    """Main execution"""
    print("🔍 Parsing Real Claude Code Conversations")
    print("=" * 60)

    # Paths
    project_root = Path(__file__).parent.parent.parent.parent
    conversations_dir = project_root / "data/conversations/claude_code_conversations"
    output_file = project_root / "data/real_conversations_parsed.jsonl"

    # Find all conversation files
    md_files = list(conversations_dir.glob("*.md"))
    print(f"\n📂 Found {len(md_files)} conversation files")

    # Parse and score all conversations
    parsed_conversations = []

    for md_file in md_files:
        print(f"\n📄 Processing: {md_file.name}")

        # Parse
        conversation = parse_markdown_conversation(md_file)

        if len(conversation["messages"]) < 4:
            print(f"   ⏭️  Skipping (too short: {len(conversation['messages'])} messages)")
            continue

        # Score against patterns
        pattern_scores = score_conversation_against_patterns(conversation)

        # Calculate overall quality
        quality_score = calculate_overall_quality(conversation, pattern_scores)

        # Find top patterns
        top_patterns = sorted(pattern_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_pattern_names = [p[0] for p in top_patterns if p[1] > 0.3]

        print(f"   📊 Quality: {quality_score:.2f}")
        print(f"   🎯 Top patterns: {', '.join(top_pattern_names) if top_pattern_names else 'None strong'}")
        print(f"   💬 Messages: {len(conversation['messages'])}")

        # Sanitize
        conversation = sanitize_conversation(conversation)

        # Add metadata
        conversation["pattern_scores"] = pattern_scores
        conversation["quality_score"] = quality_score
        conversation["top_patterns"] = top_pattern_names

        parsed_conversations.append(conversation)

    # Sort by quality
    parsed_conversations.sort(key=lambda x: x["quality_score"], reverse=True)

    # Print summary
    print(f"\n📊 Summary:")
    print(f"   Total conversations: {len(parsed_conversations)}")
    print(f"   Average quality: {sum(c['quality_score'] for c in parsed_conversations) / len(parsed_conversations):.2f}")

    # Show top 5
    print(f"\n🏆 Top 5 Quality Conversations:")
    for i, conv in enumerate(parsed_conversations[:5], 1):
        print(f"   {i}. {conv['file']} - Quality: {conv['quality_score']:.2f}")
        print(f"      Patterns: {', '.join(conv['top_patterns'])}")

    # Save
    print(f"\n💾 Saving to {output_file}...")
    with open(output_file, 'w') as f:
        for conv in parsed_conversations:
            f.write(json.dumps(conv) + '\n')

    print(f"✅ Saved {len(parsed_conversations)} parsed conversations")

    # Recommendations
    print(f"\n💡 Recommendations:")
    high_quality = sum(1 for c in parsed_conversations if c["quality_score"] > 0.5)
    print(f"   - {high_quality} conversations with quality > 0.5")
    print(f"   - Use top {min(20, len(parsed_conversations))} for validation set")
    print(f"   - These show strong pattern alignment")


if __name__ == '__main__':
    main()
