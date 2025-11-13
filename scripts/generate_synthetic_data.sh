#!/bin/bash
# Generate 200 synthetic conversations (100 from OpenAI, 100 from Gemini)
# 
# Usage: ./scripts/generate_synthetic_data.sh

set -e

echo "🚀 Generating Synthetic Training Data"
echo "======================================"
echo ""

# Check for API keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY not set"
    exit 1
fi

if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ Error: GOOGLE_API_KEY not set"
    exit 1
fi

# Generate from OpenAI (100 examples)
echo "📝 Step 1/2: Generating 100 examples with OpenAI GPT-4o..."
python -m src.level1.run.synthetic_data_generator \
    --provider openai \
    --count 100 \
    --seed 42

echo ""
echo "✅ OpenAI generation complete!"
echo ""

# Generate from Gemini (100 examples)
echo "📝 Step 2/2: Generating 100 examples with Google Gemini 2.5 Pro..."
python -m src.level1.run.synthetic_data_generator \
    --provider gemini \
    --count 100 \
    --seed 42

echo ""
echo "✅ Gemini generation complete!"
echo ""
echo "🎉 All done! Generated 200 synthetic conversations."
echo ""
echo "Output files:"
echo "  - data/synthetic/openai/synthetic_conversations_100_seed42.jsonl"
echo "  - data/synthetic/gemini/synthetic_conversations_100_seed42.jsonl"
echo ""
echo "Next steps:"
echo "  1. Review the generated conversations"
echo "  2. Combine them for fine-tuning (Milestone 1.14)"
echo "  3. Convert to Anthropic fine-tuning format"
