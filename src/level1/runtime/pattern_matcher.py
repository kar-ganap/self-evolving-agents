"""
Pattern Matcher - Detects which of the 10 learned patterns apply to a user query

This component analyzes user queries using keyword matching, semantic patterns,
and linguistic heuristics to determine which patterns should be applied.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
import re


@dataclass
class PatternMatch:
    """Represents a detected pattern with confidence score"""
    pattern_name: str
    confidence: float  # 0.0 to 1.0
    matched_signals: List[str]  # What triggered this pattern


class PatternMatcher:
    """
    Detects patterns in user queries based on learned characteristics.

    Uses keyword matching, question structure, and semantic signals to
    determine which patterns apply with confidence scores.
    """

    def __init__(self):
        """Initialize pattern matchers with keyword sets and heuristics"""

        # Pattern detection rules (keywords, phrases, linguistic patterns)
        self.pattern_rules = {
            "Hint-Based Learning": {
                "keywords": [
                    "help", "debug", "wrong", "error", "issue", "problem",
                    "not working", "fails", "broken", "bug", "what could",
                    "where should i look", "how do i troubleshoot"
                ],
                "question_words": ["what", "where", "how"],
                "weight": 1.0
            },

            "Diminishing Returns": {
                "keywords": [
                    "worth", "should i", "is it worth", "optimize",
                    "improve", "better performance", "faster", "worth the",
                    "necessary", "overkill", "too much"
                ],
                "phrases": [
                    "is it worth",
                    "should i optimize",
                    "worth the effort",
                    "worth implementing"
                ],
                "weight": 1.0
            },

            "Multi-Dimensional Evaluation": {
                "keywords": [
                    "evaluate", "review", "assess", "compare", "analysis",
                    "pros and cons", "tradeoffs", "consider", "decision",
                    "approach"
                ],
                "phrases": [
                    "review my",
                    "evaluate this",
                    "assess my",
                    "what do you think"
                ],
                "weight": 1.0
            },

            "Precision Policing": {
                "keywords": [
                    "explain", "difference", "what is", "how does",
                    "what's the difference", "how do", "definition"
                ],
                "phrases": [
                    "what's the difference between",
                    "difference between",
                    "explain how",
                    "how does",
                    "what is"
                ],
                "weight": 1.0
            },

            "Brutal Accuracy": {
                "keywords": [
                    "always", "never", "best practice", "right",
                    "correct", "true", "agree", "better than",
                    "superior", "guarantees"
                ],
                "phrases": [
                    "is always",
                    "always better",
                    "never use",
                    "best practice"
                ],
                "indicators": [
                    "ending_with_question_confirmation"  # "Right?", "Agree?", etc.
                ],
                "weight": 1.0
            },

            "Tradeoff Analysis": {
                "keywords": [
                    "vs", "versus", "or", "which", "choose", "better",
                    "comparison", "alternative", "options"
                ],
                "phrases": [
                    " vs ",
                    " or ",
                    "which should i",
                    "should i use"
                ],
                "indicators": [
                    "contains_vs_comparison"
                ],
                "weight": 1.0
            },

            "Gap Analysis": {
                "keywords": [
                    "building", "planning", "designing", "creating",
                    "missing", "overlooking", "consider", "gaps",
                    "what should i", "what am i missing"
                ],
                "phrases": [
                    "what should i consider",
                    "what am i missing",
                    "what gaps",
                    "i'm building"
                ],
                "weight": 1.0
            },

            "Production Readiness": {
                "keywords": [
                    "write", "create", "implement", "build a function",
                    "endpoint", "api", "production", "robust",
                    "handle errors", "logging"
                ],
                "phrases": [
                    "write a",
                    "create a",
                    "implement a",
                    "build a function"
                ],
                "indicators": [
                    "requests_code_implementation"
                ],
                "weight": 1.0
            },

            "Mechanistic Understanding": {
                "keywords": [
                    "how does", "explain how", "why does", "mechanism",
                    "works", "internally", "under the hood", "process"
                ],
                "phrases": [
                    "how does",
                    "explain how",
                    "how do",
                    "why does"
                ],
                "weight": 1.0
            },

            "Context-Dependent Recommendations": {
                "keywords": [
                    "best", "should i use", "which is better",
                    "recommend", "what's the best", "for my",
                    "in my case"
                ],
                "phrases": [
                    "what's the best",
                    "which is best",
                    "should i use",
                    "for my application"
                ],
                "indicators": [
                    "asks_for_recommendation_without_context"
                ],
                "weight": 1.0
            }
        }

    def detect_patterns(self, query: str) -> List[PatternMatch]:
        """
        Analyze a query and return detected patterns with confidence scores.

        Args:
            query: User's question or request

        Returns:
            List of PatternMatch objects sorted by confidence (highest first)
        """
        query_lower = query.lower()
        matches: List[PatternMatch] = []

        for pattern_name, rules in self.pattern_rules.items():
            confidence, signals = self._calculate_pattern_confidence(
                query_lower, query, rules
            )

            if confidence > 0.0:
                matches.append(PatternMatch(
                    pattern_name=pattern_name,
                    confidence=confidence,
                    matched_signals=signals
                ))

        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches

    def _calculate_pattern_confidence(
        self,
        query_lower: str,
        query_original: str,
        rules: Dict
    ) -> Tuple[float, List[str]]:
        """
        Calculate confidence score for a single pattern.

        Returns:
            Tuple of (confidence_score, matched_signals)
        """
        signals = []
        score = 0.0

        # Check keywords (partial matching, each adds to score)
        keyword_matches = 0
        for keyword in rules.get("keywords", []):
            if keyword in query_lower:
                keyword_matches += 1
                signals.append(f"keyword: {keyword}")

        if keyword_matches > 0:
            # Normalize: 1 keyword = 0.3, 2 = 0.5, 3+ = 0.7
            score += min(0.3 + (keyword_matches - 1) * 0.2, 0.7)

        # Check phrases (exact matching, stronger signal)
        for phrase in rules.get("phrases", []):
            if phrase in query_lower:
                score += 0.4
                signals.append(f"phrase: {phrase}")

        # Check question words
        for qword in rules.get("question_words", []):
            if query_lower.startswith(qword):
                score += 0.2
                signals.append(f"question_word: {qword}")

        # Check special indicators
        for indicator in rules.get("indicators", []):
            if self._check_indicator(indicator, query_lower, query_original):
                score += 0.3
                signals.append(f"indicator: {indicator}")

        # Cap at 1.0 and apply pattern weight
        confidence = min(score * rules["weight"], 1.0)

        return confidence, signals

    def _check_indicator(self, indicator: str, query_lower: str, query_original: str) -> bool:
        """Check special linguistic indicators"""

        if indicator == "ending_with_question_confirmation":
            # Ends with "Right?", "Agree?", "True?", "Correct?", "Yes?"
            return bool(re.search(r'\b(right|agree|true|correct|yes)\?$', query_lower))

        elif indicator == "contains_vs_comparison":
            # Contains "X vs Y" or "X or Y" pattern
            return bool(re.search(r'\w+\s+(vs|versus|or)\s+\w+', query_lower))

        elif indicator == "requests_code_implementation":
            # Starts with imperative verb
            imperative_verbs = ["write", "create", "implement", "build", "make", "develop"]
            return any(query_lower.startswith(verb) for verb in imperative_verbs)

        elif indicator == "asks_for_recommendation_without_context":
            # Asks "what's best" or "which should I" without specifics
            has_best_question = bool(re.search(r"what'?s\s+the\s+best|which\s+is\s+best", query_lower))
            lacks_specifics = len(query_lower.split()) < 15  # Short, vague question
            return has_best_question and lacks_specifics

        return False

    def get_top_pattern(self, query: str) -> PatternMatch | None:
        """Get the single highest-confidence pattern for a query"""
        matches = self.detect_patterns(query)
        return matches[0] if matches else None

    def get_patterns_above_threshold(
        self,
        query: str,
        threshold: float = 0.5
    ) -> List[PatternMatch]:
        """Get all patterns with confidence above threshold"""
        matches = self.detect_patterns(query)
        return [m for m in matches if m.confidence >= threshold]


# Example usage and testing
if __name__ == "__main__":
    matcher = PatternMatcher()

    # Test queries from each pattern
    test_queries = [
        "My API is returning 500 errors intermittently. What could be wrong?",
        "Should I optimize my algorithm from O(n log n) to O(n)?",
        "Review my plan to use GraphQL instead of REST for our API",
        "How do closures work in JavaScript?",
        "NoSQL is faster than SQL, so we should always use it. Agree?",
        "Should I use React or Vue for my new project?",
        "I'm building a payment processing system. What should I consider?",
        "Write a function to handle file uploads",
        "Explain how HTTPS encryption works",
        "What's the best database for my application?"
    ]

    print("Pattern Detection Test Results:\n")
    print("=" * 80)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 80)

        matches = matcher.detect_patterns(query)

        if matches:
            for match in matches[:3]:  # Show top 3
                print(f"  {match.pattern_name}: {match.confidence:.2f}")
                print(f"    Signals: {', '.join(match.matched_signals[:3])}")
        else:
            print("  No patterns detected")

        print()
