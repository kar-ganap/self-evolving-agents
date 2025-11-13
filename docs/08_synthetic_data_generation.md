# Synthetic Data Generation Guide (Milestone 1.13)

## Overview

This guide explains how to generate synthetic training data for Level 1 fine-tuning using OpenAI GPT-4o and Google Gemini 2.5 Pro.

## Why Synthetic Data?

We have 19 real conversations showing Kartik's coding style. To fine-tune effectively, we need **100-200 examples**. Synthetic data generation:

1. **Applies learned patterns** to diverse coding topics
2. **Maintains consistency** with established preferences
3. **Ensures even coverage** of all 10 patterns
4. **Reproducible** with random seeding

## Architecture

### Pattern Distribution Strategy

Each synthetic conversation:
- Covers 1 specific coding topic (100 topics available)
- Applies 2-3 specific patterns (evenly distributed)
- Alternates between 2 and 3 patterns per example
- Cycles through all 10 patterns evenly

**Example distribution for 10 conversations:**
```
Conv 1: [Gap Analysis, Tradeoff Analysis]
Conv 2: [Production Readiness, Brutal Accuracy, Multi-Dimensional Evaluation]
Conv 3: [Hint-Based Learning, Diminishing Returns]
Conv 4: [Mechanistic Understanding, Context-Dependent Recommendations, Precision Policing]
Conv 5: [Gap Analysis, Tradeoff Analysis]
...
```

This ensures:
- Each pattern appears ~20 times in 100 examples
- No pattern is over/under-represented
- Reproducible with `--seed 42`

### Reproducibility

All randomness is seeded:
- **Topic selection**: `random.seed(42)` for shuffling topics
- **Pattern assignment**: Deterministic cycling through patterns
- **Output filename**: Includes seed (`synthetic_conversations_100_seed42.jsonl`)

Running the same command twice produces **identical results**.

## Setup

### 1. Install Dependencies

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (installs everything from pyproject.toml)
uv sync
```

This installs:
- `openai>=1.0.0` - OpenAI API client
- `google-genai>=0.1.0` - Google Gemini API client (unified SDK)
- All other project dependencies

### 2. Configure API Keys

Create `.env` file:

```bash
cp .env.example .env
```

Add your API keys:

```env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
```

Get API keys:
- **OpenAI**: https://platform.openai.com/api-keys
- **Google Gemini**: https://aistudio.google.com/app/apikey

## Usage

### Quick Start (Generate All 200 Examples)

```bash
./scripts/generate_synthetic_data.sh
```

This generates:
- 100 examples from OpenAI GPT-4o
- 100 examples from Gemini 2.5 Pro
- Total: 200 synthetic conversations

Output:
```
data/synthetic/openai/synthetic_conversations_100_seed42.jsonl
data/synthetic/gemini/synthetic_conversations_100_seed42.jsonl
```

### Manual Generation

Generate from specific provider:

```bash
# OpenAI (100 examples)
uv run python -m src.level1.run.synthetic_data_generator \
    --provider openai \
    --count 100 \
    --seed 42

# Gemini (100 examples)
uv run python -m src.level1.run.synthetic_data_generator \
    --provider gemini \
    --count 100 \
    --seed 42
```

### Test Run (Small Sample)

Generate 5 examples to test:

```bash
uv run python -m src.level1.run.synthetic_data_generator \
    --provider openai \
    --count 5 \
    --seed 42
```

Output: `data/synthetic/openai/synthetic_conversations_5_seed42.jsonl`

## Output Format

Each line is a JSON object:

```json
{
  "topic": "distributed lock implementation",
  "patterns_applied": ["Tradeoff Analysis", "Production Readiness"],
  "conversation": [
    {"role": "user", "content": "Implement a distributed lock"},
    {"role": "assistant", "content": "Before implementing, let's analyze..."},
    {"role": "user", "content": "How do I handle network partitions?"},
    {"role": "assistant", "content": "Great question. Production considerations..."}
  ],
  "learning_notes": "Applied Tradeoff Analysis by comparing Redis vs etcd vs ZooKeeper..."
}
```

## Quality Control

### What to Check

After generation, review a sample of conversations:

1. **Pattern application**: Are the specified patterns actually used?
2. **Code quality**: Is the code production-ready with error handling?
3. **Naturalness**: Does it feel like a real conversation?
4. **Diversity**: Are topics sufficiently different?
5. **Consistency**: Does it match the preference profile?

### Success Criteria (from Milestone 1.13)

✅ **Go Criteria:**
- 100+ examples generated from each provider
- All 10 patterns represented evenly (~20 times each)
- Conversations are 3-5 exchanges (realistic length)
- JSON parsing succeeds for all examples
- Manual review: 90%+ examples demonstrate patterns correctly

❌ **No-Go Criteria:**
- <80 usable examples (after filtering bad ones)
- Pattern distribution is skewed (>2x variance)
- Most conversations are generic (don't show patterns)

## Next Steps

After generating synthetic data (Milestone 1.13):

1. **Combine datasets** (Milestone 1.14):
   ```bash
   cat data/synthetic/openai/*.jsonl \
       data/synthetic/gemini/*.jsonl \
       > data/synthetic/combined_200.jsonl
   ```

2. **Convert to Anthropic format** (Milestone 1.14):
   - Transform to fine-tuning API format
   - Include system prompts
   - Validate with Anthropic's tool

3. **Fine-tune** (Milestone 1.15):
   - Upload to Anthropic
   - Trigger fine-tuning job
   - Monitor training metrics

## Troubleshooting

### API Rate Limits

If you hit rate limits:

```bash
# Generate in smaller batches
uv run python -m src.level1.run.synthetic_data_generator --provider openai --count 20
uv run python -m src.level1.run.synthetic_data_generator --provider openai --count 20
...
```

The generator saves incrementally, so you won't lose progress.

### JSON Parsing Errors

The generator retries 3 times per example. If an example fails:
- It's logged and skipped
- Generation continues with next topic
- Review logs to see failure reasons

### Pattern Not Applied

If generated conversations don't show patterns:
- Check the prompt template (search for "Patterns to Apply")
- Try adjusting temperature (lower = more faithful to prompt)
- Review examples from both providers (one may be better)

## Cost Estimate

**OpenAI GPT-4o:**
- ~$0.03 per conversation (3,000 tokens avg)
- 100 conversations ≈ **$3.00**

**Google Gemini 2.5 Pro:**
- Free tier: 1,500 requests/day
- 100 conversations ≈ **$0.00** (within free tier)

**Total for 200 conversations: ~$3.00**

## Configuration Reference

### GenerationConfig

| Parameter | Default | Description |
|-----------|---------|-------------|
| `provider` | required | 'openai' or 'gemini' |
| `model` | auto | 'gpt-4o' or 'gemini-2.5-pro' |
| `temperature` | 0.8 | Creativity (0.0-1.0) |
| `max_tokens` | 3000 | Max response length |
| `seed` | 42 | Random seed for reproducibility |

### Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--provider` | choice | required | 'openai' or 'gemini' |
| `--count` | int | 100 | Number of conversations |
| `--output-dir` | path | auto | Output directory |
| `--seed` | int | 42 | Random seed |

## Pattern Definitions

The 10 patterns applied across all conversations:

1. **Gap Analysis**: Systematically identify what's missing (✓ ⚠️ ✗)
2. **Tradeoff Analysis**: Compare alternatives with context
3. **Production Readiness**: Monitoring, error handling, edge cases
4. **Brutal Accuracy**: Challenge logical connections
5. **Multi-Dimensional Evaluation**: Separate scores per dimension
6. **Hint-Based Learning**: Strategic hints, not solutions
7. **Diminishing Returns**: Quantify ROI, identify effort threshold
8. **Mechanistic Understanding**: Explain HOW things work
9. **Context-Dependent Recommendations**: No universal answers
10. **Precision Policing**: Exact technical terms

## Source Files

- Generator: `src/level1/run/synthetic_data_generator.py`
- Runner script: `scripts/generate_synthetic_data.sh`
- Patterns reference: `docs/01_extracted_patterns.md`
- Examples reference: `docs/02_synthetic_conversations.md`
- Preferences reference: `docs/03_preference_profile.md`
