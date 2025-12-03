"""
Training Data Generator for Level 2 RUN

Generates synthetic training examples for tool acquisition fine-tuning.
Uses GPT-5.1 with high reasoning effort to create high-quality variations
of seed examples.

Categories:
1. Clear gap + free library (target: 30 examples)
2. Clear gap + paid API (target: 20 examples)
3. No gap detected (target: 20 examples)
4. Build recommended (target: 15 examples)
5. Ambiguous cases (target: 15 examples)

Total target: 100+ examples
"""

import json
import os
import random
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI


def load_env_from_project():
    """
    Load environment variables from .env file in project root.
    This ensures we use the project's .env, not shell environment.
    """
    # Find project root (where .env should be)
    current = Path(__file__).resolve()
    for parent in current.parents:
        env_file = parent / ".env"
        if env_file.exists():
            # override=True ensures .env takes precedence over shell env
            load_dotenv(env_file, override=True)
            print(f"Loaded environment from: {env_file}")
            return env_file

    print("Warning: No .env file found in project hierarchy")
    return None


@dataclass
class GenerationConfig:
    """Configuration for synthetic data generation."""
    target_total: int = 120
    category_targets: Dict[str, int] = None
    temperature: float = 0.8
    reasoning_effort: str = "high"
    max_synthetic: Optional[int] = None  # Limit total synthetic examples (for testing)

    def __post_init__(self):
        if self.category_targets is None:
            self.category_targets = {
                "free_library": 30,
                "paid_api": 20,
                "no_gap": 20,
                "build": 15,
                "ambiguous": 15
            }


@dataclass
class TrainingExample:
    """A single training example in OpenAI fine-tuning format."""
    messages: List[Dict[str, str]]
    category: str
    source: str  # "seed" or "synthetic"

    def to_jsonl_format(self) -> Dict:
        """Convert to JSONL format for fine-tuning."""
        return {"messages": self.messages}


class TrainingDataGenerator:
    """
    Generate synthetic training data for tool acquisition fine-tuning.

    Uses GPT-5.1 with high reasoning effort to create variations of
    seed examples while maintaining quality and diversity.
    """

    SYSTEM_PROMPT = (
        "You are a tool acquisition advisor. Analyze patterns to determine "
        "if tools are needed, recommend build vs buy, and provide confidence scores."
    )

    CATEGORY_DESCRIPTIONS = {
        "free_library": "Clear capability gap where a free, open-source library is the best solution",
        "paid_api": "Clear capability gap where a paid API service is recommended",
        "no_gap": "No capability gap - existing tools/stdlib are sufficient",
        "build": "Capability gap where building internally is recommended over external options",
        "ambiguous": "Unclear situation requiring clarifying questions or conditional recommendations"
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the generator.

        Args:
            api_key: OpenAI API key. If not provided, loads from .env file.
        """
        # Load .env from project root (override shell environment)
        load_env_from_project()

        # Use provided key, or fall back to .env-loaded OPENAI_API_KEY
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "No OpenAI API key found. Provide api_key parameter or set "
                "OPENAI_API_KEY in your .env file."
            )

        # Mask key for logging (show first 8 chars only)
        masked_key = resolved_key[:8] + "..." if len(resolved_key) > 8 else "***"
        print(f"Using OpenAI API key: {masked_key}")

        self.client = OpenAI(api_key=resolved_key)
        self.seed_examples: List[TrainingExample] = []
        self.generated_examples: List[TrainingExample] = []

    def load_seed_examples(self, seed_path: Path) -> int:
        """
        Load seed examples from JSONL file.

        Args:
            seed_path: Path to seed_examples.jsonl

        Returns:
            Number of examples loaded
        """
        self.seed_examples = []

        with open(seed_path, 'r') as f:
            for line in f:
                data = json.loads(line.strip())
                # Infer category from content
                category = self._infer_category(data['messages'])
                example = TrainingExample(
                    messages=data['messages'],
                    category=category,
                    source="seed"
                )
                self.seed_examples.append(example)

        print(f"Loaded {len(self.seed_examples)} seed examples")
        self._print_category_distribution(self.seed_examples, "Seed")
        return len(self.seed_examples)

    def load_existing_generated(self, output_path: Path) -> int:
        """
        Load existing generated examples from output file (for --resume).

        Args:
            output_path: Path to existing output JSONL file

        Returns:
            Number of synthetic examples loaded
        """
        if not output_path.exists():
            print(f"No existing file at {output_path}, starting fresh")
            return 0

        self.generated_examples = []
        seed_count = 0

        with open(output_path, 'r') as f:
            for line in f:
                data = json.loads(line.strip())
                category = self._infer_category(data['messages'])

                # Check if this is a seed or synthetic example
                # Seeds are in the seed file, so skip them here
                is_seed = any(
                    ex.messages[1]['content'] == data['messages'][1]['content']
                    for ex in self.seed_examples
                )

                if is_seed:
                    seed_count += 1
                else:
                    example = TrainingExample(
                        messages=data['messages'],
                        category=category,
                        source="synthetic"
                    )
                    self.generated_examples.append(example)

        print(f"Loaded {len(self.generated_examples)} existing synthetic examples (skipped {seed_count} seeds)")
        self._print_category_distribution(self.generated_examples, "Existing synthetic")
        return len(self.generated_examples)

    def _infer_category(self, messages: List[Dict]) -> str:
        """Infer category from assistant response content."""
        assistant_content = messages[-1]['content'].lower()

        if "do not acquire" in assistant_content or "gap exists:** no" in assistant_content:
            return "no_gap"
        elif "recommendation:** build" in assistant_content:
            return "build"
        elif "uncertain" in assistant_content or "conditional" in assistant_content:
            return "ambiguous"
        elif any(term in assistant_content for term in ["paid", "$", "/month", "subscription"]):
            if "auto-approve:** no" in assistant_content:
                return "paid_api"

        # Default to free_library for clear buy recommendations
        return "free_library"

    def _print_category_distribution(self, examples: List[TrainingExample], label: str):
        """Print distribution of examples across categories."""
        counts = {}
        for ex in examples:
            counts[ex.category] = counts.get(ex.category, 0) + 1

        print(f"\n{label} distribution:")
        for cat, count in sorted(counts.items()):
            print(f"  {cat}: {count}")

    def generate_synthetic_examples(
        self,
        config: GenerationConfig = None,
        output_path: Optional[Path] = None
    ) -> List[TrainingExample]:
        """
        Generate synthetic examples using GPT-5.1.

        Args:
            config: Generation configuration
            output_path: Optional path to save intermediate results

        Returns:
            List of generated examples
        """
        config = config or GenerationConfig()

        # Don't reset generated_examples if resuming (they're already loaded)
        # Only reset if starting fresh
        if not self.generated_examples:
            self.generated_examples = []

        # Calculate how many to generate per category
        # Count both seed and existing synthetic examples
        category_counts = {cat: 0 for cat in config.category_targets.keys()}
        for ex in self.seed_examples:
            if ex.category in category_counts:
                category_counts[ex.category] += 1
        for ex in self.generated_examples:
            if ex.category in category_counts:
                category_counts[ex.category] += 1

        print("\nGenerating synthetic examples...")
        print(f"Target total: {config.target_total}")

        for category, target in config.category_targets.items():
            current = category_counts.get(category, 0)
            needed = max(0, target - current)

            if needed == 0:
                print(f"  {category}: Already have {current}/{target}")
                continue

            print(f"  {category}: Generating {needed} (have {current}/{target})")

            # Get seed examples for this category
            category_seeds = [ex for ex in self.seed_examples if ex.category == category]
            if not category_seeds:
                # Use any seed as inspiration
                category_seeds = self.seed_examples

            # Generate examples
            for i in range(needed):
                # Check if we've hit max_synthetic limit
                if config.max_synthetic and len(self.generated_examples) >= config.max_synthetic:
                    print(f"\n  Reached max_synthetic limit ({config.max_synthetic}), stopping.")
                    break

                seed = random.choice(category_seeds)
                try:
                    new_example = self._generate_variation(seed, category, config)
                    if new_example:
                        self.generated_examples.append(new_example)
                        print(f"    [{len(self.generated_examples)}] Generated: {category}")

                        # Save intermediate results
                        if output_path and len(self.generated_examples) % 5 == 0:
                            self._save_intermediate(output_path)

                        # Rate limiting
                        time.sleep(0.5)

                except Exception as e:
                    print(f"    Error generating example {i+1}: {e}")
                    continue

            # Check again after category loop
            if config.max_synthetic and len(self.generated_examples) >= config.max_synthetic:
                break

        print(f"\nGenerated {len(self.generated_examples)} synthetic examples")
        self._print_category_distribution(self.generated_examples, "Synthetic")

        return self.generated_examples

    # JSON Schema for structured output
    OUTPUT_SCHEMA = {
        "type": "object",
        "properties": {
            "user_content": {
                "type": "string",
                "description": "The user query in format: Pattern: [name]\\nDescription: [desc]\\nCurrent capabilities: [caps]\\nQuery: [question]"
            },
            "assistant_content": {
                "type": "string",
                "description": "Full analysis with Gap Analysis, Build vs Buy Recommendation, and Decision sections"
            }
        },
        "required": ["user_content", "assistant_content"],
        "additionalProperties": False
    }

    def _generate_variation(
        self,
        seed: TrainingExample,
        target_category: str,
        config: GenerationConfig
    ) -> Optional[TrainingExample]:
        """
        Generate a variation of a seed example using GPT-5.1.

        Args:
            seed: Seed example to base variation on
            target_category: Target category for the new example
            config: Generation configuration

        Returns:
            New TrainingExample or None if generation failed
        """
        # Build generation prompt
        generation_prompt = self._build_generation_prompt(seed, target_category)

        try:
            result = self.client.responses.create(
                model="gpt-5.1",
                input=generation_prompt,
                reasoning={"effort": config.reasoning_effort},
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "training_example",
                        "schema": self.OUTPUT_SCHEMA,
                        "strict": True,
                    }
                },
            )

            response_text = result.output_text

            # Parse the structured JSON response
            new_example = self._parse_generated_example(response_text, target_category)
            return new_example

        except Exception as e:
            print(f"    GPT-5.1 error: {e}")
            return None

    def _build_generation_prompt(self, seed: TrainingExample, target_category: str) -> str:
        """Build the prompt for generating a new example."""

        # Extract user query and assistant response from seed
        seed_user = seed.messages[1]['content']
        seed_assistant = seed.messages[2]['content']

        prompt = f"""Generate a NEW training example for a tool acquisition advisor AI.

TARGET CATEGORY: {target_category}
CATEGORY DESCRIPTION: {self.CATEGORY_DESCRIPTIONS[target_category]}

REFERENCE EXAMPLE (for style and format, but generate something DIFFERENT):

User Query:
{seed_user}

Assistant Response:
{seed_assistant}

---

Generate a COMPLETELY NEW example with:
1. A DIFFERENT pattern/scenario (not the same topic as the reference)
2. The same structured format (Gap Analysis, Build vs Buy, Decision)
3. Appropriate for the target category: {target_category}

Think of realistic software engineering scenarios like:
- Testing frameworks and tools
- Documentation generation
- API mocking
- Database tools
- Logging and monitoring
- CI/CD automation
- Code formatting/linting
- Authentication/authorization
- Data validation
- File processing
- Network utilities
- Caching solutions
- Message queues
- Search functionality

OUTPUT FORMAT (JSON):
{{
  "user_content": "Pattern: [name]\\nDescription: [description]\\nCurrent capabilities: [what we have]\\nQuery: [question]",
  "assistant_content": "[Full analysis following the format from the reference]"
}}

Generate only the JSON, no other text."""

        return prompt

    def _parse_generated_example(
        self,
        response_text: str,
        category: str
    ) -> Optional[TrainingExample]:
        """Parse GPT-5.1 structured JSON response into a TrainingExample."""
        try:
            # With structured output, response is guaranteed valid JSON
            data = json.loads(response_text)

            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": data["user_content"]},
                {"role": "assistant", "content": data["assistant_content"]}
            ]

            return TrainingExample(
                messages=messages,
                category=category,
                source="synthetic"
            )

        except (json.JSONDecodeError, KeyError) as e:
            print(f"    Parse error: {e}")
            return None

    def _save_intermediate(self, output_path: Path):
        """Save intermediate results to avoid data loss."""
        intermediate_path = output_path.with_suffix('.intermediate.jsonl')
        self.save_all_examples(intermediate_path)

    def save_all_examples(self, output_path: Path):
        """
        Save all examples (seed + generated) to JSONL file.

        Args:
            output_path: Path to output file
        """
        all_examples = self.seed_examples + self.generated_examples

        with open(output_path, 'w') as f:
            for example in all_examples:
                f.write(json.dumps(example.to_jsonl_format()) + '\n')

        print(f"\nSaved {len(all_examples)} examples to {output_path}")

    def save_generated_only(self, output_path: Path):
        """Save only generated examples to JSONL file."""
        with open(output_path, 'w') as f:
            for example in self.generated_examples:
                f.write(json.dumps(example.to_jsonl_format()) + '\n')

        print(f"Saved {len(self.generated_examples)} generated examples to {output_path}")

    def get_statistics(self) -> Dict:
        """Get statistics about the generated dataset."""
        all_examples = self.seed_examples + self.generated_examples

        stats = {
            "total": len(all_examples),
            "seed": len(self.seed_examples),
            "synthetic": len(self.generated_examples),
            "by_category": {},
            "by_source": {
                "seed": len(self.seed_examples),
                "synthetic": len(self.generated_examples)
            }
        }

        for example in all_examples:
            cat = example.category
            if cat not in stats["by_category"]:
                stats["by_category"][cat] = {"seed": 0, "synthetic": 0, "total": 0}
            stats["by_category"][cat][example.source] += 1
            stats["by_category"][cat]["total"] += 1

        return stats


def main():
    """Main entry point for training data generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic training data for Level 2 RUN")
    parser.add_argument(
        "--seed-path",
        type=Path,
        default=Path("data/finetuning/seed_examples.jsonl"),
        help="Path to seed examples JSONL file"
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/finetuning/train_level2_run.jsonl"),
        help="Path to output JSONL file"
    )
    parser.add_argument(
        "--target-total",
        type=int,
        default=120,
        help="Target total number of examples"
    )
    parser.add_argument(
        "--reasoning-effort",
        choices=["low", "medium", "high"],
        default="high",
        help="GPT-5.1 reasoning effort level"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load seeds and print stats without generating"
    )
    parser.add_argument(
        "--max-synthetic",
        type=int,
        default=None,
        help="Maximum number of synthetic examples to generate (for testing)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing output file, skipping already-completed categories"
    )
    parser.add_argument(
        "--categories",
        type=str,
        default=None,
        help="Comma-separated list of categories to generate (e.g., 'build,ambiguous,no_gap,paid_api')"
    )
    parser.add_argument(
        "--category-targets",
        type=str,
        default=None,
        help="Category targets as JSON (e.g., '{\"build\": 20, \"ambiguous\": 20}')"
    )

    args = parser.parse_args()

    # Initialize generator
    generator = TrainingDataGenerator()

    # Load seed examples
    if not args.seed_path.exists():
        print(f"Error: Seed file not found: {args.seed_path}")
        return 1

    generator.load_seed_examples(args.seed_path)

    # Load existing generated examples if resuming
    if args.resume:
        generator.load_existing_generated(args.output_path)

    if args.dry_run:
        print("\n[Dry run - not generating synthetic examples]")
        stats = generator.get_statistics()
        print(f"\nCurrent statistics:")
        print(json.dumps(stats, indent=2))
        return 0

    # Configure generation
    category_targets = None
    if args.category_targets:
        category_targets = json.loads(args.category_targets)
    elif args.categories:
        # If only categories specified, set high targets for those categories
        selected = [c.strip() for c in args.categories.split(",")]
        category_targets = {cat: 25 for cat in selected}  # Default 25 each for selected
        # Set 0 for non-selected categories
        all_cats = ["free_library", "paid_api", "no_gap", "build", "ambiguous"]
        for cat in all_cats:
            if cat not in category_targets:
                category_targets[cat] = 0

    config = GenerationConfig(
        target_total=args.target_total,
        reasoning_effort=args.reasoning_effort,
        max_synthetic=args.max_synthetic,
        category_targets=category_targets
    )

    # Generate synthetic examples
    generator.generate_synthetic_examples(config, args.output_path)

    # Save results
    generator.save_all_examples(args.output_path)

    # Print final statistics
    stats = generator.get_statistics()
    print(f"\nFinal statistics:")
    print(json.dumps(stats, indent=2))

    return 0


if __name__ == "__main__":
    exit(main())
