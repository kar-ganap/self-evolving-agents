"""
Generate a held-out test set with completely novel patterns.

Creates 20 new examples (4 per category) that are NOT in training or validation.

Usage:
    uv run python -m src.level2.run.generate_test_set
"""

import json
import os
import random
import time
from pathlib import Path
from typing import Set, Dict, List, Optional
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI


@dataclass
class TestExample:
    """A single test example."""
    messages: List[Dict[str, str]]
    category: str
    pattern_name: str


def load_env():
    """Load .env from project root."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path, override=True)


def get_existing_patterns(data_dir: Path) -> Set[str]:
    """Get all patterns from training and validation files."""
    patterns = set()

    files = [
        data_dir / "train_v2.jsonl",
        data_dir / "validation_v2.jsonl",
        data_dir / "train_level2_run_v3.jsonl",
        data_dir / "train_additional.jsonl",
        data_dir / "train_build_extra.jsonl",
    ]

    for f in files:
        if f.exists():
            with open(f, 'r') as file:
                for line in file:
                    if line.strip():
                        ex = json.loads(line)
                        user_content = ex['messages'][1]['content']
                        for l in user_content.split('\n'):
                            if l.startswith('Pattern:'):
                                patterns.add(l.replace('Pattern:', '').strip().lower())
                                break

    return patterns


# Novel scenario ideas for test set - completely different from training
NOVEL_SCENARIOS = {
    "free_library": [
        ("Image Processing Pipeline", "Resizing, cropping, and format conversion for uploaded images"),
        ("PDF Generation", "Creating PDF reports from structured data"),
        ("Markdown Parsing", "Converting markdown to HTML with syntax highlighting"),
        ("Date/Time Handling", "Complex timezone conversions and date arithmetic"),
        ("CSV Data Export", "Generating CSV files from database queries"),
        ("HTML Sanitization", "Cleaning user-submitted HTML to prevent XSS"),
        ("Password Hashing", "Securely storing and verifying user passwords"),
        ("URL Parsing & Validation", "Extracting components from URLs and validating format"),
    ],
    "paid_api": [
        ("SMS Notifications", "Sending SMS alerts for critical system events"),
        ("Video Transcoding", "Converting uploaded videos to multiple formats/resolutions"),
        ("Speech-to-Text", "Transcribing audio recordings from customer support calls"),
        ("Address Verification", "Validating and standardizing shipping addresses"),
        ("Credit Card Processing", "Accepting payments in an e-commerce checkout"),
        ("Cloud Object Storage", "Storing and retrieving large files with CDN delivery"),
        ("Real-time Translation", "Translating user chat messages between languages"),
        ("Background Check API", "Verifying identity for user onboarding"),
    ],
    "no_gap": [
        ("Simple String Formatting", "Capitalizing names and formatting phone numbers"),
        ("Basic Math Calculations", "Computing percentages and averages for reports"),
        ("List Sorting & Filtering", "Sorting users by join date and filtering by status"),
        ("Dictionary Manipulation", "Merging configuration dictionaries"),
        ("File Path Operations", "Joining paths and checking file extensions"),
        ("UUID Generation", "Creating unique identifiers for database records"),
        ("Basic Regex Matching", "Validating email format with simple pattern"),
        ("JSON Parsing", "Reading configuration from JSON files"),
    ],
    "build": [
        ("Custom Business Rules Engine", "Domain-specific validation rules unique to our industry"),
        ("Proprietary Scoring Algorithm", "Our secret sauce for ranking recommendations"),
        ("Internal Workflow Orchestrator", "Coordinating our specific multi-step approval process"),
        ("Legacy System Adapter", "Bridging our 20-year-old mainframe to modern APIs"),
        ("Custom Authorization Model", "Our unique role-permission hierarchy"),
        ("Domain-Specific DSL", "A mini-language for configuring our product rules"),
        ("Custom Audit Trail", "Tracking changes per our regulatory requirements"),
        ("Specialized Report Generator", "Our unique multi-dimensional pivot reports"),
    ],
    "ambiguous": [
        ("Real-time Collaboration", "Google Docs-like editing, but usage unclear"),
        ("Machine Learning Inference", "Need predictions but model complexity varies"),
        ("Graph Database Queries", "Social network traversal, scale unknown"),
        ("WebSocket Communication", "Real-time updates, but traffic patterns unclear"),
        ("Batch Job Processing", "ETL pipeline, but data volume unspecified"),
        ("Event Sourcing", "Audit trail needs, but domain complexity unclear"),
        ("Rate Limiting Implementation", "API protection, but traffic patterns unknown"),
        ("Distributed Locking", "Concurrency control, but cluster size varies"),
    ],
}

SYSTEM_PROMPT = (
    "You are a tool acquisition advisor. Analyze patterns to determine "
    "if tools are needed, recommend build vs buy, and provide confidence scores."
)

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "user_content": {
            "type": "string",
            "description": "The user query in format: Pattern: [name]\nDescription: [desc]\nCurrent capabilities: [caps]\nQuery: [question]"
        },
        "assistant_content": {
            "type": "string",
            "description": "Full analysis with Gap Analysis, Build vs Buy Recommendation, and Decision sections"
        }
    },
    "required": ["user_content", "assistant_content"],
    "additionalProperties": False
}

CATEGORY_DESCRIPTIONS = {
    "free_library": "Clear capability gap where a free, open-source library is the best solution",
    "paid_api": "Clear capability gap where a paid API service is recommended",
    "no_gap": "No capability gap - existing tools/stdlib are sufficient",
    "build": "Capability gap where building internally is recommended over external options",
    "ambiguous": "Unclear situation requiring clarifying questions or conditional recommendations"
}


def generate_test_example(
    client: OpenAI,
    category: str,
    scenario: tuple,
    existing_patterns: Set[str],
) -> Optional[TestExample]:
    """Generate a single test example for a scenario."""
    pattern_name, description = scenario

    # Skip if pattern already exists
    if pattern_name.lower() in existing_patterns:
        print(f"  Skipping '{pattern_name}' - already exists")
        return None

    prompt = f"""Generate a training example for a tool acquisition advisor AI.

TARGET CATEGORY: {category}
CATEGORY DESCRIPTION: {CATEGORY_DESCRIPTIONS[category]}

SCENARIO:
Pattern: {pattern_name}
Description: {description}

Generate a realistic user query and a detailed assistant response.

The user query should follow this format:
Pattern: {pattern_name}
Description: [expand on the description with specifics]
Current capabilities: [what the project currently has]
Query: [a question about acquiring tools for this pattern]

The assistant response should include:
1. **Gap Analysis** - Does a capability gap exist? What specific functionality is missing?
2. **Build vs Buy Analysis** - Evaluate options, consider cost/maintenance
3. **Recommendation** - Clear recommendation matching the target category ({category})
4. **Decision** section with:
   - Gap Exists: yes/no
   - Recommendation: build/buy/do not acquire
   - Auto-approve: yes/no/conditional
   - Specific tool recommendations (if applicable)

For '{category}' category:
{"- Recommend a specific open-source library/package" if category == "free_library" else ""}
{"- Recommend a paid API service with pricing info" if category == "paid_api" else ""}
{"- Explain why no external tool is needed, stdlib is sufficient" if category == "no_gap" else ""}
{"- Recommend building internally, explain why external options don't fit" if category == "build" else ""}
{"- Ask clarifying questions, provide conditional recommendations" if category == "ambiguous" else ""}

OUTPUT FORMAT (JSON):
{{
  "user_content": "Pattern: ...\nDescription: ...\nCurrent capabilities: ...\nQuery: ...",
  "assistant_content": "**Gap Analysis**\n...\n\n**Build vs Buy Analysis**\n...\n\n**Recommendation**\n...\n\n**Decision**\n..."
}}
"""

    try:
        result = client.responses.create(
            model="gpt-5.1",
            input=prompt,
            reasoning={"effort": "high"},
            text={
                "format": {
                    "type": "json_schema",
                    "name": "training_example",
                    "schema": OUTPUT_SCHEMA,
                    "strict": True,
                }
            },
        )

        data = json.loads(result.output_text)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": data["user_content"]},
            {"role": "assistant", "content": data["assistant_content"]}
        ]

        return TestExample(
            messages=messages,
            category=category,
            pattern_name=pattern_name
        )

    except Exception as e:
        print(f"  Error generating '{pattern_name}': {e}")
        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate held-out test set")
    parser.add_argument("--examples-per-category", type=int, default=4,
                       help="Number of examples per category")
    parser.add_argument("--output", type=Path,
                       default=Path("data/finetuning/test_holdout.jsonl"),
                       help="Output file path")

    args = parser.parse_args()

    load_env()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    data_dir = Path("data/finetuning")
    existing_patterns = get_existing_patterns(data_dir)
    print(f"Found {len(existing_patterns)} existing patterns to avoid")

    generated = []

    for category, scenarios in NOVEL_SCENARIOS.items():
        print(f"\nGenerating {category} examples...")

        # Shuffle and take requested number
        available = [s for s in scenarios if s[0].lower() not in existing_patterns]
        random.shuffle(available)

        count = 0
        for scenario in available:
            if count >= args.examples_per_category:
                break

            print(f"  Generating: {scenario[0]}...")
            example = generate_test_example(client, category, scenario, existing_patterns)

            if example:
                generated.append(example)
                existing_patterns.add(example.pattern_name.lower())
                count += 1
                print(f"    ✓ Generated")

            time.sleep(0.5)  # Rate limiting

        print(f"  Generated {count}/{args.examples_per_category} for {category}")

    # Save test set
    with open(args.output, 'w') as f:
        for ex in generated:
            f.write(json.dumps({"messages": ex.messages}) + '\n')

    print(f"\n{'='*50}")
    print(f"Generated {len(generated)} test examples")
    print(f"Saved to: {args.output}")

    # Print distribution
    by_cat = {}
    for ex in generated:
        by_cat[ex.category] = by_cat.get(ex.category, 0) + 1

    print("\nDistribution:")
    for cat, count in sorted(by_cat.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
