# Self-Evolving Agents

An AI coding assistant that learns your preferences from conversation patterns and evolves its capabilities over time.

## Overview

This project implements a multi-level self-evolving agent system:

- **Level 1**: Pattern-based learning (memory-augmented prompting, few-shot learning, fine-tuning)
- **Level 2**: Architectural self-modification (agent generates tools to automate learned patterns)

## Project Structure

```
self-evolving-agents/
├── docs/                      # Documentation and roadmaps
├── data/                      # Data storage
│   ├── conversations/         # Raw conversation data
│   ├── patterns.json          # Extracted patterns
│   └── training/              # Training data for fine-tuning
├── src/                       # Source code
│   ├── level1/                # Level 1: Pattern-based learning
│   │   ├── crawl/             # Pattern matching & prompting
│   │   ├── walk/              # Few-shot learning
│   │   └── run/               # Fine-tuning
│   ├── level2/                # Level 2: Tool generation
│   │   ├── crawl/             # Tool analysis & generation
│   │   ├── walk/              # Adaptive tool creation
│   │   └── tools/             # Generated tools (version controlled)
│   ├── common/                # Shared utilities
│   └── demo/                  # Streamlit demo apps
├── scripts/                   # Utility scripts
├── examples/                  # Quick start examples
└── tests/                     # Test suite
```

## Quick Start

### 1. Setup

```bash
# Clone the repository
git clone https://github.com/kar-ganap/self-evolving-agents.git
cd self-evolving-agents

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (automatically creates venv and installs everything)
uv sync

# Optional: Install ML dependencies for local fine-tuning (only if you need local training)
# Most users can skip this and use Anthropic's fine-tuning API instead
uv sync --extra ml

# Configure environment
cp .env.example .env
# Edit .env and add your API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY)
```

**Note**: The ML dependencies (PyTorch, transformers) are optional and only needed for local fine-tuning. Most users will use Anthropic's fine-tuning API and don't need these heavy dependencies.

### 2. Choose Your Level

**Level 1 Only** (Recommended for starting):
```bash
# Run Level 1 CRAWL demo (5.5 hours implementation)
uv run streamlit run src/demo/level1_crawl_demo.py
```

**Level 1 + Level 2** (Advanced):
```bash
# Run Level 2 CRAWL demo (9.5 hours implementation)
uv run streamlit run src/demo/level2_crawl_demo.py
```

## Implementation Phases

### Level 1: Pattern-Based Learning

| Phase | Time | Status | Output |
|-------|------|--------|--------|
| **Phase 0** (Learn Patterns) | ~20h | ✅ Complete | Base GPT-4.1 + system prompting (80% adherence) |
| **Phase 1** (Runtime Optimization) | TBD | 📋 Next | DPO training for self-improvement |

**Key Result**: Base GPT-4.1 with pattern-aware system prompting achieves 80% pattern adherence, outperforming fine-tuning.

See: `docs/11_phase0_results.md` for Phase 0 findings

### Level 2: Architectural Self-Modification

| Phase | Time | Output |
|-------|------|--------|
| **CRAWL** | +4h | Auto-generated tools |
| **WALK** | +3h | Adaptive tool creation |
| **RUN** | +0h | Integrated with Level 1 RUN |

See: `docs/07_level2_detailed_roadmap.md`

## Documentation

- `docs/01_extracted_patterns.md` - 10 learned patterns from conversations
- `docs/02_synthetic_conversations.md` - Example conversations demonstrating patterns
- `docs/03_preference_profile.md` - Coding assistant preference profile
- `docs/04_training_implementation_plan.md` - Original training plan
- `docs/05_level2_architectural_changes.md` - Level 2 design document
- `docs/06_detailed_implementation_roadmap.md` - **Level 1 implementation guide**
- `docs/07_level2_detailed_roadmap.md` - **Level 2 implementation guide**

## Key Features

### Level 1: Pattern-Based Learning
- ✅ Extracts patterns from real conversations
- ✅ Applies patterns via prompt engineering
- ✅ Few-shot learning with similar examples
- ✅ Optional fine-tuning for maximum personalization

### Level 2: Architectural Self-Modification
- ✅ Analyzes patterns for automation opportunities
- ✅ Generates Python tools using Claude API
- ✅ Dynamically loads and executes tools
- ✅ Agent's responses incorporate tool analysis
- ✅ Version-controlled tool evolution

## Example Usage

### Level 1 CRAWL
```python
from src.level1.crawl.agent import SelfEvolvingAgent

agent = SelfEvolvingAgent()

# Without patterns
response, _ = agent.respond("Implement a cache", use_patterns=False)

# With patterns (shows tradeoff analysis, production checks, etc.)
response, patterns = agent.respond("Implement a cache", use_patterns=True)
print(f"Applied patterns: {patterns}")
```

### Level 2 CRAWL
```python
from src.level2.crawl.agent_with_tools import SelfEvolvingAgentWithTools

agent = SelfEvolvingAgentWithTools()

code = """
def fibonacci(n):
    return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)
"""

# Agent runs auto-generated tools, then responds
response, metadata = agent.respond(
    "Review this code",
    code=code,
    use_tools=True
)

print(f"Tools executed: {metadata['tools_executed']}")
print(f"Tool results: {metadata['tool_results']}")
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

## Contributing

See implementation roadmaps in `docs/` for detailed plans with go/no-go checkpoints.

## License

[Your License Here]

## Contact

[Your Contact Information]
