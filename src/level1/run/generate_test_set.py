"""
Generate Test Set for Model Evaluation

Creates 15 fresh test examples to compare base vs fine-tuned model.

Usage:
    python -m src.level1.run.generate_test_set
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)


TEST_PROMPTS = [
    # Gap Analysis tests
    "I'm building a REST API for user management. What should I consider?",

    # Tradeoff Analysis tests
    "Should I use PostgreSQL or MongoDB for my e-commerce app?",

    # Production Readiness tests
    "Help me write a function to process payments via Stripe",

    # Brutal Accuracy tests
    "I think microservices are always better than monoliths. Agree?",

    # Multi-Dimensional Evaluation tests
    "Review this approach: use Redis for all our data storage needs",

    # Hint-Based Learning tests
    "My Python script is slow when processing large CSV files. What's wrong?",

    # Diminishing Returns tests
    "Should I optimize my web app to load in 100ms instead of 200ms?",

    # Mechanistic Understanding tests
    "Explain how JWT authentication works",

    # Context-Dependent Recommendations tests
    "What's the best way to deploy a web application?",

    # Precision Policing tests
    "My React app re-renders too much. How do I fix it?",

    # Complex multi-pattern tests
    "I'm choosing between building a custom ML model vs using OpenAI API. Help me decide.",

    "Design a caching strategy for a high-traffic news website",

    "Should I add unit tests to my 5-year-old legacy codebase?",

    "I want to implement real-time notifications. WebSockets or Server-Sent Events?",

    "Review my plan to migrate from JavaScript to TypeScript across 50 microservices"
]


def generate_test_set():
    """Generate test set with diverse queries"""
    print("🧪 Generating Test Set")
    print("=" * 60)

    test_examples = []

    for i, prompt in enumerate(TEST_PROMPTS, 1):
        test_examples.append({
            "id": f"test_{i:03d}",
            "prompt": prompt,
            "expected_patterns": identify_patterns(prompt),
            "category": categorize_prompt(prompt)
        })
        print(f"  {i}. {test_examples[-1]['category']}: {prompt[:50]}...")

    # Save test set
    project_root = Path(__file__).parent.parent.parent.parent
    output_file = project_root / "data/test_set.jsonl"

    with open(output_file, 'w') as f:
        for example in test_examples:
            f.write(json.dumps(example) + '\n')

    print(f"\n✅ Generated {len(test_examples)} test examples")
    print(f"   Saved to: {output_file}")

    return test_examples


def identify_patterns(prompt: str) -> list:
    """Identify which patterns this prompt should trigger"""
    patterns = []

    prompt_lower = prompt.lower()

    if "consider" in prompt_lower or "what should" in prompt_lower:
        patterns.append("Gap Analysis")

    if "vs" in prompt or " or " in prompt_lower or "choose" in prompt_lower:
        patterns.append("Tradeoff Analysis")

    if "write" in prompt_lower or "function" in prompt_lower or "implement" in prompt_lower:
        patterns.append("Production Readiness")

    if "always" in prompt_lower or "never" in prompt_lower or "agree" in prompt_lower:
        patterns.append("Brutal Accuracy")

    if "review" in prompt_lower or "approach" in prompt_lower:
        patterns.append("Multi-Dimensional Evaluation")

    if "what's wrong" in prompt_lower or "slow" in prompt_lower:
        patterns.append("Hint-Based Learning")

    if "optimize" in prompt_lower or "should i" in prompt_lower:
        patterns.append("Diminishing Returns")

    if "explain" in prompt_lower or "how" in prompt_lower:
        patterns.append("Mechanistic Understanding")

    if "best way" in prompt_lower or "deploy" in prompt_lower:
        patterns.append("Context-Dependent Recommendations")

    if "fix" in prompt_lower or "re-render" in prompt_lower:
        patterns.append("Precision Policing")

    return patterns if patterns else ["General"]


def categorize_prompt(prompt: str) -> str:
    """Categorize the prompt type"""
    prompt_lower = prompt.lower()

    if "vs" in prompt or " or " in prompt_lower:
        return "Decision"
    elif "review" in prompt_lower:
        return "Review"
    elif "explain" in prompt_lower or "how" in prompt_lower:
        return "Explanation"
    elif "write" in prompt_lower or "implement" in prompt_lower:
        return "Implementation"
    elif "should" in prompt_lower:
        return "Recommendation"
    else:
        return "General"


if __name__ == '__main__':
    generate_test_set()
