"""
Synthetic Data Generator for Level 1 Fine-Tuning (Milestone 1.13)

Generates synthetic coding conversations using OpenAI and Google Gemini APIs.
Applies Kartik's learned patterns to diverse coding topics.

Usage:
    python -m src.level1.run.synthetic_data_generator --provider openai --count 100
    python -m src.level1.run.synthetic_data_generator --provider gemini --count 100
"""

import os
import json
import time
import random
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import argparse

# API clients
import openai
from google import genai

from src.common.utils import save_jsonl, timer, ProgressTracker


@dataclass
class GenerationConfig:
    """Configuration for synthetic data generation"""
    provider: str  # 'openai' or 'gemini'
    model: str
    temperature: float = 0.8
    max_tokens: int = 3000
    seed: Optional[int] = 42  # For reproducibility

    @classmethod
    def for_provider(cls, provider: str, seed: Optional[int] = 42):
        if provider == 'openai':
            return cls(
                provider='openai',
                model='gpt-4o',
                temperature=0.8,
                max_tokens=3000,
                seed=seed
            )
        elif provider == 'gemini':
            return cls(
                provider='gemini',
                model='gemini-2.5-pro',
                temperature=0.8,
                max_tokens=3000,
                seed=seed
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")


# Diverse coding topics for synthetic data generation
CODING_TOPICS = [
    # Systems & Infrastructure
    "distributed lock implementation",
    "load balancer design",
    "database connection pooling",
    "caching strategy for high-traffic API",
    "message queue consumer implementation",
    "circuit breaker pattern",
    "retry mechanism with exponential backoff",
    "service mesh architecture",
    "API gateway design",
    "distributed tracing implementation",

    # Data Structures & Algorithms
    "LRU cache implementation",
    "trie data structure for autocomplete",
    "consistent hashing algorithm",
    "bloom filter implementation",
    "skip list design",
    "union-find data structure",
    "segment tree for range queries",
    "binary indexed tree (Fenwick tree)",
    "red-black tree implementation",
    "B-tree for database indexing",

    # Concurrency & Performance
    "thread pool implementation",
    "producer-consumer pattern",
    "read-write lock optimization",
    "lock-free queue design",
    "async task scheduler",
    "parallel batch processor",
    "connection pooling with backpressure",
    "rate limiter with token bucket",
    "debouncing vs throttling implementation",
    "worker pool for CPU-bound tasks",

    # Web & APIs
    "REST API versioning strategy",
    "GraphQL query optimization",
    "websocket server implementation",
    "SSE (server-sent events) for real-time updates",
    "OAuth2 authentication flow",
    "JWT token management",
    "API pagination implementation",
    "webhook delivery system",
    "file upload handling with streaming",
    "CORS middleware implementation",

    # Testing & Quality
    "test fixture management",
    "mock vs stub vs fake strategy",
    "integration test database setup",
    "flaky test detection",
    "test coverage measurement",
    "contract testing implementation",
    "mutation testing approach",
    "performance benchmark suite",
    "chaos engineering tests",
    "smoke test automation",

    # Security
    "input validation framework",
    "SQL injection prevention",
    "XSS protection middleware",
    "CSRF token implementation",
    "password hashing strategy",
    "secrets management system",
    "API key rotation mechanism",
    "security header configuration",
    "audit logging system",
    "rate limiting for DDoS protection",

    # Observability
    "structured logging implementation",
    "metrics collection system",
    "distributed tracing setup",
    "health check endpoint design",
    "alerting threshold configuration",
    "log aggregation pipeline",
    "custom metric instrumentation",
    "error tracking integration",
    "performance monitoring dashboard",
    "SLA measurement framework",

    # Architecture & Design
    "event-driven architecture design",
    "CQRS pattern implementation",
    "saga pattern for distributed transactions",
    "strangler fig migration pattern",
    "feature flag system",
    "plugin architecture design",
    "dependency injection container",
    "observer pattern for event handling",
    "repository pattern implementation",
    "factory pattern for object creation",

    # Data & Storage
    "database migration strategy",
    "data denormalization approach",
    "sharding key selection",
    "read replica configuration",
    "write-ahead logging implementation",
    "eventual consistency handling",
    "data retention policy implementation",
    "backup and restore system",
    "data validation pipeline",
    "ETL job orchestration",

    # DevOps & Deployment
    "zero-downtime deployment",
    "blue-green deployment strategy",
    "canary release implementation",
    "rollback mechanism design",
    "configuration management system",
    "secrets injection in CI/CD",
    "health check before deployment",
    "database migration in deployment",
    "container orchestration setup",
    "infrastructure as code design"
]

# 10 learned patterns for even distribution
PATTERNS = [
    "Gap Analysis",
    "Tradeoff Analysis",
    "Production Readiness",
    "Brutal Accuracy",
    "Multi-Dimensional Evaluation",
    "Hint-Based Learning",
    "Diminishing Returns",
    "Mechanistic Understanding",
    "Context-Dependent Recommendations",
    "Precision Policing"
]


class SyntheticDataGenerator:
    """Generates synthetic coding conversations using LLM APIs"""

    def __init__(self, config: GenerationConfig):
        self.config = config
        self.setup_client()
        self.load_context_files()

    def setup_client(self):
        """Initialize API client based on provider"""
        if self.config.provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            self.client = openai.OpenAI(api_key=api_key)
        elif self.config.provider == 'gemini':
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment")
            self.client = genai.Client(api_key=api_key)

    def load_context_files(self):
        """Load patterns, examples, and preferences from docs"""
        docs_dir = Path(__file__).parent.parent.parent.parent / "docs"

        with open(docs_dir / "01_extracted_patterns.md", 'r') as f:
            self.patterns_content = f.read()

        with open(docs_dir / "02_synthetic_conversations.md", 'r') as f:
            self.examples_content = f.read()

        with open(docs_dir / "03_preference_profile.md", 'r') as f:
            self.preferences_content = f.read()

    def build_prompt(self, topic: str, patterns_to_apply: List[str]) -> str:
        """Build prompt for generating a synthetic conversation"""
        patterns_str = ", ".join(patterns_to_apply)
        prompt = f"""You are generating a synthetic coding conversation that demonstrates specific interaction patterns.

# Context
Generate a conversation between a user and an AI coding assistant about: **{topic}**

The conversation should demonstrate learned patterns from real conversations while discussing this new topic.

# Patterns to Apply (MUST use these specific patterns): {patterns_str}

# All Available Patterns for Reference:

1. **Gap Analysis**: Systematically identify what's missing (✓ ⚠️ ✗ scoring)
2. **Tradeoff Analysis**: Compare alternatives with context-dependent recommendations
3. **Production Readiness**: Consider monitoring, error handling, edge cases, scalability
4. **Brutal Accuracy**: Challenge logical connections, don't accept claims at face value
5. **Multi-Dimensional Evaluation**: Separate scores for functionality, quality, performance, security
6. **Hint-Based Learning**: For debugging, give strategic hints not solutions
7. **Diminishing Returns**: Quantify ROI, identify point where effort isn't worth it
8. **Mechanistic Understanding**: Explain HOW things work, trace execution
9. **Context-Dependent Recommendations**: No universal answers, always factor in constraints
10. **Precision Policing**: Use exact technical terms, correct imprecise language

# Response Structure (for implementation requests):
1. Clarify context first (scale, requirements, constraints)
2. Present tradeoff analysis for 2-3 alternatives
3. Recommend based on context
4. Provide implementation with edge case handling
5. List what's missing (production checklist)

# Instructions
1. Generate a realistic conversation (3-5 exchanges) about "{topic}"
2. Apply at least 2-3 of the learned patterns
3. Include code where relevant
4. Demonstrate pattern characteristics naturally
5. Make it feel like a real coding discussion

# Output Format
Return ONLY a valid JSON object (no markdown, no extra text):
{{
    "topic": "{topic}",
    "patterns_applied": ["Pattern Name 1", "Pattern Name 2"],
    "conversation": [
        {{"role": "user", "content": "user message here"}},
        {{"role": "assistant", "content": "assistant response here"}},
        {{"role": "user", "content": "follow-up question"}},
        {{"role": "assistant", "content": "detailed response"}}
    ],
    "learning_notes": "Brief explanation of which patterns were applied and how"
}}

Generate the conversation now. Remember: ONLY return the JSON, no other text."""

        return prompt

    @timer
    def generate_one(self, topic: str, patterns_to_apply: List[str], retry_count: int = 3) -> Optional[Dict]:
        """Generate a single synthetic conversation with retries"""
        prompt = self.build_prompt(topic, patterns_to_apply)

        for attempt in range(retry_count):
            try:
                if self.config.provider == 'openai':
                    response = self.client.chat.completions.create(
                        model=self.config.model,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }],
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens
                    )
                    content = response.choices[0].message.content

                elif self.config.provider == 'gemini':
                    response = self.client.models.generate_content(
                        model=self.config.model,
                        contents=prompt,
                        config=genai.types.GenerateContentConfig(
                            temperature=self.config.temperature,
                            max_output_tokens=self.config.max_tokens
                        )
                    )
                    content = response.text

                # Parse JSON response
                # Clean up markdown code blocks if present
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()

                result = json.loads(content)

                # Validate structure
                required_keys = ['topic', 'patterns_applied', 'conversation', 'learning_notes']
                if all(key in result for key in required_keys):
                    return result
                else:
                    print(f"  ⚠️  Missing required keys (attempt {attempt+1}/{retry_count})")
                    continue

            except json.JSONDecodeError as e:
                print(f"  ⚠️  JSON parse error (attempt {attempt+1}/{retry_count}): {e}")
                if attempt == retry_count - 1:
                    print(f"  ✗ Failed to parse response: {content[:200]}...")
                continue
            except Exception as e:
                print(f"  ⚠️  API error (attempt {attempt+1}/{retry_count}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue

        return None

    def generate_batch(self, count: int, output_file: Path) -> List[Dict]:
        """Generate multiple synthetic conversations"""
        print(f"\n🚀 Generating {count} synthetic conversations using {self.config.provider}...")
        print(f"   Model: {self.config.model}")
        print(f"   Seed: {self.config.seed}")
        print(f"   Output: {output_file}\n")

        # Set random seed for reproducibility
        if self.config.seed is not None:
            random.seed(self.config.seed)

        # Shuffle topics for diversity (reproducible with seed)
        topics = random.sample(CODING_TOPICS * 10, count)  # Repeat topics if needed

        # Distribute patterns evenly across examples
        # Each example gets 2-3 patterns
        pattern_assignments = []
        for i in range(count):
            # Cycle through patterns evenly, picking 2-3 at a time
            num_patterns = 2 if i % 2 == 0 else 3  # Alternate between 2 and 3 patterns
            start_idx = (i * 2) % len(PATTERNS)
            selected_patterns = []
            for j in range(num_patterns):
                selected_patterns.append(PATTERNS[(start_idx + j) % len(PATTERNS)])
            pattern_assignments.append(selected_patterns)

        results = []
        progress = ProgressTracker(count, "conversations")

        for i, (topic, patterns) in enumerate(zip(topics, pattern_assignments), 1):
            patterns_str = ", ".join(patterns)
            print(f"[{i}/{count}] {topic}")
            print(f"           Patterns: {patterns_str}")
            result = self.generate_one(topic, patterns)

            if result:
                results.append(result)
                print(f"  ✓ Generated ({len(result['conversation'])} exchanges)")

                # Save incrementally (don't lose progress)
                save_jsonl(results, output_file)
            else:
                print(f"  ✗ Failed to generate")

            progress.update()

            # Rate limiting
            if i < count:
                time.sleep(1)  # Be nice to the APIs

        print(f"\n✅ Generated {len(results)}/{count} conversations")
        print(f"   Saved to: {output_file}")

        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate synthetic training data")
    parser.add_argument(
        '--provider',
        choices=['openai', 'gemini'],
        required=True,
        help='API provider to use'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=100,
        help='Number of conversations to generate (default: 100)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='Output directory (default: data/synthetic/<provider>/)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    args = parser.parse_args()

    # Setup output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = Path(__file__).parent.parent.parent.parent / "data" / "synthetic" / args.provider

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"synthetic_conversations_{args.count}_seed{args.seed}.jsonl"

    # Generate
    config = GenerationConfig.for_provider(args.provider, seed=args.seed)
    generator = SyntheticDataGenerator(config)
    generator.generate_batch(args.count, output_file)


if __name__ == '__main__':
    main()
