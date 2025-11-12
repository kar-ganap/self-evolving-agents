# Self-Evolving Agent Training Implementation Plan

## Document Purpose
Phased approach to building a self-evolving coding agent that learns from user interaction patterns. Each phase builds on the previous, from hackathon-ready MVP to production-grade fine-tuned system.

---

## Overview: Three-Phase Approach

| Phase | Approach | Time Required | Risk | Demo Quality | Production Ready |
|-------|----------|---------------|------|--------------|------------------|
| **CRAWL** | Memory-Augmented Prompting | 5-6 hours | Low | High | Medium |
| **WALK** | + Few-Shot Learning | 8-12 hours | Medium | Very High | High |
| **RUN** | + Fine-Tuning | 3-5 days | High | Exceptional | Very High |

---

# PHASE 1: CRAWL - Memory-Augmented Prompting

## Goal
Build pattern-based prompt engineering system that applies learned preferences without any ML training.

## Timeline: 5.5 Hours (Hackathon-Ready)

### What You're Building

```
User Query → Pattern Matcher → Augmented Prompt → Claude API → Response
                      ↓
              Pattern Database
           (Your 10 learned patterns)
```

**Key Insight:** This isn't "training" in the ML sense—it's extracting patterns and encoding them as structured prompt engineering.

---

## Hour 1: Data Structure & Pattern Extraction

### Task: Convert Markdown Conversations to Structured Patterns

**Input:** Your 3 markdown files (extracted patterns, synthetic conversations, preference profile)

**Output:** Structured JSON pattern database

```python
# patterns_extractor.py
import json

def create_pattern_database():
    """
    Convert your markdown documentation into structured patterns.
    """
    
    patterns = {
        "production_readiness": {
            "name": "Production Readiness Checker",
            "trigger_keywords": ["implement", "build", "create", "code", "write"],
            "priority": 1,
            "description": """When providing code implementations, ALWAYS include:
- Error handling for edge cases
- Unit tests with examples
- Type hints (Python) or strong typing
- Docstrings with complexity analysis
- Edge cases explicitly listed""",
            
            "example": """
# Good example:
def rate_limiter(max_requests: int, window: int) -> bool:
    '''
    Token bucket rate limiter.
    
    Time: O(1), Space: O(n) where n = number of users
    
    Edge cases:
    - First request from new user
    - Concurrent requests (use atomic Redis ops)
    - Clock skew (use monotonic time)
    '''
    # Implementation with error handling
    try:
        # ... code ...
    except RedisError as e:
        logger.error(f"Rate limiter failed: {e}")
        return True  # Fail open for availability
    
# Tests included below
def test_rate_limiter():
    assert rate_limiter(10, 60) == True  # First request
    # ... more tests
""",
            "template": """
Before providing the implementation, I should:
1. Ask about scale/requirements
2. Present tradeoff analysis
3. Implement with full production readiness
4. Include tests and documentation
"""
        },
        
        "tradeoff_analysis": {
            "name": "Tradeoff Analysis First",
            "trigger_keywords": ["implement", "should we", "which", "versus", "vs"],
            "priority": 1,
            "description": """Before recommending a solution, ALWAYS present alternatives with:
- Pros/cons for each option
- Best use case for each
- What you sacrifice with each choice
- Context-specific recommendation with reasoning""",
            
            "example": """
# Good example:
User: "Should we use Redis or Memcached?"

Response structure:
**Redis:**
- ✓ Rich data types, persistence, pub/sub
- ✗ Single-threaded (write bottleneck)
- ✗ More memory overhead
- Best for: Complex data, persistence needs, pub/sub

**Memcached:**
- ✓ Multi-threaded, less memory
- ✗ Only key-value, no persistence
- ✗ Limited data structures
- Best for: Simple caching, high concurrency

**For your use case (high-volume session storage):**
Recommend Memcached for simple KV + memory efficiency.
If you need persistence or complex types later, Redis.""",
            
            "template": """
When presenting architectural decisions:
1. List 2-4 alternatives
2. Pros/cons for each
3. Best scenario for each
4. Specific recommendation tied to user's context
"""
        },
        
        "hint_based_debugging": {
            "name": "Hint-Based Debugging",
            "trigger_keywords": ["debug", "fix", "bug", "error", "not working", "help me solve"],
            "priority": 2,
            "description": """For debugging requests, NEVER give the solution directly. Instead:
- Ask guiding questions
- Provide strategic hints
- Suggest concrete test cases to trace
- Point to suspicious areas without revealing the fix""",
            
            "example": """
# Good example:
User: "This binary search isn't working: [buggy code]"

Response:
I'll help you find the bug yourself:

**Questions to consider:**
1. What value does `mid` have when searching [1,2,3] for target=3?
2. When does the loop terminate?
3. Trace this case manually: arr=[1], target=1

**Specific area to examine:**
Look at line 5: `right = mid`. What happens if target is at `mid`?

Does this help you spot it? Let me know if you want another hint!

[After user tries]
Good progress! You fixed the infinite loop. However, there's still an edge case...
""",
            
            "template": """
Debugging response structure:
1. Guiding questions (not answers)
2. Concrete test case to trace
3. Point to suspicious area (not the fix)
4. Acknowledge progress + introduce next issue
"""
        },
        
        "gap_analysis": {
            "name": "Gap Analysis & Completeness",
            "trigger_keywords": ["review", "assess", "evaluate", "analyze", "check"],
            "priority": 1,
            "description": """For reviews/assessments, use systematic scoring and EXPLICITLY identify gaps:
- Use ✓ ⚠️ ✗ scoring system
- State what's MISSING, not just what's present
- Multi-dimensional evaluation
- Context-dependent recommendations""",
            
            "example": """
# Good example:
**Functionality: 8/10**
- ✓ Core logic correct
- ✓ Handles main use cases
- ⚠️ Edge case: empty input not handled

**Production Readiness: 4/10**
- ✗ No unit tests
- ✗ No error handling for network failures
- ✗ No logging for debugging
- ✓ Clear function signatures
- ✗ No monitoring hooks

**Missing:**
- Tests (unit, integration)
- Error recovery strategy
- Performance benchmarks
- Documentation beyond inline comments

**Recommendation:**
For production: Add items marked ✗ before deploying
For prototype: Current state is acceptable
""",
            
            "template": """
Review structure:
1. Multi-dimensional scores
2. What's present (✓)
3. What's missing (✗)
4. Context-specific recommendations
"""
        },
        
        "precision_policing": {
            "name": "Precision Policing",
            "trigger_keywords": ["thread-safe", "scales", "distributed", "always", "never", "guaranteed"],
            "priority": 3,  # Always apply
            "description": """Be PRECISE in all technical claims. Add caveats and qualifications:
- Don't say "thread-safe" without conditions
- Don't say "scales horizontally" without clarification
- Don't say "ML-based" when it's rule-based
- Always note limitations and edge cases""",
            
            "example": """
# Bad:
"This is thread-safe because it uses Redis"
"Scales horizontally across servers"
"This solution is optimal"

# Good:
"Redis INCR is atomic for a single instance. For distributed thread-safety, use Lua scripts or WATCH/MULTI/EXEC."

"Scales reads horizontally via replicas. Writes are limited by single-master bottleneck. For write scaling, use Redis Cluster (partitioning)."

"This is optimal for the stated constraints (O(n log n) with O(1) space). If memory is unlimited, O(n) solutions exist with O(n) space."
""",
            
            "template": """
When making technical claims:
1. State the claim
2. Add the conditions/context where it holds
3. Note limitations or exceptions
4. Provide alternatives if relevant
"""
        },
        
        "multi_dimensional_evaluation": {
            "name": "Multi-Dimensional Evaluation",
            "trigger_keywords": ["compare", "better", "choose", "decide", "which"],
            "priority": 2,
            "description": """Never give single-dimensional evaluations. Break down into multiple criteria with context-dependent conclusions.""",
            
            "example": """
# Good example:
**Technical Complexity: A=9/10, B=6/10**
- A has more sophisticated algorithms
- B is simpler but sufficient

**Production Readiness: A=5/10, B=9/10**
- A lacks tests and monitoring
- B has comprehensive testing

**For research paper: Choose A** (complexity valued)
**For production system: Choose B** (reliability critical)
""",
            
            "template": """
1. Multiple evaluation dimensions
2. Separate scores per dimension
3. Context-dependent recommendation
4. Explain why context matters
"""
        },
        
        "mechanistic_understanding": {
            "name": "Mechanistic Explanation",
            "trigger_keywords": ["explain", "how does", "why", "understand", "help me learn"],
            "priority": 2,
            "description": """For explanations, provide mechanistic understanding with concrete examples:
- Context & motivation first
- Step-by-step breakdown
- Trace execution with specific values
- Compare to alternatives""",
            
            "example": """
# Good example:
**CONTEXT:** We need O(1) lookup for LRU cache eviction

**KEY IDEA:** HashMap for O(1) access + Doubly-Linked List for O(1) reordering

**STEP-BY-STEP:**
1. HashMap stores {key → node_pointer}
2. Node contains {key, value, prev, next}
3. On access: Move node to head (most recent)
4. On eviction: Remove tail (least recent)

**EXAMPLE TRACE:**
Capacity=3, operations: put(1,'a'), put(2,'b'), get(1)
After put(1): [1] (head=1, tail=1)
After put(2): [2,1] (head=2, tail=1)
After get(1): [1,2] (1 moved to head)

**WHY CLEVER:**
Array-only: O(n) to find least recent
This approach: O(1) for all operations
Tradeoff: More complex implementation
""",
            
            "template": """
Explanation structure:
1. Context/motivation
2. High-level idea
3. Step-by-step mechanics
4. Concrete trace with values
5. Comparison to alternatives
6. Tradeoff analysis
"""
        },
        
        "diminishing_returns": {
            "name": "Diminishing Returns Analysis",
            "trigger_keywords": ["should i add", "worth it", "time left", "polish", "more features"],
            "priority": 2,
            "description": """Think in terms of marginal utility. Quantify ROI for each option.""",
            
            "example": """
# Good example:
**Option A: Polish existing features**
- Time: 4 hours
- Value boost: 30% (demo quality)
- Risk: Low
- ROI: 7.5% per hour

**Option B: Add new feature**
- Time: 6 hours
- Value boost: 15% (marginal improvement)
- Risk: High (could break existing)
- ROI: 2.5% per hour

**Recommendation:** Polish. Diminishing returns on new features.
You're at 85% feature complete—focus on the 60% → 90% polish gap.
""",
            
            "template": """
1. Quantify time investment
2. Estimate value/impact
3. Factor in risk
4. Calculate ROI
5. Identify point of diminishing returns
"""
        },
        
        "challenging_logic": {
            "name": "Challenge Logical Connections",
            "trigger_keywords": [],  # Applied reactively when detecting non-sequiturs
            "priority": 3,
            "description": """When claims don't directly address the problem, call it out:
- Identify when A doesn't actually solve B
- Separate orthogonal concerns
- Ask for missing logical connection""",
            
            "example": """
# Good example:
Claim: "Use microservices because they're modern"
Response: "How does 'modern' address your specific problem? 
What's the connection between architecture age and solving your deployment bottleneck?"

Claim: "Feature X is valuable" (when discussing security concern Y)
Response: "Value doesn't address security. These are orthogonal. 
Either X's value outweighs Y's risk, OR you have a solution for Y. Which is it?"
""",
            
            "template": """
When detecting non-sequiturs:
1. Identify the claim
2. Identify the problem
3. Call out the missing connection
4. Ask for clarification
"""
        },
        
        "brutal_accuracy": {
            "name": "Brutal Accuracy",
            "trigger_keywords": [],  # Applied when complexity can be reduced
            "priority": 3,
            "description": """Strip away complexity to reveal core truth. Cut through BS.""",
            
            "example": """
# Good examples:
Long discussion about fine-tuning strategies →
"So we need good prompt engineering?"

Complex microservices architecture →
"So we need a queue and a database?"

Elaborate ML pipeline →
"So we're showing people things similar users liked?"
""",
            
            "template": """
After complex explanation:
"So essentially, [simple core truth]?"
"""
        }
    }
    
    return patterns

# Save to JSON
patterns = create_pattern_database()
with open('patterns.json', 'w') as f:
    json.dump(patterns, f, indent=2)

print(f"Created {len(patterns)} patterns")
```

**Deliverable:** `patterns.json` with all 10 patterns structured

---

## Hour 2: Pattern Matching Engine

### Task: Build keyword-based pattern retrieval

```python
# pattern_matcher.py
import json
from typing import List, Dict

class PatternMatcher:
    """
    Matches user queries to relevant patterns using keyword matching.
    """
    
    def __init__(self, patterns_file='patterns.json'):
        with open(patterns_file, 'r') as f:
            self.patterns = json.load(f)
    
    def match(self, query: str) -> List[Dict]:
        """
        Return relevant patterns for a given query.
        
        Args:
            query: User's question/request
            
        Returns:
            List of pattern dictionaries, sorted by priority
        """
        matched = []
        query_lower = query.lower()
        
        for pattern_key, pattern_data in self.patterns.items():
            # Check if any trigger keywords match
            if self._has_keyword_match(query_lower, pattern_data['trigger_keywords']):
                matched.append(pattern_data)
        
        # Always include precision_policing (priority 3)
        precision = self.patterns.get('precision_policing')
        if precision and precision not in matched:
            matched.append(precision)
        
        # Sort by priority (lower number = higher priority)
        matched.sort(key=lambda p: p['priority'])
        
        return matched
    
    def _has_keyword_match(self, query: str, keywords: List[str]) -> bool:
        """Check if any keyword appears in query."""
        return any(keyword in query for keyword in keywords)
    
    def get_pattern_names(self, patterns: List[Dict]) -> List[str]:
        """Extract pattern names for display."""
        return [p['name'] for p in patterns]

# Test
if __name__ == '__main__':
    matcher = PatternMatcher()
    
    test_queries = [
        "Implement a rate limiter for our API",
        "Review this code and tell me what's wrong",
        "Help me debug this binary search",
        "Should we use PostgreSQL or MongoDB?"
    ]
    
    for query in test_queries:
        patterns = matcher.match(query)
        names = matcher.get_pattern_names(patterns)
        print(f"\nQuery: {query}")
        print(f"Matched patterns: {', '.join(names)}")
```

**Deliverable:** `pattern_matcher.py` with keyword-based matching

---

## Hour 3: Prompt Builder & Agent Core

### Task: Build augmented prompt system

```python
# agent.py
import anthropic
from pattern_matcher import PatternMatcher
from typing import Optional

class SelfEvolvingAgent:
    """
    Coding agent that applies learned patterns via prompt augmentation.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.matcher = PatternMatcher()
        self.model = "claude-sonnet-4-5-20250929"
    
    def respond(self, query: str, use_patterns: bool = True) -> tuple[str, list]:
        """
        Generate response with or without learned patterns.
        
        Args:
            query: User's question
            use_patterns: Whether to apply learned patterns
            
        Returns:
            (response_text, applied_patterns)
        """
        if use_patterns:
            patterns = self.matcher.match(query)
            system_prompt = self._build_augmented_prompt(patterns)
            pattern_names = self.matcher.get_pattern_names(patterns)
        else:
            system_prompt = "You are a helpful coding assistant."
            patterns = []
            pattern_names = []
        
        # Call Claude API
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": query}]
        )
        
        response_text = message.content[0].text
        return response_text, pattern_names
    
    def _build_augmented_prompt(self, patterns: list) -> str:
        """
        Build system prompt with relevant patterns.
        """
        base = """You are a coding assistant for Kartik, an experienced ML engineer.

You have learned his preferences from analyzing past conversations.
Apply the following patterns when responding:"""
        
        pattern_sections = []
        for i, pattern in enumerate(patterns, 1):
            section = f"""
## Pattern {i}: {pattern['name']}

{pattern['description']}

Template to follow:
{pattern['template']}

Example:
{pattern['example']}
"""
            pattern_sections.append(section)
        
        full_prompt = base + "\n" + "\n---\n".join(pattern_sections)
        
        # Add final instruction
        full_prompt += "\n\nApply these patterns naturally. Don't mention the patterns explicitly."
        
        return full_prompt

# Quick test
if __name__ == '__main__':
    agent = SelfEvolvingAgent()
    
    query = "Implement a rate limiter"
    
    print("=== WITHOUT PATTERNS ===")
    response_base, _ = agent.respond(query, use_patterns=False)
    print(response_base[:500] + "...")
    
    print("\n=== WITH PATTERNS ===")
    response_learned, patterns = agent.respond(query, use_patterns=True)
    print(f"Applied patterns: {', '.join(patterns)}")
    print(response_learned[:500] + "...")
```

**Deliverable:** `agent.py` - Core agent with pattern augmentation

---

## Hour 4: Demo Interface

### Task: Build Streamlit demo UI

```python
# demo.py
import streamlit as st
from agent import SelfEvolvingAgent
import json

st.set_page_config(page_title="Self-Evolving Coding Agent", layout="wide")

# Initialize agent
@st.cache_resource
def get_agent():
    return SelfEvolvingAgent()

agent = get_agent()

# Load patterns for display
with open('patterns.json', 'r') as f:
    all_patterns = json.load(f)

# Sidebar: Show learned patterns
st.sidebar.title("🧠 Learned Patterns")
st.sidebar.write("**From 19 conversations:**")
for pattern_key, pattern_data in all_patterns.items():
    with st.sidebar.expander(f"✓ {pattern_data['name']}"):
        st.write(pattern_data['description'][:200] + "...")

# Main UI
st.title("🤖 Self-Evolving Coding Agent")
st.write("An agent that learns your coding preferences from conversation patterns")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["Before/After Comparison", "Interactive Demo", "Pattern Analysis"])

# Pre-defined test queries
test_queries = {
    "Rate Limiter": "Implement a rate limiter for our API",
    "Code Review": "Review this code:\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```",
    "Debugging": "Help me debug this binary search - it's not finding elements:\n```python\ndef binary_search(arr, target):\n    left, right = 0, len(arr)\n    while left < right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid\n        else:\n            right = mid\n    return -1\n```",
    "Architecture": "Should we use microservices or a monolith for our startup?",
}

with tab1:
    st.header("Before Learning vs After Learning")
    st.write("See how the agent responds before and after learning your patterns")
    
    selected_query = st.selectbox("Choose a test query:", list(test_queries.keys()))
    query = test_queries[selected_query]
    
    st.text_area("Query:", query, height=150, disabled=True)
    
    if st.button("Generate Comparison", key="compare"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("❌ Before Learning")
            st.caption("Generic coding assistant")
            with st.spinner("Generating..."):
                response_before, _ = agent.respond(query, use_patterns=False)
            st.markdown(response_before)
        
        with col2:
            st.subheader("✅ After Learning")
            st.caption("With your learned patterns")
            with st.spinner("Generating..."):
                response_after, patterns = agent.respond(query, use_patterns=True)
            
            st.info(f"**Patterns applied:** {', '.join(patterns)}")
            st.markdown(response_after)

with tab2:
    st.header("Interactive Demo")
    st.write("Ask your own questions and see pattern application")
    
    custom_query = st.text_area(
        "Enter your coding question:",
        height=100,
        placeholder="e.g., Implement a distributed cache, Review my API design, etc."
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        use_patterns = st.checkbox("Apply learned patterns", value=True)
    
    if st.button("Get Response", key="interactive"):
        if custom_query:
            with st.spinner("Thinking..."):
                response, patterns = agent.respond(custom_query, use_patterns=use_patterns)
            
            if use_patterns:
                st.success(f"**Patterns applied:** {', '.join(patterns)}")
            
            st.markdown("### Response:")
            st.markdown(response)
        else:
            st.warning("Please enter a question")

with tab3:
    st.header("Pattern Analysis")
    st.write("Explore the patterns learned from your conversations")
    
    pattern_to_view = st.selectbox(
        "Select a pattern to examine:",
        list(all_patterns.keys()),
        format_func=lambda x: all_patterns[x]['name']
    )
    
    pattern = all_patterns[pattern_to_view]
    
    st.subheader(f"📋 {pattern['name']}")
    
    st.markdown("**Description:**")
    st.info(pattern['description'])
    
    st.markdown("**Trigger Keywords:**")
    st.code(", ".join(pattern['trigger_keywords']))
    
    st.markdown("**Template:**")
    st.code(pattern['template'])
    
    st.markdown("**Example:**")
    st.code(pattern['example'], language='python')

# Footer
st.markdown("---")
st.caption("Built for Self-Evolving Agents Hackathon | Phase 1: Memory-Augmented Prompting")
```

**Deliverable:** `demo.py` - Interactive Streamlit demo

---

## Hour 5: Testing & Polish

### Task: Test all functionality and polish demo

**Testing checklist:**
```python
# test_agent.py
import pytest
from agent import SelfEvolvingAgent
from pattern_matcher import PatternMatcher

def test_pattern_matching():
    matcher = PatternMatcher()
    
    # Test implementation query
    patterns = matcher.match("Implement a cache")
    names = matcher.get_pattern_names(patterns)
    assert "Production Readiness Checker" in names
    assert "Tradeoff Analysis First" in names
    
    # Test debug query
    patterns = matcher.match("Help me debug this code")
    names = matcher.get_pattern_names(patterns)
    assert "Hint-Based Debugging" in names
    
    # Test review query
    patterns = matcher.match("Review my code")
    names = matcher.get_pattern_names(patterns)
    assert "Gap Analysis & Completeness" in names

def test_agent_response():
    agent = SelfEvolvingAgent()
    
    # Test with patterns
    response, patterns = agent.respond("Implement a rate limiter", use_patterns=True)
    assert len(response) > 100
    assert len(patterns) > 0
    
    # Test without patterns
    response_base, patterns_base = agent.respond("Implement a rate limiter", use_patterns=False)
    assert len(response_base) > 100
    assert len(patterns_base) == 0

if __name__ == '__main__':
    pytest.main([__file__])
```

**Polish tasks:**
- Run demo with 5 test queries
- Check pattern matching accuracy
- Verify Claude API responses
- Test edge cases
- Screenshot key screens

---

## Hour 5.5: Documentation & Demo Video

### Task: Prepare submission materials

**README.md:**
```markdown
# Self-Evolving Coding Agent

An AI assistant that learns your coding preferences from conversation patterns.

## How It Works

1. **Pattern Extraction**: Analyzed 19 conversations to extract 10 key interaction patterns
2. **Pattern Matching**: Keywords trigger relevant patterns for each query
3. **Prompt Augmentation**: Dynamically builds prompts with learned patterns
4. **Response Generation**: Claude API generates responses following your style

## Patterns Learned

- Production Readiness Checker
- Tradeoff Analysis First
- Hint-Based Debugging
- Gap Analysis & Completeness
- Precision Policing
- Multi-Dimensional Evaluation
- Mechanistic Explanation
- Diminishing Returns Analysis
- Challenging Logic
- Brutal Accuracy

## Running the Demo

```bash
pip install streamlit anthropic
export ANTHROPIC_API_KEY=your_key_here
streamlit run demo.py
```

## Before vs After

**Before Learning:**
> "Here's a rate limiter implementation: [basic code]"

**After Learning:**
> "Before implementing, let me understand context:
> - Scale? (requests/sec)
> - Requirements? (latency, consistency)
> 
> Tradeoff Analysis:
> Option A: Token Bucket...
> Option B: Sliding Window...
> 
> [Full implementation with tests, error handling, docs]"
```

**Demo Video Script (3 minutes):**
1. **Intro (30s)**: Problem statement - coding assistants don't remember your preferences
2. **Learning Phase (30s)**: Show pattern extraction from conversations
3. **Before Example (45s)**: Generic response to "implement rate limiter"
4. **After Example (45s)**: Same query with learned patterns applied
5. **Multiple Patterns (30s)**: Show 2-3 more quick examples
6. **Closing (30s)**: Future work - automated pattern extraction, fine-tuning

---

## Phase 1 Success Criteria

✅ **10 patterns** extracted and structured
✅ **Pattern matching** working for all query types
✅ **Before/after comparison** shows clear improvement
✅ **Demo runs** without errors
✅ **3-minute video** recorded
✅ **README** with setup instructions

**Time Budget:** 5.5 hours
**Risk:** Low
**Demo Quality:** High (clear before/after)
**Hackathon Ready:** ✅ YES

---

# PHASE 2: WALK - Few-Shot Learning

## Goal
Add dynamic example selection to show Claude similar conversations before responding.

## Timeline: +3-6 Hours (Post-Hackathon)

### What You're Adding

```
User Query → Pattern Matcher → Augmented Prompt + Examples → Claude API
                                         ↑
                                Example Selector
                                         ↑
                                Conversation Database
                            (Your 19 real conversations)
```

**Key Addition:** Instead of just patterns, include full conversation examples that are similar to current query.

---

## Implementation Steps

### Step 1: Conversation Database (1 hour)

```python
# conversation_db.py
import json
from typing import List, Dict
import anthropic

class ConversationDatabase:
    """
    Stores and retrieves full conversation examples.
    """
    
    def __init__(self, conversations_file='conversations.json'):
        self.conversations = self._load_conversations(conversations_file)
        self.client = anthropic.Anthropic()
    
    def _load_conversations(self, file_path: str) -> List[Dict]:
        """Load pre-parsed conversations."""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def find_similar(self, query: str, k: int = 2) -> List[Dict]:
        """
        Find k most similar conversations to query.
        
        Uses Claude to score similarity (simple approach).
        For production: use embeddings + vector search.
        """
        scored = []
        
        for conv in self.conversations:
            # Extract first user message from conversation
            user_msg = self._extract_first_user_message(conv)
            
            # Score similarity
            score = self._similarity_score(query, user_msg)
            scored.append((score, conv))
        
        # Return top k
        scored.sort(reverse=True)
        return [conv for _, conv in scored[:k]]
    
    def _extract_first_user_message(self, conversation: Dict) -> str:
        """Get the initial user query from conversation."""
        for msg in conversation['messages']:
            if msg['role'] == 'user':
                return msg['content']
        return ""
    
    def _similarity_score(self, query1: str, query2: str) -> float:
        """
        Simple keyword overlap similarity.
        
        For Phase 3: Replace with embeddings.
        """
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def format_example(self, conversation: Dict) -> str:
        """Format conversation for prompt inclusion."""
        formatted = "Example conversation:\n\n"
        
        for msg in conversation['messages']:
            role = msg['role'].capitalize()
            content = msg['content'][:500]  # Truncate if too long
            formatted += f"{role}: {content}\n\n"
        
        return formatted

# Create conversation database from your markdown files
def create_conversation_database():
    """
    Parse your 19 markdown conversation files into JSON.
    """
    conversations = []
    
    # This would parse your actual conversation markdown files
    # For now, placeholder structure
    
    example_conversation = {
        "id": "conv_001",
        "topic": "rate_limiter_implementation",
        "messages": [
            {
                "role": "user",
                "content": "Implement a rate limiter for our API"
            },
            {
                "role": "assistant",
                "content": "Before implementing, let me understand your context:\n\n- Scale? (users, requests/sec)\n- Requirements? (latency, consistency)\n\nTradeoff Analysis:\n\n**Token Bucket:**\n- ✓ O(1) memory\n- ✓ Handles bursts\n...[full response with production readiness]"
            }
        ]
    }
    
    conversations.append(example_conversation)
    
    # Save to file
    with open('conversations.json', 'w') as f:
        json.dump(conversations, f, indent=2)
    
    return conversations
```

**Deliverable:** `conversation_db.py` + `conversations.json`

---

### Step 2: Enhanced Agent with Few-Shot (2 hours)

```python
# agent_v2.py
import anthropic
from pattern_matcher import PatternMatcher
from conversation_db import ConversationDatabase
from typing import Optional, List

class SelfEvolvingAgentV2:
    """
    Agent with both pattern-based prompting AND few-shot examples.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.matcher = PatternMatcher()
        self.conversation_db = ConversationDatabase()
        self.model = "claude-sonnet-4-5-20250929"
    
    def respond(
        self, 
        query: str, 
        use_patterns: bool = True,
        use_examples: bool = True,
        num_examples: int = 2
    ) -> tuple[str, dict]:
        """
        Generate response with patterns and/or examples.
        
        Returns:
            (response_text, metadata_dict)
        """
        metadata = {
            'patterns_applied': [],
            'examples_used': []
        }
        
        # Build system prompt
        system_sections = ["You are a coding assistant for Kartik."]
        
        # Add patterns
        if use_patterns:
            patterns = self.matcher.match(query)
            pattern_section = self._build_pattern_section(patterns)
            system_sections.append(pattern_section)
            metadata['patterns_applied'] = self.matcher.get_pattern_names(patterns)
        
        # Add examples
        if use_examples:
            examples = self.conversation_db.find_similar(query, k=num_examples)
            example_section = self._build_example_section(examples)
            system_sections.append(example_section)
            metadata['examples_used'] = len(examples)
        
        system_prompt = "\n\n---\n\n".join(system_sections)
        
        # Generate response
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": query}]
        )
        
        response_text = message.content[0].text
        return response_text, metadata
    
    def _build_pattern_section(self, patterns: List) -> str:
        """Build pattern section (same as Phase 1)."""
        section = "# Your Learned Patterns:\n\n"
        
        for pattern in patterns:
            section += f"## {pattern['name']}\n"
            section += f"{pattern['description']}\n"
            section += f"Template: {pattern['template']}\n\n"
        
        return section
    
    def _build_example_section(self, examples: List) -> str:
        """Build example section."""
        section = "# Similar Past Conversations:\n\n"
        section += "Here are examples of how you prefer to respond to similar queries:\n\n"
        
        for i, conv in enumerate(examples, 1):
            section += f"## Example {i}:\n"
            section += self.conversation_db.format_example(conv)
            section += "\n---\n\n"
        
        section += "Follow similar patterns in your response.\n"
        return section
```

**Deliverable:** `agent_v2.py` - Enhanced agent with few-shot

---

### Step 3: Updated Demo (2 hours)

```python
# demo_v2.py
import streamlit as st
from agent_v2 import SelfEvolvingAgentV2

st.title("🧠 Self-Evolving Agent v2: Few-Shot Learning")

agent = SelfEvolvingAgentV2()

# New comparison options
mode = st.radio(
    "Select mode:",
    ["Generic", "Patterns Only", "Examples Only", "Patterns + Examples"]
)

query = st.text_area("Your question:")

if st.button("Generate"):
    use_patterns = mode in ["Patterns Only", "Patterns + Examples"]
    use_examples = mode in ["Examples Only", "Patterns + Examples"]
    
    response, metadata = agent.respond(
        query,
        use_patterns=use_patterns,
        use_examples=use_examples
    )
    
    # Show metadata
    st.info(f"""
    **Applied:**
    - Patterns: {', '.join(metadata['patterns_applied']) if metadata['patterns_applied'] else 'None'}
    - Examples: {metadata['examples_used']} conversations
    """)
    
    st.markdown(response)
```

**Deliverable:** `demo_v2.py` - Four-way comparison demo

---

### Step 4: Testing & Evaluation (1 hour)

```python
# evaluate_v2.py

def compare_approaches():
    """
    Compare response quality across different modes.
    """
    agent = SelfEvolvingAgentV2()
    
    test_queries = [
        "Implement a distributed counter",
        "Debug this binary search",
        "Review this API design"
    ]
    
    results = []
    
    for query in test_queries:
        # Test all 4 modes
        generic, _ = agent.respond(query, use_patterns=False, use_examples=False)
        patterns_only, _ = agent.respond(query, use_patterns=True, use_examples=False)
        examples_only, _ = agent.respond(query, use_patterns=False, use_examples=True)
        both, meta = agent.respond(query, use_patterns=True, use_examples=True)
        
        results.append({
            'query': query,
            'generic': generic,
            'patterns_only': patterns_only,
            'examples_only': examples_only,
            'both': both,
            'metadata': meta
        })
    
    return results
```

---

## Phase 2 Success Criteria

✅ **Conversation database** created from 19 real conversations
✅ **Similarity search** finds relevant examples
✅ **Four-way comparison** (Generic, Patterns, Examples, Both)
✅ **Examples improve** response quality beyond patterns alone
✅ **Demo showcases** the additive benefit

**Time Budget:** +3-6 hours
**Risk:** Medium (similarity search may need tuning)
**Demo Quality:** Very High (shows progressive improvement)

---

# PHASE 3: RUN - Fine-Tuning

## Goal
Actually train a model on your conversation data for maximum adaptation.

## Timeline: 3-5 Days (Long-term Project)

### What You're Building

```
Conversation Data → Data Preparation → Fine-Tuning → Evaluation → Deployment
       ↓                    ↓                ↓
   19 real convs      200-500 examples   Custom model
   + synthetic        + validation set    
```

**Key Difference:** This trains model weights, not just prompt engineering.

---

## Day 1: Data Preparation (8 hours)

### Task 1: Parse All Conversations (2 hours)

```python
# parse_conversations.py
import re
import json
from pathlib import Path

def parse_markdown_conversation(md_file: Path) -> dict:
    """
    Parse conversation markdown into training format.
    """
    with open(md_file, 'r') as f:
        content = f.read()
    
    # Extract metadata
    metadata = extract_metadata(content)
    
    # Split into turns
    turns = re.split(r'## (👤 User|🤖 Claude|🤖 Assistant)', content)
    
    messages = []
    current_role = None
    
    for i in range(1, len(turns), 2):
        role_marker = turns[i]
        message_content = turns[i+1].strip() if i+1 < len(turns) else ""
        
        if "User" in role_marker:
            role = "user"
        elif "Claude" in role_marker or "Assistant" in role_marker:
            role = "assistant"
        else:
            continue
        
        if message_content:
            messages.append({
                "role": role,
                "content": message_content
            })
    
    return {
        "conversation_id": md_file.stem,
        "metadata": metadata,
        "messages": messages
    }

def extract_metadata(content: str) -> dict:
    """Extract conversation metadata."""
    metadata = {}
    
    # Extract date
    date_match = re.search(r'Date: (\d{4}-\d{2}-\d{2})', content)
    if date_match:
        metadata['date'] = date_match.group(1)
    
    # Extract session ID
    session_match = re.search(r'Session ID: ([\w-]+)', content)
    if session_match:
        metadata['session_id'] = session_match.group(1)
    
    return metadata

def create_training_example(conversation: dict, system_prompt: str) -> dict:
    """
    Convert conversation to fine-tuning format.
    """
    return {
        "messages": [
            {"role": "system", "content": system_prompt}
        ] + conversation['messages']
    }

# Process all conversations
conversation_dir = Path("conversations/")
system_prompt = """You are a coding assistant for Kartik, an ML engineer.

Key preferences:
1. Production readiness checks (tests, error handling, docs)
2. Tradeoff analysis before recommendations
3. Hint-based debugging (not solutions)
4. Precision in technical claims with caveats
5. Gap analysis in reviews
6. Multi-dimensional evaluation
7. Mechanistic explanations with examples
8. Marginal utility thinking
9. Challenge logical leaps
10. Strip complexity to core truth"""

training_examples = []

for md_file in conversation_dir.glob("*.md"):
    conversation = parse_markdown_conversation(md_file)
    example = create_training_example(conversation, system_prompt)
    training_examples.append(example)

print(f"Parsed {len(training_examples)} conversations")

# Save to JSONL
with open('training_data.jsonl', 'w') as f:
    for example in training_examples:
        f.write(json.dumps(example) + '\n')
```

**Deliverable:** `training_data.jsonl` with 19 real examples

---

### Task 2: Synthetic Data Generation (4 hours)

```python
# generate_synthetic.py
import anthropic
import json
from typing import List

class SyntheticDataGenerator:
    """
    Generate synthetic conversations matching user's style.
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-5-20250929"
    
    def generate_batch(
        self,
        real_examples: List[dict],
        num_synthetic: int = 10,
        topics: List[str] = None
    ) -> List[dict]:
        """
        Generate synthetic conversations.
        """
        if topics is None:
            topics = [
                "rate limiting", "caching strategies", "database selection",
                "API design", "debugging algorithms", "code review",
                "system architecture", "testing strategies", "performance optimization",
                "security best practices"
            ]
        
        synthetic = []
        
        for i in range(num_synthetic):
            topic = topics[i % len(topics)]
            
            # Generate conversation
            conversation = self._generate_conversation(
                topic=topic,
                real_examples=real_examples[:3]  # Show 3 examples as templates
            )
            
            if conversation:
                synthetic.append(conversation)
        
        return synthetic
    
    def _generate_conversation(
        self,
        topic: str,
        real_examples: List[dict]
    ) -> dict:
        """
        Generate one synthetic conversation.
        """
        # Build generation prompt
        examples_text = self._format_examples(real_examples)
        
        generation_prompt = f"""I need you to generate a realistic coding conversation about {topic}.

Here are examples of my actual conversation style:

{examples_text}

Generate a NEW conversation (3-5 turns) about {topic} that follows the SAME patterns:
- User asks a question
- Assistant responds with: context questions, tradeoff analysis, production checks, precise language
- User may ask follow-ups
- Assistant maintains same style

Format as JSON:
{{
  "messages": [
    {{"role": "user", "content": "..."}},
    {{"role": "assistant", "content": "..."}},
    ...
  ]
}}

Make it realistic and different from the examples."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            messages=[{"role": "user", "content": generation_prompt}]
        )
        
        response_text = message.content[0].text
        
        # Parse JSON from response
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0]
            else:
                json_text = response_text
            
            conversation = json.loads(json_text)
            return conversation
        except json.JSONDecodeError:
            print(f"Failed to parse generated conversation for topic: {topic}")
            return None
    
    def _format_examples(self, examples: List[dict]) -> str:
        """Format example conversations for prompt."""
        formatted = ""
        
        for i, example in enumerate(examples, 1):
            formatted += f"\n### Example {i}:\n"
            for msg in example['messages'][:4]:  # First 2 turns
                role = msg['role'].capitalize()
                content = msg['content'][:300]  # Truncate
                formatted += f"{role}: {content}...\n\n"
        
        return formatted

# Generate synthetic data
generator = SyntheticDataGenerator()

# Load real examples
with open('training_data.jsonl', 'r') as f:
    real_examples = [json.loads(line) for line in f]

print(f"Loaded {len(real_examples)} real examples")

# Generate 100 synthetic conversations (in batches)
all_synthetic = []

for batch in range(10):
    print(f"Generating batch {batch+1}/10...")
    synthetic_batch = generator.generate_batch(
        real_examples=real_examples,
        num_synthetic=10
    )
    all_synthetic.extend(synthetic_batch)

print(f"Generated {len(all_synthetic)} synthetic conversations")

# Save synthetic data
with open('synthetic_data.jsonl', 'w') as f:
    for conv in all_synthetic:
        example = {
            "messages": [
                {"role": "system", "content": system_prompt}
            ] + conv['messages']
        }
        f.write(json.dumps(example) + '\n')
```

**Deliverable:** `synthetic_data.jsonl` with ~100 synthetic examples

---

### Task 3: Data Augmentation via Paraphrasing (2 hours)

```python
# augment_data.py
import anthropic
import json

def paraphrase_user_query(original_query: str, client) -> List[str]:
    """
    Generate 3-5 paraphrased versions of user query.
    """
    prompt = f"""Paraphrase this coding question in 4 different ways.
Keep the same meaning but use different words/structure.

Original: {original_query}

Return as JSON array: ["paraphrase1", "paraphrase2", ...]"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        paraphrases = json.loads(message.content[0].text)
        return paraphrases
    except:
        return []

def augment_dataset(input_file: str, output_file: str):
    """
    Create paraphrased versions of all conversations.
    """
    client = anthropic.Anthropic()
    
    with open(input_file, 'r') as f:
        examples = [json.loads(line) for line in f]
    
    augmented = []
    
    for example in examples:
        # Keep original
        augmented.append(example)
        
        # Generate paraphrases
        first_user_msg = None
        for msg in example['messages']:
            if msg['role'] == 'user':
                first_user_msg = msg['content']
                break
        
        if first_user_msg:
            paraphrases = paraphrase_user_query(first_user_msg, client)
            
            # Create augmented examples
            for paraphrase in paraphrases[:3]:  # Use top 3
                augmented_example = {
                    "messages": example['messages'].copy()
                }
                # Replace first user message
                for i, msg in enumerate(augmented_example['messages']):
                    if msg['role'] == 'user':
                        augmented_example['messages'][i] = {
                            "role": "user",
                            "content": paraphrase
                        }
                        break
                
                augmented.append(augmented_example)
    
    # Save augmented dataset
    with open(output_file, 'w') as f:
        for example in augmented:
            f.write(json.dumps(example) + '\n')
    
    print(f"Augmented {len(examples)} examples to {len(augmented)} examples")

# Run augmentation
augment_dataset('training_data.jsonl', 'training_augmented.jsonl')
augment_dataset('synthetic_data.jsonl', 'synthetic_augmented.jsonl')
```

**Deliverable:** Augmented datasets (~200-400 total examples)

---

## Day 2: Fine-Tuning (8 hours)

### Option A: OpenAI Fine-Tuning (Easiest)

```python
# openai_finetune.py
import openai
import json

# Combine all training data
training_files = [
    'training_augmented.jsonl',
    'synthetic_augmented.jsonl'
]

combined_data = []
for file in training_files:
    with open(file, 'r') as f:
        combined_data.extend([json.loads(line) for line in f])

print(f"Total training examples: {len(combined_data)}")

# Save combined data
with open('training_combined.jsonl', 'w') as f:
    for example in combined_data:
        f.write(json.dumps(example) + '\n')

# Upload training file
with open('training_combined.jsonl', 'rb') as f:
    response = openai.File.create(
        file=f,
        purpose='fine-tune'
    )

training_file_id = response['id']
print(f"Uploaded training file: {training_file_id}")

# Create fine-tuning job
finetune_job = openai.FineTuning.create(
    training_file=training_file_id,
    model="gpt-4o-mini-2024-07-18",
    hyperparameters={
        "n_epochs": 3,
        "learning_rate_multiplier": 0.5,
        "batch_size": 4
    }
)

job_id = finetune_job['id']
print(f"Started fine-tuning job: {job_id}")

# Monitor progress
import time

while True:
    status = openai.FineTuning.retrieve(job_id)
    print(f"Status: {status['status']}")
    
    if status['status'] in ['succeeded', 'failed']:
        break
    
    time.sleep(60)

if status['status'] == 'succeeded':
    print(f"Fine-tuned model: {status['fine_tuned_model']}")
    
    # Save model ID
    with open('finetuned_model_id.txt', 'w') as f:
        f.write(status['fine_tuned_model'])
```

**Time:** 1-2 hours for training
**Cost:** ~$10-20

---

### Option B: Hugging Face + LoRA (Most Control)

```python
# huggingface_finetune.py
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset
import torch

# 1. Load base model
model_name = "meta-llama/Llama-3.1-8B-Instruct"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_8bit=True,
    torch_dtype=torch.float16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# 2. Setup LoRA
model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# 3. Load dataset
dataset = load_dataset('json', data_files={
    'train': 'training_combined.jsonl',
    'validation': 'validation.jsonl'  # Hold out 10% for validation
})

# 4. Tokenize
def tokenize_function(examples):
    # Format as chat
    texts = []
    for messages in examples['messages']:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )
        texts.append(text)
    
    return tokenizer(
        texts,
        truncation=True,
        max_length=2048,
        padding='max_length'
    )

tokenized_dataset = dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=dataset['train'].column_names
)

# 5. Training arguments
training_args = TrainingArguments(
    output_dir="./kartik-coding-agent",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_strategy="epoch",
    evaluation_strategy="epoch",
    warmup_steps=50,
    save_total_limit=2,
    load_best_model_at_end=True,
)

# 6. Data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

# 7. Train
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset['train'],
    eval_dataset=tokenized_dataset['validation'],
    data_collator=data_collator,
)

print("Starting training...")
trainer.train()

# 8. Save
model.save_pretrained("./kartik-agent-lora")
tokenizer.save_pretrained("./kartik-agent-lora")

print("Fine-tuning complete!")
```

**Time:** 2-4 hours on GPU
**Cost:** $1-3 on cloud GPU

---

## Day 3: Evaluation (8 hours)

```python
# evaluate_finetuned.py
import json
from agent_v2 import SelfEvolvingAgentV2
import openai  # or your finetuned model

class ModelComparison:
    """
    Compare base model, pattern-augmented, and fine-tuned.
    """
    
    def __init__(self):
        self.base_agent = SelfEvolvingAgentV2()
        self.finetuned_model_id = self._load_finetuned_id()
    
    def _load_finetuned_id(self):
        with open('finetuned_model_id.txt', 'r') as f:
            return f.read().strip()
    
    def evaluate_query(self, query: str) -> dict:
        """
        Get responses from all 3 approaches.
        """
        # 1. Base model (no patterns)
        base_response, _ = self.base_agent.respond(
            query,
            use_patterns=False,
            use_examples=False
        )
        
        # 2. Pattern-augmented (Phase 1)
        pattern_response, _ = self.base_agent.respond(
            query,
            use_patterns=True,
            use_examples=False
        )
        
        # 3. Fine-tuned
        finetuned_response = openai.ChatCompletion.create(
            model=self.finetuned_model_id,
            messages=[{"role": "user", "content": query}]
        )['choices'][0]['message']['content']
        
        return {
            'query': query,
            'base': base_response,
            'pattern_augmented': pattern_response,
            'finetuned': finetuned_response
        }
    
    def score_response(self, response: str, query: str) -> dict:
        """
        Score response on your 10 patterns.
        """
        scores = {}
        
        # Production Readiness
        scores['production_readiness'] = (
            ('tests' in response.lower()) * 1 +
            ('error handling' in response.lower()) * 1 +
            ('type hint' in response.lower() or 'typing' in response.lower()) * 1
        ) / 3
        
        # Tradeoff Analysis
        scores['tradeoff_analysis'] = (
            ('option a' in response.lower() and 'option b' in response.lower()) * 1 +
            ('pros' in response.lower() and 'cons' in response.lower()) * 1
        ) / 2
        
        # Precision (caveats/qualifications)
        scores['precision'] = (
            ('note:' in response.lower()) * 1 +
            ('caveat' in response.lower()) * 1 +
            ('however' in response.lower()) * 1
        ) / 3
        
        # Context questions
        scores['context_questions'] = (
            response.count('?') >= 2
        ) * 1
        
        # Overall
        scores['overall'] = sum(scores.values()) / len(scores)
        
        return scores
    
    def run_evaluation(self, test_queries: list) -> dict:
        """
        Evaluate all approaches on test queries.
        """
        results = []
        
        for query in test_queries:
            responses = self.evaluate_query(query)
            
            # Score each response
            base_scores = self.score_response(responses['base'], query)
            pattern_scores = self.score_response(responses['pattern_augmented'], query)
            finetuned_scores = self.score_response(responses['finetuned'], query)
            
            results.append({
                'query': query,
                'responses': responses,
                'scores': {
                    'base': base_scores,
                    'pattern_augmented': pattern_scores,
                    'finetuned': finetuned_scores
                }
            })
        
        return results

# Run evaluation
test_queries = [
    "Implement a rate limiter",
    "Review this code: [code snippet]",
    "Debug this binary search: [buggy code]",
    "Should we use microservices or monolith?",
    "Explain how Redis handles distributed locking"
]

evaluator = ModelComparison()
results = evaluator.run_evaluation(test_queries)

# Print results
for result in results:
    print(f"\n{'='*80}")
    print(f"Query: {result['query']}")
    print(f"{'='*80}")
    
    scores = result['scores']
    print(f"\nBase Model Score: {scores['base']['overall']:.2f}")
    print(f"Pattern-Augmented Score: {scores['pattern_augmented']['overall']:.2f}")
    print(f"Fine-Tuned Score: {scores['finetuned']['overall']:.2f}")
    
    # Winner
    winner = max(scores.items(), key=lambda x: x[1]['overall'])
    print(f"\n🏆 Winner: {winner[0]}")

# Save results
with open('evaluation_results.json', 'w') as f:
    json.dump(results, f, indent=2)
```

**Expected Results:**
- Base: 0.3-0.4
- Pattern-Augmented: 0.6-0.7
- Fine-Tuned: 0.7-0.9 (if successful)

---

## Days 4-5: Integration & Demo (16 hours)

### Task: Build unified system with fallback

```python
# unified_agent.py

class UnifiedSelfEvolvingAgent:
    """
    Production system combining all approaches with fallback.
    """
    
    def __init__(self):
        # Phase 1: Patterns
        self.pattern_matcher = PatternMatcher()
        
        # Phase 2: Examples
        self.conversation_db = ConversationDatabase()
        
        # Phase 3: Fine-tuned model
        try:
            self.finetuned_model = self._load_finetuned_model()
            self.has_finetuned = True
        except:
            self.finetuned_model = None
            self.has_finetuned = False
        
        self.base_client = anthropic.Anthropic()
    
    def respond(self, query: str, mode: str = "auto") -> str:
        """
        Generate response using best available method.
        
        Args:
            query: User's question
            mode: "auto", "finetuned", "pattern", "base"
        """
        if mode == "auto":
            # Try fine-tuned first
            if self.has_finetuned:
                response = self._finetuned_response(query)
                
                # Validate quality
                if self._validate_response(response, query):
                    return response
            
            # Fallback to pattern-augmented
            return self._pattern_response(query)
        
        elif mode == "finetuned" and self.has_finetuned:
            return self._finetuned_response(query)
        
        elif mode == "pattern":
            return self._pattern_response(query)
        
        else:  # base
            return self._base_response(query)
    
    def _finetuned_response(self, query: str) -> str:
        """Use fine-tuned model."""
        # Implementation depends on where model is hosted
        pass
    
    def _pattern_response(self, query: str) -> str:
        """Phase 1+2: Pattern + Examples."""
        patterns = self.pattern_matcher.match(query)
        examples = self.conversation_db.find_similar(query, k=2)
        
        system_prompt = self._build_prompt(patterns, examples)
        
        message = self.base_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": query}]
        )
        
        return message.content[0].text
    
    def _base_response(self, query: str) -> str:
        """Vanilla Claude."""
        message = self.base_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": query}]
        )
        
        return message.content[0].text
    
    def _validate_response(self, response: str, query: str) -> bool:
        """
        Check if response matches expected patterns.
        """
        # Basic validation
        if len(response) < 100:
            return False
        
        # Check for key patterns
        if "implement" in query.lower():
            # Should have tradeoff analysis
            if not ("option" in response.lower() and "✓" in response):
                return False
        
        return True
```

---

## Phase 3 Success Criteria

✅ **200-400 training examples** (real + synthetic + augmented)
✅ **Fine-tuned model** trained and deployed
✅ **Evaluation** shows improvement over pattern-only
✅ **Unified system** with graceful fallback
✅ **Production deployment** ready

**Time Budget:** 3-5 days
**Risk:** High (may not improve over patterns)
**Demo Quality:** Exceptional (if successful)
**Production Value:** Very High

---

# Comparison: All Three Phases

## Response Quality Progression

**Example Query:** "Implement a rate limiter"

### Phase 1 (Patterns Only):
```
Before implementing, let me understand context:
- Scale? (requests/sec)
- Requirements? (latency, consistency)

Tradeoff Analysis:
**Option A: Token Bucket**
- ✓ O(1) memory, handles bursts
- ✗ Not distributed-friendly
...

[Implementation with tests, error handling, docs]
```

### Phase 2 (Patterns + Examples):
```
Before implementing, let me understand context:
[Same as Phase 1, but more natural phrasing]

Similar to how I approached the caching question earlier,
let's analyze the tradeoffs...

[Even more aligned with your specific phrasing patterns]
```

### Phase 3 (Fine-Tuned):
```
[Response that naturally embodies all patterns without
explicit prompting - most human-like adaptation]
```

---

## Cost Comparison

| Phase | Development | Infrastructure | API Costs | Total |
|-------|-------------|----------------|-----------|-------|
| **CRAWL** | 5.5 hours | $0 | $2-5/month | ~$5 |
| **WALK** | +6 hours | $0 | $5-10/month | ~$15 |
| **RUN** | +40 hours | $20-50 | $10-20/month | $100+ |

---

## Risk vs Reward

| Phase | Risk | Reward | Recommended For |
|-------|------|--------|-----------------|
| **CRAWL** | Low | Medium-High | Hackathons, MVPs, demos |
| **WALK** | Medium | High | Production v1, longer projects |
| **RUN** | High | Very High | Long-term, high-volume use |

---

# Recommended Path

## For Hackathon (5.5 hours available)
**Execute: CRAWL only**
- Proven approach
- Demo-ready
- Low risk

## Post-Hackathon (Learning Project)
**Week 1-2:** Polish CRAWL, test thoroughly
**Week 3-4:** Add WALK features
**Month 2-3:** Attempt RUN with proper evaluation

## For Production (Real Product)
**Month 1:** CRAWL (MVP)
**Month 2-3:** WALK (v1.0)
**Month 4-6:** RUN (v2.0 with fine-tuning)

---

# Conclusion

You now have three complete implementation paths:

1. **CRAWL:** Memory-augmented prompting (5.5h, hackathon-ready)
2. **WALK:** + Few-shot learning (11h total, production v1)
3. **RUN:** + Fine-tuning (5 days total, production v2)

Each phase builds incrementally on the previous one.

**My strong recommendation for your hackathon: Execute CRAWL, document WALK and RUN as future work.**

Good luck! 🚀
