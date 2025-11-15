"""
Augmented Prompt Generator - Enhances prompts with pattern-specific context

Takes detected patterns and user queries, then injects relevant context to help
the fine-tuned model apply the learned patterns effectively.
"""

from typing import List, Dict
from dataclasses import dataclass

from src.level1.runtime.pattern_matcher import PatternMatch


@dataclass
class AugmentedPrompt:
    """An enhanced prompt ready for the fine-tuned model"""
    system_prompt: str
    user_prompt: str
    detected_patterns: List[PatternMatch]
    augmentation_applied: List[str]  # Which augmentations were added


class PromptGenerator:
    """
    Generates augmented prompts based on detected patterns.

    For each detected pattern, adds specific context that guides the model
    to apply learned behaviors (gap analysis, tradeoff thinking, etc.)
    """

    def __init__(self):
        """Initialize with pattern-specific augmentation templates"""

        # Base system prompt (always included)
        self.base_system_prompt = """You are a coding assistant for Kartik, an experienced ML engineer.

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

        # Pattern-specific augmentations (added when pattern detected)
        self.pattern_augmentations = {
            "Hint-Based Learning": """
For debugging questions, provide strategic hints rather than full solutions. Guide the user through:
- Where to look (specific files, logs, config)
- What to check (common failure modes)
- How to validate hypotheses
- Next debugging steps if initial approach fails""",

            "Diminishing Returns": """
For optimization questions, quantify the ROI before recommending action:
- Current performance baseline
- Expected improvement magnitude
- Engineering effort required (hours/days)
- Complexity added to codebase
- Threshold where effort exceeds benefit""",

            "Multi-Dimensional Evaluation": """
For architectural decisions, evaluate across multiple dimensions:
- Performance implications
- Developer experience impact
- Operational complexity
- Cost considerations
- Team expertise required
- Future flexibility
Provide separate scores for each dimension, not a single recommendation.""",

            "Precision Policing": """
For technical explanations, use exact terms with caveats:
- Define technical terms precisely
- Clarify common misconceptions
- Specify when concepts apply vs don't apply
- Explain edge cases and exceptions
- Avoid oversimplifications that mislead""",

            "Brutal Accuracy": """
For absolute statements, challenge the claim directly:
- Identify oversimplifications
- Provide counterexamples
- Explain context-dependency
- Clarify when the statement IS true vs false
- Cut through buzzwords with technical reality""",

            "Tradeoff Analysis": """
For A vs B questions, compare with structured tradeoffs:
- List pros/cons for each option
- Identify when A is better
- Identify when B is better
- Highlight dealbreakers for each
- Consider hybrid approaches""",

            "Gap Analysis": """
For system design questions, systematically identify gaps using ✓ ⚠️ ✗:
- Security considerations
- Error handling & edge cases
- Performance & scalability
- Monitoring & observability
- Testing strategy
- Operational concerns
- Cost & resource implications""",

            "Production Readiness": """
For code implementation requests, include production-grade elements:
- Type hints for all functions
- Comprehensive error handling
- Input validation
- Logging at appropriate levels
- Unit tests
- Docstrings with examples
- Security considerations""",

            "Mechanistic Understanding": """
For "how does X work" questions, explain the mechanism:
- Step-by-step process flow
- Concrete examples with real data
- Diagrams or pseudocode where helpful
- Common misconceptions to avoid
- Performance implications of the mechanism""",

            "Context-Dependent Recommendations": """
For "what's best" questions, refuse universal answers:
- List key factors that determine the answer
- Ask for missing context if truly needed
- Provide decision matrix
- Give recommendations for different scenarios
- Explain why context matters for this decision"""
        }

    def generate_augmented_prompt(
        self,
        user_query: str,
        detected_patterns: List[PatternMatch],
        top_n: int = 2
    ) -> AugmentedPrompt:
        """
        Generate an augmented prompt based on detected patterns.

        Args:
            user_query: The user's original question
            detected_patterns: Patterns detected by PatternMatcher
            top_n: How many top patterns to use for augmentation

        Returns:
            AugmentedPrompt with enhanced system prompt and user query
        """
        # Start with base system prompt
        system_prompt_parts = [self.base_system_prompt]
        augmentations_applied = []

        # Add pattern-specific augmentations for top N patterns
        top_patterns = detected_patterns[:top_n]

        if top_patterns:
            system_prompt_parts.append("\n**Context for this query:**")

            for pattern in top_patterns:
                if pattern.pattern_name in self.pattern_augmentations:
                    augmentation = self.pattern_augmentations[pattern.pattern_name]
                    system_prompt_parts.append(augmentation)
                    augmentations_applied.append(pattern.pattern_name)

        # Combine into final system prompt
        system_prompt = "\n".join(system_prompt_parts)

        # User prompt stays the same (augmentation is in system prompt)
        user_prompt = user_query

        return AugmentedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            detected_patterns=detected_patterns,
            augmentation_applied=augmentations_applied
        )

    def generate_simple_prompt(self, user_query: str) -> AugmentedPrompt:
        """
        Generate a prompt without pattern detection (uses base prompt only).

        Useful for queries where no patterns are detected or for baseline testing.
        """
        return AugmentedPrompt(
            system_prompt=self.base_system_prompt,
            user_prompt=user_query,
            detected_patterns=[],
            augmentation_applied=[]
        )


# Example usage and testing
if __name__ == "__main__":
    from src.level1.runtime.pattern_matcher import PatternMatcher

    matcher = PatternMatcher()
    generator = PromptGenerator()

    # Test queries
    test_queries = [
        "Should I optimize my algorithm from O(n log n) to O(n)?",
        "Review my plan to use GraphQL instead of REST for our API",
        "I'm building a payment processing system. What should I consider?",
    ]

    print("Augmented Prompt Generation Test:\n")
    print("=" * 80)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 80)

        # Detect patterns
        matches = matcher.detect_patterns(query)

        # Generate augmented prompt
        augmented = generator.generate_augmented_prompt(query, matches, top_n=2)

        print(f"\nDetected Patterns (top 2):")
        for pattern in augmented.detected_patterns[:2]:
            print(f"  - {pattern.pattern_name}: {pattern.confidence:.2f}")

        print(f"\nAugmentations Applied:")
        for aug in augmented.augmentation_applied:
            print(f"  - {aug}")

        print(f"\nSystem Prompt Length: {len(augmented.system_prompt)} chars")
        print(f"User Prompt: {augmented.user_prompt}")
        print()
