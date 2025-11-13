"""
Pattern Matcher - Level 1 CRAWL (Milestone 1.2)

Matches user queries to relevant patterns using keyword matching.
Maps directly to: 06_detailed_implementation_roadmap.md - Milestone 1.2
"""

import json
from typing import List, Dict
from pathlib import Path

from src.common.config import Config


class PatternMatcher:
    """
    Matches user queries to relevant patterns using keyword matching.

    This is the core pattern matching engine for Level 1 CRAWL phase.
    It implements simple keyword-based matching to identify which
    learned patterns are relevant to a given query.

    Attributes:
        patterns: Dictionary of all loaded patterns

    Example:
        >>> matcher = PatternMatcher()
        >>> patterns = matcher.match("Implement a cache")
        >>> print([p['name'] for p in patterns])
        ['Production Readiness Checker', 'Tradeoff Analysis First']
    """

    def __init__(self, patterns_file: Path = None):
        """
        Initialize pattern matcher.

        Args:
            patterns_file: Path to patterns.json (defaults to Config.PATTERNS_FILE)
        """
        if patterns_file is None:
            patterns_file = Config.PATTERNS_FILE

        # TODO: Implement pattern loading
        # See: 06_detailed_implementation_roadmap.md - Milestone 1.2
        self.patterns = {}

    def match(self, query: str) -> List[Dict]:
        """
        Return relevant patterns for a given query.

        Args:
            query: User's question/request

        Returns:
            List of pattern dictionaries, sorted by priority

        TODO: Implement keyword matching logic
        See: 06_detailed_implementation_roadmap.md - Milestone 1.2
        """
        # Placeholder implementation
        matched = []
        query_lower = query.lower()

        # TODO: Implement actual matching logic
        # - Check if any trigger keywords match
        # - Always include precision_policing (priority 3)
        # - Sort by priority (lower number = higher priority)

        return matched

    def get_pattern_names(self, patterns: List[Dict]) -> List[str]:
        """Extract pattern names for display."""
        return [p['name'] for p in patterns]

    def _has_keyword_match(self, query: str, keywords: List[str]) -> bool:
        """
        Check if any keyword appears in query.

        TODO: Implement keyword matching
        """
        # Placeholder
        return False


if __name__ == '__main__':
    # Test pattern matcher
    print("Testing PatternMatcher...")
    print("⚠️  This is a placeholder - implement according to Milestone 1.2")
