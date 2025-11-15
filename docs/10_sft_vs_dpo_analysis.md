# SFT vs DPO: Training Strategy Analysis

**Document Purpose:** Document the SFT vs DPO decision for Phase 0 and future optimization opportunities.

**Created:** 2025-01-15
**Status:** Reference Document

---

## TL;DR

- **Phase 0 (Current)**: Using **SFT** (Supervised Fine-Tuning)
- **Future Phases**: Consider **DPO** (Direct Preference Optimization) if quality variance is observed
- **Key Insight**: Our source data contains implicit preferences, but we collapsed them into SFT format for simplicity

---

## Background: What We Discovered

### Our Source Data Structure

Real Claude Code conversations follow this pattern:

```
Turn 1: User query
Turn 2: Claude's initial response (missing patterns)
Turn 3: User pushback / correction
Turn 4: Claude's revised response (with patterns applied) ← PREFERRED
```

**Implicit Preference Structure**: Turn 4 > Turn 2 for the same query

### How We Actually Extracted Training Data

We **collapsed the multi-turn interactions into single-turn demonstrations**:

```json
{
  "messages": [
    {"role": "system", "content": "You are a coding assistant..."},
    {"role": "user", "content": "Original query"},
    {"role": "assistant", "content": "Final revised response with patterns"}
  ]
}
```

**What we kept**: Only the final "good" responses
**What we discarded**: Initial attempts that lacked patterns

---

## SFT vs DPO: Key Differences

### Supervised Fine-Tuning (SFT)
**What it does**: Teaches model to produce outputs similar to demonstrations

**Data format**:
```json
{
  "messages": [
    {"role": "user", "content": "How should I version my API?"},
    {"role": "assistant", "content": "Let me analyze this with tradeoffs..."}
  ]
}
```

**Training objective**: Maximize likelihood of producing the demonstrated response

**When to use**:
- Teaching new behaviors from scratch
- Have high-quality demonstration data
- Want model to learn "what good looks like"

**Pros**:
- Simpler to implement (OpenAI API supports it natively)
- Works well with limited data
- Clear training signal

**Cons**:
- Doesn't explicitly learn comparisons between good/bad responses
- May not capture subtle preference distinctions
- Treats all demonstrations equally

### Direct Preference Optimization (DPO)
**What it does**: Teaches model to prefer one output over another

**Data format**:
```json
{
  "prompt": "How should I version my API?",
  "chosen": "Let me analyze this with tradeoffs... [comprehensive analysis]",
  "rejected": "Here are some versioning strategies: URI, headers... [missing patterns]"
}
```

**Training objective**: Increase probability of chosen response relative to rejected response

**When to use**:
- Refining behavior after initial SFT
- Have preference pairs (A > B comparisons)
- Want to distinguish between "good" and "better"

**Pros**:
- Explicitly learns preferences
- More data-efficient (uses both good and bad examples)
- Better at capturing subtle quality differences

**Cons**:
- Requires different infrastructure (not in OpenAI API)
- Needs preference pair data
- More complex to implement (TRL library, custom training)

---

## Why We Chose SFT for Phase 0

### Reason 1: Infrastructure Constraints
- OpenAI Fine-Tuning API uses SFT format
- DPO requires custom training loop (HuggingFace TRL, PyTorch)
- SFT is faster to implement for Phase 0

### Reason 2: Data Availability
- We collapsed multi-turn into single-turn demonstrations
- Would need to restructure data to extract preference pairs
- 201 SFT examples vs ~50 preference pairs (if we extracted)

### Reason 3: Simplicity
- SFT is well-understood and proven
- Lower risk for Phase 0 deliverable
- Can always add DPO later if needed

### Reason 4: Sufficient for Goal
- Goal: Teach model to apply 10 patterns
- SFT is effective for teaching behaviors from demonstrations
- DPO is overkill when we just need "pattern presence" not "style ranking"

---

## What We're Missing by Not Using DPO

### Opportunity Cost

Our source data DOES contain preference information:
- Turn 2 (bad): Response without patterns
- Turn 4 (good): Response with patterns applied

**By using SFT, we're discarding the "bad" examples entirely.**

### Potential Benefits of DPO

If we had extracted preference pairs:

1. **More data-efficient**: 50 preference pairs = 100 examples (good + bad)
2. **Explicit contrast learning**: Model learns "don't do X, do Y instead"
3. **Better at subtle distinctions**: Learns what makes one pattern-rich response better than another

### Cost-Benefit Analysis

**Cost of switching to DPO for Phase 0**:
- Rewrite data extraction (2-4 hours)
- Set up custom training infrastructure (4-8 hours)
- Debug training loop (2-4 hours)
- **Total**: 8-16 hours of additional work

**Benefit**:
- Potentially 10-15% better pattern adherence
- More nuanced style matching

**Verdict**: **Not worth it for Phase 0.** SFT is sufficient.

---

## Future Optimization: When to Consider DPO

### Decision Point: After Phase 0 Validation

Run validation testing with fine-tuned SFT model. If you observe:

**Signals that DPO would help**:
- Model applies patterns inconsistently (e.g., 70% of the time)
- Quality varies significantly between similar queries
- Model produces "technically correct" but stylistically mismatched responses
- You want to refine between "good" and "great"

**Signals that SFT is sufficient**:
- Model applies patterns consistently (>90%)
- Quality is uniformly good
- Any failures are binary (pattern missing vs present)

### How to Implement DPO (Future Phases)

**Step 1: Extract Preference Pairs from Source Data**

Go back to real conversations and extract both versions:

```python
def extract_preference_pairs(conversation):
    """Extract (query, chosen, rejected) from multi-turn conversations"""

    # Find turns where user pushed back on initial response
    for i, turn in enumerate(conversation):
        if turn.role == "user" and "but" in turn.content.lower():
            # Turn i-1 = initial (rejected)
            # Turn i+1 = revised (chosen)
            yield {
                "prompt": conversation[i-2].content,  # Original query
                "rejected": conversation[i-1].content,  # Initial response
                "chosen": conversation[i+1].content     # Revised response
            }
```

**Step 2: Set Up DPO Training Infrastructure**

```python
from trl import DPOTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

trainer = DPOTrainer(
    model=model,
    ref_model=None,  # Reference model (can be same as model initially)
    train_dataset=preference_pairs,
    tokenizer=tokenizer,
    beta=0.1,  # KL divergence coefficient
)

trainer.train()
```

**Step 3: Validate Against SFT Baseline**

Compare DPO-tuned model vs SFT-only model on held-out test set.

---

## Research Summary: Industry Best Practices

### From DPO Paper (Rafailov et al., 2023)

**Key Finding**: "DPO can fine-tune LMs to align with human preferences as well as or better than existing methods"

**Recommended Workflow**:
1. **Stage 1 (SFT)**: Train on demonstrations to learn base capabilities
2. **Stage 2 (DPO)**: Refine with preference data to align style/quality

**Quote**: "DPO eliminates the need for sampling from the LM during fine-tuning or performing significant hyperparameter tuning"

### From HuggingFace TRL Documentation

**When to use SFT**:
- Teaching new tasks from scratch
- Have demonstration data
- Want model to mimic expert behavior

**When to use DPO**:
- After SFT, to refine outputs
- Have preference comparisons
- Want to align with subjective quality criteria

**Typical Pipeline**:
```
Pre-trained Model → SFT (demonstrations) → DPO (preferences) → Production
```

---

## Recommendation for This Project

### Phase 0 (Now): SFT Only

**Deliverable**: Fine-tuned GPT-4o using 201 SFT examples

**Rationale**:
- Simpler, lower risk
- Sufficient for teaching pattern application
- Can iterate if results unsatisfactory

### Phase 2-3 (Future): Evaluate DPO

**Decision Criteria**:

| Metric | SFT Sufficient | Consider DPO |
|--------|---------------|--------------|
| Pattern adherence | >90% | <80% |
| Quality consistency | Low variance | High variance |
| User satisfaction | "Good enough" | "Needs refinement" |
| Implementation cost | N/A | <1 week of work |

**If DPO is warranted**:
1. Extract ~50 preference pairs from source conversations
2. Set up TRL training pipeline
3. Fine-tune on top of SFT model
4. A/B test against SFT baseline

**If SFT is sufficient**:
- Skip DPO entirely
- Focus on other improvements (tool generation, pattern expansion, etc.)

---

## Key Takeaway

**We made the right choice for Phase 0:**
- SFT is simpler and proven
- Our data structure supports it well (demonstration format)
- DPO is an optimization, not a requirement

**We preserve optionality for future:**
- Source data contains preference information
- Can extract preference pairs if needed
- DPO can be layered on top of SFT

**Decision is data-driven:**
- Run Phase 0 validation first
- Only pursue DPO if SFT results show quality variance
- Don't optimize prematurely

---

## References

1. **DPO Paper**: Rafailov et al. (2023) - "Direct Preference Optimization: Your Language Model is Secretly a Reward Model"
   - arXiv: https://arxiv.org/abs/2305.18290

2. **HuggingFace TRL Documentation**: SFT Trainer
   - https://huggingface.co/docs/trl/sft_trainer

3. **OpenAI Fine-Tuning Guide**: Best practices for GPT-4 fine-tuning
   - https://platform.openai.com/docs/guides/fine-tuning

---

## Appendix: Data Format Comparison

### What Our Source Data Looks Like

```
# Real Claude Code Conversation (Markdown)

User: How should I version my REST API?