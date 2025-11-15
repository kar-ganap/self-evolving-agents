"""
Level 1 Agent - Memory-Augmented Prompting with Fine-Tuned Model

Integrates pattern detection, prompt augmentation, and fine-tuned model inference
to provide pattern-aware responses.
"""

import os
from typing import Optional
from dataclasses import dataclass

from openai import OpenAI

from src.level1.runtime.pattern_matcher import PatternMatcher
from src.level1.runtime.prompt_generator import PromptGenerator


@dataclass
class AgentResponse:
    """Response from the Level 1 agent"""
    response: str
    detected_patterns: list
    augmentations_applied: list
    model_used: str


class Level1Agent:
    """
    Level 1 Agent using Memory-Augmented Prompting.

    Architecture:
        User Query → Pattern Detection → Prompt Augmentation → Fine-Tuned Model → Response

    This agent demonstrates learned preferences through:
    1. Pattern matching to identify relevant learned behaviors
    2. Prompt augmentation to inject pattern-specific context
    3. Fine-tuned model inference to apply learned patterns
    """

    def __init__(
        self,
        finetuned_model_id: Optional[str] = None,
        use_pattern_augmentation: bool = True,
        api_key: Optional[str] = None
    ):
        """
        Initialize the Level 1 Agent.

        Args:
            finetuned_model_id: OpenAI fine-tuned model ID (e.g., "ft:gpt-4o-2024-08-06:...")
                              If None, will try to load from data/finetuned_model_info.json
            use_pattern_augmentation: Whether to use pattern-based prompt augmentation
            api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
        """
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

        # Load fine-tuned model ID
        self.finetuned_model_id = finetuned_model_id or self._load_model_id()

        # Initialize pattern matching and prompt generation
        self.use_pattern_augmentation = use_pattern_augmentation
        self.pattern_matcher = PatternMatcher()
        self.prompt_generator = PromptGenerator()

    def _load_model_id(self) -> Optional[str]:
        """Load fine-tuned model ID from data/finetuned_model_info.json"""
        try:
            import json
            from pathlib import Path

            project_root = Path(__file__).parent.parent.parent.parent
            model_info_path = project_root / "data" / "finetuned_model_info.json"

            if model_info_path.exists():
                with open(model_info_path, 'r') as f:
                    model_info = json.load(f)
                    return model_info.get("fine_tuned_model")

            print("⚠️  No fine-tuned model info found. Will use base GPT-4.1 model.")
            return None

        except Exception as e:
            print(f"⚠️  Error loading model info: {e}")
            return None

    def query(
        self,
        user_query: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_patterns: int = 2
    ) -> AgentResponse:
        """
        Process a user query with pattern-aware prompting.

        Args:
            user_query: The user's question or request
            temperature: Sampling temperature for generation
            max_tokens: Maximum tokens in response
            top_patterns: How many top patterns to use for augmentation

        Returns:
            AgentResponse with the model's response and metadata
        """
        # Step 1: Detect patterns in the query
        detected_patterns = []
        augmentations_applied = []

        if self.use_pattern_augmentation:
            detected_patterns = self.pattern_matcher.detect_patterns(user_query)

            # Step 2: Generate augmented prompt
            augmented_prompt = self.prompt_generator.generate_augmented_prompt(
                user_query=user_query,
                detected_patterns=detected_patterns,
                top_n=top_patterns
            )

            system_prompt = augmented_prompt.system_prompt
            user_prompt = augmented_prompt.user_prompt
            augmentations_applied = augmented_prompt.augmentation_applied
        else:
            # Use simple prompt without pattern augmentation
            simple_prompt = self.prompt_generator.generate_simple_prompt(user_query)
            system_prompt = simple_prompt.system_prompt
            user_prompt = simple_prompt.user_prompt

        # Step 3: Call fine-tuned model (or base GPT-4.1 if no fine-tuned model available)
        model_to_use = self.finetuned_model_id or "gpt-4.1-2025-04-14"

        try:
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            response_text = response.choices[0].message.content

        except Exception as e:
            # Fallback to base GPT-4.1 if fine-tuned model fails
            if self.finetuned_model_id:
                print(f"⚠️  Fine-tuned model failed, falling back to base GPT-4.1: {e}")
                response = self.client.chat.completions.create(
                    model="gpt-4.1-2025-04-14",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                response_text = response.choices[0].message.content
                model_to_use = "gpt-4.1-2025-04-14 (fallback)"
            else:
                raise

        # Step 4: Return structured response
        return AgentResponse(
            response=response_text,
            detected_patterns=[
                {
                    "pattern": p.pattern_name,
                    "confidence": p.confidence,
                    "signals": p.matched_signals
                }
                for p in detected_patterns[:top_patterns]
            ],
            augmentations_applied=augmentations_applied,
            model_used=model_to_use
        )

    def query_simple(self, user_query: str, **kwargs) -> str:
        """
        Simplified query interface that just returns the response text.

        Args:
            user_query: The user's question
            **kwargs: Additional arguments passed to query()

        Returns:
            The model's response as a string
        """
        agent_response = self.query(user_query, **kwargs)
        return agent_response.response


# Example usage and testing
if __name__ == "__main__":
    import sys

    # Initialize agent
    print("🤖 Initializing Level 1 Agent...")
    agent = Level1Agent(use_pattern_augmentation=True)

    if agent.finetuned_model_id:
        print(f"✅ Using fine-tuned model: {agent.finetuned_model_id}\n")
    else:
        print(f"⚠️  Using base model (no fine-tuned model found)\n")

    # Test queries from different pattern categories
    test_queries = [
        "Should I optimize my sorting algorithm from O(n log n) to O(n)?",
        "Review my plan to migrate from REST to GraphQL",
        "I'm building a rate limiter. What should I consider?",
    ]

    print("=" * 80)
    print("LEVEL 1 AGENT TEST - Pattern-Aware Responses")
    print("=" * 80)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test Query {i}:")
        print(f"{'='*80}")
        print(f"\n❓ {query}\n")

        # Get response with metadata
        response = agent.query(query, temperature=0.7, top_patterns=2)

        # Show detected patterns
        print("📊 Detected Patterns:")
        for pattern_info in response.detected_patterns:
            print(f"   • {pattern_info['pattern']}: {pattern_info['confidence']:.2f}")
            print(f"     Signals: {', '.join(pattern_info['signals'][:2])}")

        # Show applied augmentations
        if response.augmentations_applied:
            print(f"\n🔧 Augmentations Applied:")
            for aug in response.augmentations_applied:
                print(f"   • {aug}")

        # Show response
        print(f"\n💬 Response:\n")
        print(response.response)
        print(f"\n🤖 Model: {response.model_used}")

    print(f"\n{'='*80}\n")

    # Interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        print("\n🎮 Interactive Mode (type 'quit' to exit)\n")

        while True:
            try:
                query = input("\n❓ Your query: ").strip()

                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!\n")
                    break

                if not query:
                    continue

                # Get response
                print("\n💭 Thinking...\n")
                response = agent.query(query)

                # Show patterns
                if response.detected_patterns:
                    print("📊 Patterns:", ", ".join([
                        f"{p['pattern']} ({p['confidence']:.2f})"
                        for p in response.detected_patterns
                    ]))
                    print()

                # Show response
                print("💬 Response:\n")
                print(response.response)
                print()

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
