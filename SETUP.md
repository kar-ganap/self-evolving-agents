# Quick Setup Guide

This project uses `uv` for Python package management.

## Installation

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and setup
git clone https://github.com/kar-ganap/self-evolving-agents.git
cd self-evolving-agents

# 3. Sync dependencies
uv sync

# 4. Configure API keys
cp .env.example .env
# Edit .env and add:
#   OPENAI_API_KEY=your_key
#   GOOGLE_API_KEY=your_key
#   ANTHROPIC_API_KEY=your_key (for agent runtime)
```

## Generate Synthetic Training Data

```bash
# Generate all 200 examples (100 from OpenAI, 100 from Gemini)
./scripts/generate_synthetic_data.sh

# Or generate individually:
uv run python -m src.level1.run.synthetic_data_generator --provider openai --count 100
uv run python -m src.level1.run.synthetic_data_generator --provider gemini --count 100

# Test with small sample:
uv run python -m src.level1.run.synthetic_data_generator --provider openai --count 5
```

## Optional: ML Dependencies

For local fine-tuning (not needed for most users):

```bash
uv sync --extra ml
```

This installs PyTorch, transformers, etc. Skip this if you're using Anthropic's fine-tuning API.

## What's Next?

1. Generate synthetic data (above)
2. Review generated conversations in `data/synthetic/`
3. Continue to Milestone 1.14: Convert to Anthropic format
4. Milestone 1.15: Fine-tune on Anthropic API

See `docs/06_detailed_implementation_roadmap.md` for full plan.
