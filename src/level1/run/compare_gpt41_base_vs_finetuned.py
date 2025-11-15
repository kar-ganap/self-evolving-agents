"""
Compare Base GPT-4.1 vs Fine-Tuned GPT-4.1

Critical comparison: Does fine-tuning improve over the base model?

Usage:
    python -m src.level1.run.compare_gpt41_base_vs_finetuned
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)


PATTERN_INDICATORS = {
    "Gap Analysis": ["missing", "not addressed", "gap", "✓", "✗", "⚠️", "completeness", "should also"],
    "Tradeoff Analysis": ["tradeoff", "vs", "pros", "cons", "alternative", "option", "consider"],
    "Production Readiness": ["error handling", "edge case", "test", "validation", "production", "logging"],
    "Brutal Accuracy": ["however", "caveat", "depends", "not always", "actually", "misleading"],
    "Multi-Dimensional Evaluation": ["dimension", "aspect", "criteria", "score", "rating"],
    "Hint-Based Learning": ["hint", "consider", "think about", "investigate", "check"],
    "Diminishing Returns": ["diminishing", "roi", "worth", "effort", "benefit", "cost"],
    "Mechanistic Understanding": ["how", "why", "because", "works by", "mechanism", "process"],
    "Context-Dependent Recommendations": ["depends on", "context", "scenario", "situation", "varies"],
    "Precision Policing": ["specifically", "precisely", "exact", "caveat", "condition"]
}


def load_api_key():
    """Load API key from .env"""
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                return line.split('=', 1)[1].split('#')[0].strip()
    raise ValueError("OPENAI_API_KEY not found")


def load_test_set():
    """Load test examples"""
    project_root = Path(__file__).parent.parent.parent.parent
    test_file = project_root / "data/test_set.jsonl"

    examples = []
    with open(test_file, 'r') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    return examples


def score_response_for_patterns(response: str, expected_patterns: list) -> dict:
    """Score a response based on pattern indicators"""
    scores = {}
    response_lower = response.lower()

    for pattern in expected_patterns:
        if pattern in PATTERN_INDICATORS:
            indicators = PATTERN_INDICATORS[pattern]
            matches = sum(1 for ind in indicators if ind.lower() in response_lower)
            score = min(matches / 3.0, 1.0)  # Cap at 1.0, need 3+ indicators for full score
            scores[pattern] = score

    # Overall score
    if scores:
        scores['overall'] = sum(scores.values()) / len(scores)
    else:
        scores['overall'] = 0.0

    return scores


def query_model(client: OpenAI, model: str, prompt: str, system_prompt: str = None) -> str:
    """Query a model and return response"""
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content


def create_system_prompt():
    """System prompt with patterns (same as used in training)"""
    return """You are a coding assistant for Kartik, an experienced ML engineer.

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

Apply these patterns naturally without explicitly mentioning them."""


def main():
    """Main comparison"""
    print("🔬 Model Comparison: Base GPT-4.1 vs Fine-Tuned GPT-4.1")
    print("=" * 80)

    # Load
    api_key = load_api_key()
    client = OpenAI(api_key=api_key)
    test_examples = load_test_set()

    print(f"\n📊 Testing {len(test_examples)} examples")

    # Load fine-tuned model info
    project_root = Path(__file__).parent.parent.parent.parent
    model_info_file = project_root / "data/finetuned_model_info.json"
    with open(model_info_file, 'r') as f:
        model_info = json.loads(f.read())

    fine_tuned_model = model_info['fine_tuned_model']
    base_model = "gpt-4.1-2025-04-14"  # Base GPT-4.1, not GPT-4o!

    system_prompt = create_system_prompt()

    # Results
    results = []
    base_scores = []
    finetuned_scores = []

    print(f"\n🔄 Running comparisons...")
    print(f"   Base model:  {base_model}")
    print(f"   Fine-tuned:  {fine_tuned_model}")
    print()

    for i, example in enumerate(test_examples, 1):
        prompt = example['prompt']
        expected_patterns = example['expected_patterns']

        print(f"[{i}/{len(test_examples)}] {example['category']}: {prompt[:60]}...")

        # Query base GPT-4.1 (with same system prompt)
        print(f"  → Base GPT-4.1...", end='', flush=True)
        base_response = query_model(client, base_model, prompt, system_prompt)
        base_score = score_response_for_patterns(base_response, expected_patterns)
        base_scores.append(base_score['overall'])
        print(f" Score: {base_score['overall']:.2f}")

        # Query fine-tuned GPT-4.1
        print(f"  → Fine-tuned...", end='', flush=True)
        ft_response = query_model(client, fine_tuned_model, prompt, system_prompt)
        ft_score = score_response_for_patterns(ft_response, expected_patterns)
        finetuned_scores.append(ft_score['overall'])
        print(f" Score: {ft_score['overall']:.2f}")

        results.append({
            'test_id': example['id'],
            'prompt': prompt,
            'category': example['category'],
            'expected_patterns': expected_patterns,
            'base_response': base_response,
            'base_score': base_score,
            'finetuned_response': ft_response,
            'finetuned_score': ft_score,
            'improvement': ft_score['overall'] - base_score['overall']
        })

        print()

    # Save results
    output_file = project_root / "data/comparison_gpt41_base_vs_finetuned.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("=" * 80)
    print("📊 COMPARISON RESULTS: GPT-4.1 Base vs Fine-Tuned")
    print("=" * 80)

    avg_base = sum(base_scores) / len(base_scores) if base_scores else 0
    avg_ft = sum(finetuned_scores) / len(finetuned_scores) if finetuned_scores else 0
    improvement = avg_ft - avg_base

    print(f"\nAverage Pattern Adherence Scores:")
    print(f"  Base GPT-4.1 (with system prompt):  {avg_base:.1%}")
    print(f"  Fine-tuned GPT-4.1:                 {avg_ft:.1%}")
    print(f"  Improvement:                        {improvement:+.1%}")

    # Show wins
    base_wins = sum(1 for r in results if r['base_score']['overall'] > r['finetuned_score']['overall'])
    ft_wins = sum(1 for r in results if r['finetuned_score']['overall'] > r['base_score']['overall'])
    ties = len(results) - base_wins - ft_wins

    print(f"\nHead-to-Head:")
    print(f"  Fine-tuned wins: {ft_wins}/{len(results)}")
    print(f"  Base wins:       {base_wins}/{len(results)}")
    print(f"  Ties:            {ties}/{len(results)}")

    print(f"\n💾 Detailed results saved to: {output_file}")

    # Show top improvements
    if results:
        print("\n" + "=" * 80)
        print("📈 TOP 3 IMPROVEMENTS (Fine-Tuned Better)")
        print("=" * 80)

        improvements = sorted([r for r in results if r['improvement'] > 0],
                            key=lambda x: x['improvement'], reverse=True)[:3]

        for i, result in enumerate(improvements, 1):
            print(f"\n{i}. {result['prompt'][:70]}...")
            print(f"   Patterns: {', '.join(result['expected_patterns'])}")
            print(f"   Base: {result['base_score']['overall']:.1%} → Fine-tuned: {result['finetuned_score']['overall']:.1%} ({result['improvement']:+.1%})")

        print("\n" + "=" * 80)
        print("📉 TOP 3 REGRESSIONS (Base Better)")
        print("=" * 80)

        regressions = sorted([r for r in results if r['improvement'] < 0],
                           key=lambda x: x['improvement'])[:3]

        for i, result in enumerate(regressions, 1):
            print(f"\n{i}. {result['prompt'][:70]}...")
            print(f"   Patterns: {', '.join(result['expected_patterns'])}")
            print(f"   Base: {result['base_score']['overall']:.1%} → Fine-tuned: {result['finetuned_score']['overall']:.1%} ({result['improvement']:+.1%})")


if __name__ == '__main__':
    main()
