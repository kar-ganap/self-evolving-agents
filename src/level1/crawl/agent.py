"""
Self-Evolving Agent - Level 1 CRAWL (Milestone 1.3)

Core agent with pattern-augmented prompting.
Maps directly to: 06_detailed_implementation_roadmap.md - Milestone 1.3
"""

import anthropic
from typing import Optional, Tuple, List
from pathlib import Path

from src.common.config import Config
from src.level1.crawl.pattern_matcher import PatternMatcher


class SelfEvolvingAgent:
    """
    Coding agent that applies learned patterns via prompt augmentation.

    This is the core agent for Level 1 CRAWL phase. It takes user queries,
    matches them to relevant patterns, builds an augmented system prompt,
    and generates responses using Claude API.

    Example:
        >>> agent = SelfEvolvingAgent()
        >>> response, patterns = agent.respond("Implement a cache", use_patterns=True)
        >>> print(f"Applied {len(patterns)} patterns")
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the self-evolving agent.

        Args:
            api_key: Anthropic API key (defaults to Config.ANTHROPIC_API_KEY)

        TODO: Implement initialization
        See: 06_detailed_implementation_roadmap.md - Milestone 1.3
        """
        self.client = anthropic.Anthropic(api_key=api_key or Config.ANTHROPIC_API_KEY)
        self.matcher = PatternMatcher()
        self.model = Config.DEFAULT_MODEL

    def respond(self, query: str, use_patterns: bool = True) -> Tuple[str, List[str]]:
        """
        Generate response with or without learned patterns.

        Args:
            query: User's question
            use_patterns: Whether to apply learned patterns

        Returns:
            Tuple of (response_text, list of applied pattern names)

        TODO: Implement response generation
        See: 06_detailed_implementation_roadmap.md - Milestone 1.3

        Implementation steps:
        1. Match patterns if use_patterns=True
        2. Build system prompt (augmented or base)
        3. Call Claude API
        4. Return response and pattern names
        """
        if use_patterns:
            patterns = self.matcher.match(query)
            system_prompt = self._build_augmented_prompt(patterns)
            pattern_names = self.matcher.get_pattern_names(patterns)
        else:
            system_prompt = "You are a helpful coding assistant."
            patterns = []
            pattern_names = []

        # TODO: Call Claude API
        # message = self.client.messages.create(
        #     model=self.model,
        #     max_tokens=Config.MAX_TOKENS,
        #     system=system_prompt,
        #     messages=[{"role": "user", "content": query}]
        # )

        # Placeholder response
        response_text = "Placeholder response - implement according to Milestone 1.3"

        return response_text, pattern_names

    def _build_augmented_prompt(self, patterns: List) -> str:
        """
        Build system prompt with relevant patterns.

        TODO: Implement prompt building
        See: 06_detailed_implementation_roadmap.md - Milestone 1.3

        Format:
        - Base prompt
        - For each pattern:
          - Pattern name
          - Description
          - Template
          - Example
        - Final instruction
        """
        base = """You are a coding assistant for Kartik, an experienced ML engineer.

You have learned his preferences from analyzing past conversations.
Apply the following patterns when responding:"""

        # TODO: Add pattern sections

        return base


if __name__ == '__main__':
    print("Testing SelfEvolvingAgent...")
    print("⚠️  This is a placeholder - implement according to Milestone 1.3")

    # Example usage (will work once implemented):
    # agent = SelfEvolvingAgent()
    # response, patterns = agent.respond("Implement a rate limiter")
    # print(f"Response: {response[:100]}...")
    # print(f"Patterns applied: {patterns}")
