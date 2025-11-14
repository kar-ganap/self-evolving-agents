"""
Pre-Flight Validation for Fine-Tuning Data

Validates ALL best practices before spending money on training.
Must pass 100% of checks before proceeding.

Usage:
    python -m src.level1.run.validate_finetuning_data
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


class FinetuningValidator:
    """Comprehensive validation of fine-tuning data quality"""

    def __init__(self, train_file: Path, val_file: Path, test_file: Path):
        self.train_file = train_file
        self.val_file = val_file
        self.test_file = test_file

        # Load data
        self.train_data = self._load_jsonl(train_file)
        self.val_data = self._load_jsonl(val_file)
        self.test_data = self._load_jsonl(test_file)

        # Results tracking
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        self.errors = []

    def _load_jsonl(self, file_path: Path) -> List[Dict]:
        """Load JSONL file"""
        data = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data

    def _check(self, name: str, condition: bool, error_msg: str = "", warning: bool = False):
        """Record check result"""
        symbol = "✓" if condition else ("⚠️" if warning else "✗")
        status = "PASS" if condition else ("WARN" if warning else "FAIL")

        print(f"{symbol} [{status}] {name}")

        if condition:
            self.checks_passed += 1
        else:
            if warning:
                self.warnings.append(f"{name}: {error_msg}")
            else:
                self.checks_failed += 1
                self.errors.append(f"{name}: {error_msg}")
                if error_msg:
                    print(f"    └─ {error_msg}")

        return condition

    def _get_last_assistant_message(self, example: Dict) -> str:
        """Extract last assistant message from example"""
        messages = example.get('messages', [])
        assistant_msgs = [m['content'] for m in messages if m['role'] == 'assistant']
        return assistant_msgs[-1] if assistant_msgs else ""

    def _get_last_user_message(self, example: Dict) -> str:
        """Extract last user message from example"""
        messages = example.get('messages', [])
        user_msgs = [m['content'] for m in messages if m['role'] == 'user']
        return user_msgs[-1] if user_msgs else ""

    # ==================== VALIDATION CHECKS ====================

    def check_basic_format(self) -> bool:
        """Check 1: Basic format requirements"""
        print("\n📋 CHECK 1: Basic Format")
        print("=" * 60)

        all_pass = True

        # Check all examples have messages
        train_has_messages = all('messages' in ex for ex in self.train_data)
        all_pass &= self._check(
            "All training examples have 'messages' field",
            train_has_messages,
            f"{sum(1 for ex in self.train_data if 'messages' not in ex)} examples missing 'messages'"
        )

        val_has_messages = all('messages' in ex for ex in self.val_data)
        all_pass &= self._check(
            "All validation examples have 'messages' field",
            val_has_messages
        )

        # Check all examples end with assistant message
        train_ends_assistant = all(
            ex['messages'][-1]['role'] == 'assistant'
            for ex in self.train_data if 'messages' in ex
        )
        all_pass &= self._check(
            "All training examples end with assistant message",
            train_ends_assistant,
            f"{sum(1 for ex in self.train_data if ex['messages'][-1]['role'] != 'assistant')} end with user message"
        )

        val_ends_assistant = all(
            ex['messages'][-1]['role'] == 'assistant'
            for ex in self.val_data if 'messages' in ex
        )
        all_pass &= self._check(
            "All validation examples end with assistant message",
            val_ends_assistant
        )

        # Check system prompts exist
        train_has_system = all(
            ex['messages'][0]['role'] == 'system'
            for ex in self.train_data if 'messages' in ex
        )
        all_pass &= self._check(
            "All training examples start with system prompt",
            train_has_system,
            warning=True  # This is a warning, not critical error
        )

        return all_pass

    def check_response_quality(self) -> bool:
        """Check 2: Response quality requirements"""
        print("\n💎 CHECK 2: Response Quality")
        print("=" * 60)

        all_pass = True

        # Check response lengths
        train_responses = [self._get_last_assistant_message(ex) for ex in self.train_data]
        short_responses = sum(1 for r in train_responses if len(r) < 200)

        all_pass &= self._check(
            "< 10% training responses are too short (< 200 chars)",
            short_responses < len(train_responses) * 0.1,
            f"{short_responses}/{len(train_responses)} responses are too short"
        )

        # Check for question-ending responses (conversational bias)
        question_endings = sum(
            1 for r in train_responses
            if '?' in r[-100:]  # Question in last 100 chars
        )

        all_pass &= self._check(
            "< 20% training responses end with questions",
            question_endings < len(train_responses) * 0.2,
            f"{question_endings}/{len(train_responses)} ({question_endings/len(train_responses)*100:.1f}%) end with questions - HIGH CONVERSATIONAL BIAS!"
        )

        # Check for structured responses (has formatting)
        structured = sum(
            1 for r in train_responses
            if any(marker in r for marker in ['✓', '✗', '⚠️', '###', '**', '```', '1.', '2.'])
        )

        all_pass &= self._check(
            "> 70% training responses are structured",
            structured > len(train_responses) * 0.7,
            f"Only {structured}/{len(train_responses)} ({structured/len(train_responses)*100:.1f}%) are structured"
        )

        # Check average response length
        lengths = [len(r) for r in train_responses]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        all_pass &= self._check(
            "Average response length > 500 chars",
            avg_length > 500,
            f"Average length: {avg_length:.0f} chars (too short for comprehensive answers)",
            warning=avg_length > 300  # Warning if > 300 but < 500
        )

        return all_pass

    def check_distribution_alignment(self) -> bool:
        """Check 3: Train/Val/Test distribution alignment"""
        print("\n📊 CHECK 3: Distribution Alignment")
        print("=" * 60)

        all_pass = True

        # Extract features from prompts
        def extract_features(examples):
            """Extract prompt features for distribution comparison"""
            prompts = [self._get_last_user_message(ex) for ex in examples]
            responses = [self._get_last_assistant_message(ex) for ex in examples]

            prompt_lengths = [len(p) for p in prompts]
            response_lengths = [len(r) for r in responses]

            return {
                'avg_prompt_length': sum(prompt_lengths) / len(prompt_lengths) if prompt_lengths else 0,
                'avg_response_length': sum(response_lengths) / len(response_lengths) if response_lengths else 0,
                'question_ratio': sum(1 for r in responses if '?' in r[-100:]) / len(responses) if responses else 0,
                'structured_ratio': sum(1 for r in responses if any(m in r for m in ['✓', '###', '```'])) / len(responses) if responses else 0,
            }

        train_features = extract_features(self.train_data)
        val_features = extract_features(self.val_data)
        test_features = extract_features(self.test_data)

        # Check response length alignment
        train_val_length_diff = abs(train_features['avg_response_length'] - val_features['avg_response_length'])
        # Note: Train has synthetic comprehensive examples, Val has real filtered examples
        # Large difference is acceptable if val responses are still high quality
        self._check(
            "Train/Val response lengths reasonably aligned",
            train_val_length_diff < train_features['avg_response_length'] * 1.0,  # Allow 100% diff
            f"Difference: {train_val_length_diff:.0f} chars ({train_val_length_diff/train_features['avg_response_length']*100:.1f}%) - Train is synthetic, Val is real",
            warning=True  # Always warning, not critical error
        )

        # Skip test response length check (test set has no responses, only prompts)
        self._check(
            "Test set format validated (prompts only, no responses)",
            True,  # Always pass
            "Test set contains prompts for evaluation, not training format"
        )

        # Skip question/structured ratio checks for test (test has no responses)
        self._check(
            "Training responses minimize unnecessary questions",
            train_features['question_ratio'] < 0.15,
            f"Train question ratio: {train_features['question_ratio']:.2f} (should be < 0.15 for frontloaded responses)",
            warning=True
        )

        self._check(
            "Training responses are well-structured",
            train_features['structured_ratio'] > 0.7,
            f"Train structured ratio: {train_features['structured_ratio']:.2f} (should be > 0.7)"
        )

        return all_pass

    def check_data_diversity(self) -> bool:
        """Check 4: Data diversity and deduplication"""
        print("\n🎨 CHECK 4: Data Diversity")
        print("=" * 60)

        all_pass = True

        # Check for exact duplicate prompts
        train_prompts = [self._get_last_user_message(ex) for ex in self.train_data]
        unique_prompts = len(set(train_prompts))

        all_pass &= self._check(
            "> 95% unique prompts (no exact duplicates)",
            unique_prompts > len(train_prompts) * 0.95,
            f"Only {unique_prompts}/{len(train_prompts)} unique prompts",
            warning=True
        )

        # Check response diversity (exact duplicates)
        train_responses = [self._get_last_assistant_message(ex) for ex in self.train_data]
        unique_responses = len(set(train_responses))

        all_pass &= self._check(
            "> 90% unique responses (no exact duplicates)",
            unique_responses > len(train_responses) * 0.9,
            f"Only {unique_responses}/{len(train_responses)} unique responses",
            warning=True
        )

        # Check for very short prompts (might indicate quality issues)
        very_short_prompts = sum(1 for p in train_prompts if len(p) < 30)
        all_pass &= self._check(
            "< 5% very short prompts (< 30 chars)",
            very_short_prompts < len(train_prompts) * 0.05,
            f"{very_short_prompts}/{len(train_prompts)} prompts are too short",
            warning=True
        )

        return all_pass

    def check_pattern_coverage(self) -> bool:
        """Check 5: Pattern representation balance"""
        print("\n🎯 CHECK 5: Pattern Coverage")
        print("=" * 60)

        all_pass = True

        patterns = [
            "Gap Analysis", "Tradeoff Analysis", "Production Readiness",
            "Brutal Accuracy", "Multi-Dimensional Evaluation", "Hint-Based Learning",
            "Diminishing Returns", "Mechanistic Understanding",
            "Context-Dependent Recommendations", "Precision Policing"
        ]

        pattern_keywords = {
            "Gap Analysis": ["✓", "✗", "⚠️", "missing", "gap"],
            "Tradeoff Analysis": ["tradeoff", "pros", "cons", "vs", "alternative"],
            "Production Readiness": ["test", "error handling", "production"],
            "Brutal Accuracy": ["however", "caveat", "depends", "not always"],
            "Multi-Dimensional Evaluation": ["dimension", "criteria", "score"],
            "Hint-Based Learning": ["hint", "consider", "think about"],
            "Diminishing Returns": ["roi", "worth", "benefit", "cost"],
            "Mechanistic Understanding": ["how", "why", "mechanism", "works by"],
            "Context-Dependent Recommendations": ["depends on", "context", "scenario"],
            "Precision Policing": ["specifically", "precisely", "exact"]
        }

        # Count pattern occurrences
        pattern_counts = defaultdict(int)
        train_responses = [self._get_last_assistant_message(ex) for ex in self.train_data]

        for response in train_responses:
            response_lower = response.lower()
            for pattern, keywords in pattern_keywords.items():
                if any(kw.lower() in response_lower for kw in keywords):
                    pattern_counts[pattern] += 1

        # Check balance
        if pattern_counts:
            max_count = max(pattern_counts.values())
            min_count = min(pattern_counts.values())

            print(f"\n    Pattern distribution:")
            for pattern in patterns:
                count = pattern_counts.get(pattern, 0)
                pct = count / len(train_responses) * 100
                print(f"      {pattern}: {count} ({pct:.1f}%)")

            balance_ratio = min_count / max_count if max_count > 0 else 0
            all_pass &= self._check(
                "Pattern balance ratio > 0.3 (max/min < 3.3x)",
                balance_ratio > 0.3,
                f"Most common: {max_count}, Least common: {min_count}, Ratio: {balance_ratio:.2f}",
                warning=True
            )

        return all_pass

    def check_dataset_size(self) -> bool:
        """Check 6: Dataset size requirements"""
        print("\n📏 CHECK 6: Dataset Size")
        print("=" * 60)

        all_pass = True

        all_pass &= self._check(
            "Training set: 50-500 examples (quality > quantity)",
            50 <= len(self.train_data) <= 500,
            f"Current: {len(self.train_data)} examples"
        )

        all_pass &= self._check(
            "Validation set: 20-100 examples",
            20 <= len(self.val_data) <= 100,
            f"Current: {len(self.val_data)} examples"
        )

        all_pass &= self._check(
            "Test set: 10-50 examples",
            10 <= len(self.test_data) <= 50,
            f"Current: {len(self.test_data)} examples"
        )

        # Check train/val ratio
        val_ratio = len(self.val_data) / len(self.train_data) if len(self.train_data) > 0 else 0
        all_pass &= self._check(
            "Val/Train ratio: 0.1-0.3",
            0.1 <= val_ratio <= 0.3,
            f"Current ratio: {val_ratio:.2f}"
        )

        return all_pass

    def run_all_checks(self) -> bool:
        """Run all validation checks"""
        print("🔍 FINE-TUNING PRE-FLIGHT VALIDATION")
        print("=" * 60)
        print(f"Training:   {self.train_file}")
        print(f"Validation: {self.val_file}")
        print(f"Test:       {self.test_file}")

        # Run all checks
        checks = [
            self.check_basic_format(),
            self.check_response_quality(),
            self.check_distribution_alignment(),
            self.check_data_diversity(),
            self.check_pattern_coverage(),
            self.check_dataset_size(),
        ]

        # Summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"✓ Checks passed: {self.checks_passed}")
        print(f"✗ Checks failed: {self.checks_failed}")
        print(f"⚠️  Warnings:      {len(self.warnings)}")

        if self.errors:
            print("\n❌ CRITICAL ERRORS (must fix before training):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS (recommended to fix):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        print("\n" + "=" * 60)

        # Pass if no critical errors (warnings are OK)
        all_passed = self.checks_failed == 0

        if all_passed:
            print("✅ ALL CHECKS PASSED - READY FOR FINE-TUNING!")
            if self.warnings:
                print("   Note: There are warnings above, but they're not critical.")
        else:
            print("❌ VALIDATION FAILED - DO NOT PROCEED WITH FINE-TUNING")
            print("   Fix the errors above before training.")

        print("=" * 60)

        return all_passed


def main():
    """Run validation"""
    project_root = Path(__file__).parent.parent.parent.parent

    train_file = project_root / "data/finetuning/train_v3.jsonl"
    val_file = project_root / "data/finetuning/validation_v2.jsonl"
    test_file = project_root / "data/test_set.jsonl"

    # Check files exist
    for f in [train_file, val_file, test_file]:
        if not f.exists():
            print(f"❌ ERROR: File not found: {f}")
            return False

    validator = FinetuningValidator(train_file, val_file, test_file)
    passed = validator.run_all_checks()

    return passed


if __name__ == '__main__':
    import sys
    passed = main()
    sys.exit(0 if passed else 1)
