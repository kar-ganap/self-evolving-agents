# Level 2: Online Learning + Architectural Changes
## Self-Evolving Agent Tool Generation Implementation Plan

## Document Purpose
Detailed incremental additions to the base training plan (Level 1) to enable the agent to **create new tools** based on learned patterns. Each phase shows exactly what to add to the corresponding Level 1 phase.

---

## Overview: What Is Level 2?

### The Core Difference

**Level 1 (Memory-Augmented Prompting):**
```
User Query → Pattern Matcher → Augmented Prompt → Claude API → Response
```
- Agent learns patterns
- Agent applies patterns via prompts
- **Architecture is static**

**Level 2 (Architectural Changes):**
```
User Query → Pattern Matcher → Tool Generator → Tool Execution → Response
                                      ↓
                              Tool Registry
                          (Auto-generated tools)
```
- Agent learns patterns
- Agent **creates tools** to automate patterns
- **Architecture evolves** (new capabilities added)

### What "Architectural Changes" Means

The agent doesn't just remember your preferences—it **writes code** to automate them.

**Example:**
- **Level 1:** "I notice you always ask for tests. I'll mention tests in my response."
- **Level 2:** "I notice you always ask for tests. I've created a `TestCoverageAnalyzer` tool that automatically checks for tests."

---

## Philosophy: When Should Patterns Become Tools?

Not every pattern should become a tool. Use this decision framework:

### ✅ Good Tool Candidates

1. **Repetitive** - Pattern triggers frequently (priority 1)
2. **Mechanical** - Can be automated with rules (not creative)
3. **Deterministic** - Clear success criteria
4. **Checkable** - Has objective pass/fail conditions

**Examples:**
- ✅ Production readiness checks (tests, error handling, type hints)
- ✅ Gap analysis (what's missing from a checklist)
- ✅ Precision validation (overly broad claims)
- ✅ Complexity analysis (O(n) statements in code)

### ❌ Bad Tool Candidates

1. **Creative** - Requires reasoning and context
2. **Subjective** - No clear right answer
3. **Contextual** - Depends on situation
4. **Rare** - Only triggers occasionally

**Examples:**
- ❌ Tradeoff analysis (requires deep reasoning)
- ❌ Challenging logic (context-dependent)
- ❌ Brutal accuracy (creative insight)
- ❌ Mechanistic explanations (teaching skill)

---

## Incremental Additions: CRAWL Phase

**Base:** Level 1 CRAWL (5.5 hours - memory-augmented prompting)
**Addition:** Tool generation layer (+4 hours)
**Total:** 9.5 hours

---

## Hour 6: Tool Opportunity Analysis

### Goal
Analyze your 10 learned patterns to determine which should become tools.

### Implementation

```python
# tool_analyzer.py

from typing import Dict, List
import json

class ToolAnalyzer:
    """
    Analyzes patterns to identify automation opportunities.
    
    Uses a scoring system to determine which patterns are:
    - Repetitive enough to justify automation
    - Mechanical enough to be codifiable
    - Deterministic enough to implement reliably
    """
    
    def __init__(self, patterns_file: str = 'patterns.json'):
        with open(patterns_file, 'r') as f:
            self.patterns = json.load(f)
        
        self.tool_candidates = []
    
    def analyze_all_patterns(self) -> List[Dict]:
        """
        Score all patterns for tool-worthiness.
        
        Returns:
            List of tool candidates sorted by automation score
        """
        for pattern_key, pattern_data in self.patterns.items():
            score = self._calculate_automation_score(pattern_data)
            
            if score >= 0.5:  # Threshold for tool generation
                self.tool_candidates.append({
                    'pattern_key': pattern_key,
                    'pattern_name': pattern_data['name'],
                    'tool_type': self._determine_tool_type(pattern_data),
                    'automation_score': score,
                    'reasoning': self._explain_score(pattern_data, score)
                })
        
        # Sort by score (highest first)
        self.tool_candidates.sort(key=lambda x: x['automation_score'], reverse=True)
        
        return self.tool_candidates
    
    def _calculate_automation_score(self, pattern: Dict) -> float:
        """
        Calculate 0-1 score based on automation potential.
        
        Scoring factors:
        - Priority (0.3): How often does this trigger?
        - Mechanical (0.4): How rule-based is the checking?
        - Deterministic (0.3): How clear are the criteria?
        """
        score = 0.0
        
        # Factor 1: Priority (high priority = triggers often)
        priority = pattern.get('priority', 3)
        if priority == 1:
            score += 0.3
        elif priority == 2:
            score += 0.2
        elif priority == 3:
            score += 0.1
        
        # Factor 2: Mechanical nature
        # Check if pattern involves checking/validating/analyzing
        description = pattern.get('description', '').lower()
        mechanical_keywords = [
            'check', 'validate', 'analyze', 'verify', 'detect',
            'identify', 'count', 'measure', 'find', 'scan'
        ]
        
        mechanical_count = sum(1 for keyword in mechanical_keywords if keyword in description)
        score += min(0.4, mechanical_count * 0.1)
        
        # Factor 3: Deterministic criteria
        # Patterns with clear templates and examples are more deterministic
        if len(pattern.get('template', '')) > 100:
            score += 0.15
        
        if len(pattern.get('example', '')) > 200:
            score += 0.15
        
        return min(1.0, score)
    
    def _determine_tool_type(self, pattern: Dict) -> str:
        """
        Categorize what type of tool this should be.
        """
        name = pattern['name'].lower()
        description = pattern.get('description', '').lower()
        
        if 'check' in name or 'readiness' in name:
            return 'static_analyzer'
        elif 'gap' in name or 'analysis' in name or 'completeness' in name:
            return 'evaluator'
        elif 'precision' in name or 'validate' in name or 'verify' in name:
            return 'validator'
        elif 'detect' in description or 'identify' in description:
            return 'detector'
        else:
            return 'helper'
    
    def _explain_score(self, pattern: Dict, score: float) -> str:
        """
        Generate human-readable explanation of score.
        """
        reasons = []
        
        if pattern.get('priority', 3) == 1:
            reasons.append("High priority (always applied)")
        
        description = pattern.get('description', '').lower()
        if 'check' in description:
            reasons.append("Contains checkable criteria")
        
        if len(pattern.get('template', '')) > 100:
            reasons.append("Has detailed template")
        
        if not reasons:
            reasons.append("Low automation potential")
        
        return f"Score {score:.2f}: " + ", ".join(reasons)
    
    def print_analysis(self):
        """
        Print human-readable analysis report.
        """
        print("=" * 80)
        print("TOOL OPPORTUNITY ANALYSIS")
        print("=" * 80)
        print(f"\nAnalyzed {len(self.patterns)} patterns")
        print(f"Found {len(self.tool_candidates)} tool candidates (score >= 0.5)\n")
        
        for i, candidate in enumerate(self.tool_candidates, 1):
            print(f"{i}. {candidate['pattern_name']}")
            print(f"   Type: {candidate['tool_type']}")
            print(f"   {candidate['reasoning']}")
            print()
        
        if not self.tool_candidates:
            print("No patterns scored high enough for tool generation.")
            print("Consider lowering threshold or adding more mechanical patterns.")
    
    def get_top_candidates(self, n: int = 3) -> List[Dict]:
        """Get top N tool candidates."""
        return self.tool_candidates[:n]

# Usage Example
if __name__ == '__main__':
    analyzer = ToolAnalyzer('patterns.json')
    candidates = analyzer.analyze_all_patterns()
    analyzer.print_analysis()
    
    # Get top 3 for implementation
    top_3 = analyzer.get_top_candidates(3)
    
    print("\n" + "=" * 80)
    print("RECOMMENDED FOR IMPLEMENTATION")
    print("=" * 80)
    for candidate in top_3:
        print(f"✓ {candidate['pattern_name']} ({candidate['tool_type']})")
```

### Expected Output

```
================================================================================
TOOL OPPORTUNITY ANALYSIS
================================================================================

Analyzed 10 patterns
Found 3 tool candidates (score >= 0.5)

1. Production Readiness Checker
   Type: static_analyzer
   Score 1.00: High priority (always applied), Contains checkable criteria, Has detailed template

2. Gap Analysis & Completeness
   Type: evaluator
   Score 0.85: High priority (always applied), Contains checkable criteria, Has detailed template

3. Precision Policing
   Type: validator
   Score 0.70: High priority (always applied), Contains checkable criteria

================================================================================
RECOMMENDED FOR IMPLEMENTATION
================================================================================
✓ Production Readiness Checker (static_analyzer)
✓ Gap Analysis & Completeness (evaluator)
✓ Precision Policing (validator)
```

### Deliverable
- `tool_analyzer.py` - Analysis script
- Analysis report showing top 3 tool candidates

---

## Hour 7: Automated Tool Code Generation

### Goal
Use Claude API to generate Python tool code from pattern descriptions.

### Implementation

```python
# tool_generator.py

import anthropic
import json
import os
from typing import Dict, Optional

class ToolCodeGenerator:
    """
    Generates Python tool code from pattern descriptions.
    
    Uses Claude to write production-quality tools that:
    - Follow your coding standards
    - Include error handling
    - Have clear interfaces
    - Return structured results
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"
        self.generated_tools = {}
    
    def generate_tool(
        self,
        pattern: Dict,
        tool_type: str,
        pattern_key: str
    ) -> tuple[str, str]:
        """
        Generate complete tool code from pattern.
        
        Args:
            pattern: Pattern dictionary from patterns.json
            tool_type: Type of tool (static_analyzer, evaluator, etc.)
            pattern_key: Key for saving/loading tool
            
        Returns:
            (tool_code, class_name)
        """
        class_name = self._generate_class_name(pattern['name'])
        
        # Build generation prompt
        generation_prompt = self._build_generation_prompt(
            pattern=pattern,
            tool_type=tool_type,
            class_name=class_name
        )
        
        # Generate code using Claude
        message = self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            temperature=0.3,  # Lower temp for consistent code generation
            system="You are an expert Python developer generating production-quality tools.",
            messages=[{"role": "user", "content": generation_prompt}]
        )
        
        tool_code = message.content[0].text
        
        # Extract Python code from markdown if present
        tool_code = self._extract_code(tool_code)
        
        # Validate generated code
        if not self._validate_tool_code(tool_code, class_name):
            raise ValueError(f"Generated code for {class_name} failed validation")
        
        return tool_code, class_name
    
    def _build_generation_prompt(
        self,
        pattern: Dict,
        tool_type: str,
        class_name: str
    ) -> str:
        """
        Build detailed prompt for tool generation.
        """
        prompt = f"""Generate a production-quality Python tool that automates this pattern.

# Pattern Information
**Name:** {pattern['name']}
**Description:** {pattern['description']}
**Tool Type:** {tool_type}

# Requirements

1. **Class Structure:**
   - Class name: `{class_name}`
   - Main method: `analyze(self, code: str) -> dict`
   - Return format: {{'score': float, 'checks': dict, 'issues': list, 'suggestions': list}}

2. **Functionality:**
   Based on the pattern description, implement checks that detect:
   - What the pattern looks for
   - Common issues related to this pattern
   - Suggestions for improvement

3. **Code Quality:**
   - Include comprehensive docstrings
   - Add type hints
   - Handle edge cases (empty input, None, etc.)
   - Include example usage in __main__ block

4. **Return Structure:**
   ```python
   {{
       'score': 0.0-1.0,  # Overall score
       'checks': {{  # Individual check results
           'check_name': bool,
           ...
       }},
       'issues': [  # Problems found
           "Description of issue",
           ...
       ],
       'suggestions': [  # Recommendations
           "How to fix issue",
           ...
       ]
   }}
   ```

# Example Pattern Application

{pattern.get('example', 'N/A')}

# Template to Follow

{pattern.get('template', 'N/A')}

Generate ONLY the Python code. No explanation, no markdown except code block.
"""
        return prompt
    
    def _extract_code(self, response_text: str) -> str:
        """Extract Python code from Claude's response."""
        # Check for markdown code blocks
        if "```python" in response_text:
            code = response_text.split("```python")[1].split("```")[0]
            return code.strip()
        elif "```" in response_text:
            code = response_text.split("```")[1].split("```")[0]
            return code.strip()
        else:
            return response_text.strip()
    
    def _validate_tool_code(self, code: str, class_name: str) -> bool:
        """
        Basic validation of generated tool code.
        """
        # Check for class definition
        if f"class {class_name}" not in code:
            print(f"❌ Missing class definition: {class_name}")
            return False
        
        # Check for analyze method
        if "def analyze" not in code:
            print(f"❌ Missing analyze method")
            return False
        
        # Check for return statement
        if "return" not in code:
            print(f"❌ No return statement found")
            return False
        
        # Try to compile (syntax check)
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            print(f"❌ Syntax error: {e}")
            return False
        
        return True
    
    def _generate_class_name(self, pattern_name: str) -> str:
        """
        Convert pattern name to PascalCase class name.
        
        Examples:
        - "Production Readiness Checker" -> "ProductionReadinessChecker"
        - "Gap Analysis & Completeness" -> "GapAnalysisAndCompleteness"
        """
        # Remove special characters
        clean_name = pattern_name.replace('&', 'And').replace('-', ' ')
        
        # Convert to PascalCase
        words = clean_name.split()
        class_name = ''.join(word.capitalize() for word in words)
        
        return class_name
    
    def save_tool(
        self,
        pattern_key: str,
        tool_code: str,
        class_name: str,
        output_dir: str = 'tools'
    ) -> str:
        """
        Save generated tool to file.
        
        Returns:
            Path to saved file
        """
        # Create tools directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"generated_{pattern_key}.py"
        filepath = os.path.join(output_dir, filename)
        
        # Add header
        header = f"""# Auto-generated tool
# Pattern: {pattern_key}
# Class: {class_name}
# Generated by: ToolCodeGenerator

"""
        
        full_code = header + tool_code
        
        # Save to file
        with open(filepath, 'w') as f:
            f.write(full_code)
        
        self.generated_tools[pattern_key] = {
            'filepath': filepath,
            'class_name': class_name
        }
        
        print(f"✓ Saved tool: {filepath}")
        return filepath
    
    def generate_and_save_all(
        self,
        tool_candidates: List[Dict]
    ) -> Dict[str, str]:
        """
        Generate and save tools for all candidates.
        
        Args:
            tool_candidates: List from ToolAnalyzer
            
        Returns:
            Dictionary mapping pattern_key to filepath
        """
        results = {}
        
        for i, candidate in enumerate(tool_candidates, 1):
            print(f"\n{'='*80}")
            print(f"Generating tool {i}/{len(tool_candidates)}: {candidate['pattern_name']}")
            print(f"{'='*80}")
            
            try:
                # Load full pattern data
                with open('patterns.json', 'r') as f:
                    patterns = json.load(f)
                
                pattern = patterns[candidate['pattern_key']]
                
                # Generate tool code
                tool_code, class_name = self.generate_tool(
                    pattern=pattern,
                    tool_type=candidate['tool_type'],
                    pattern_key=candidate['pattern_key']
                )
                
                # Save to file
                filepath = self.save_tool(
                    pattern_key=candidate['pattern_key'],
                    tool_code=tool_code,
                    class_name=class_name
                )
                
                results[candidate['pattern_key']] = filepath
                
                print(f"✓ Successfully generated {class_name}")
                
            except Exception as e:
                print(f"✗ Failed to generate tool for {candidate['pattern_name']}: {e}")
                continue
        
        return results

# Usage Example
if __name__ == '__main__':
    # Load tool candidates from Hour 6
    analyzer = ToolAnalyzer('patterns.json')
    candidates = analyzer.analyze_all_patterns()
    top_candidates = analyzer.get_top_candidates(3)
    
    # Generate tools
    generator = ToolCodeGenerator()
    generated_files = generator.generate_and_save_all(top_candidates)
    
    print("\n" + "="*80)
    print("GENERATION COMPLETE")
    print("="*80)
    print(f"Successfully generated {len(generated_files)} tools:")
    for pattern_key, filepath in generated_files.items():
        print(f"  ✓ {pattern_key}: {filepath}")
```

### Example Generated Tool

```python
# tools/generated_production_readiness.py
# Auto-generated tool
# Pattern: production_readiness
# Class: ProductionReadinessChecker
# Generated by: ToolCodeGenerator

from typing import Dict, List

class ProductionReadinessChecker:
    """
    Auto-generated tool for Production Readiness pattern.
    
    Analyzes code for production readiness including:
    - Unit tests
    - Error handling
    - Type hints
    - Documentation
    - Complexity analysis
    
    Usage:
        checker = ProductionReadinessChecker()
        result = checker.analyze(code_string)
        print(f"Score: {result['score']:.2f}")
    """
    
    def analyze(self, code: str) -> Dict:
        """
        Analyze code for production readiness.
        
        Args:
            code: Python code to analyze
            
        Returns:
            Dictionary with:
            - score: Overall score 0-1
            - checks: Individual check results
            - issues: List of problems found
            - suggestions: List of improvements
        """
        if not code or not isinstance(code, str):
            return {
                'score': 0.0,
                'checks': {},
                'issues': ['No code provided'],
                'suggestions': []
            }
        
        checks = {}
        issues = []
        suggestions = []
        
        # Check 1: Unit tests
        checks['has_tests'] = self._check_tests(code)
        if not checks['has_tests']:
            issues.append("No unit tests found")
            suggestions.append("Add test functions with 'def test_' prefix or use pytest")
        
        # Check 2: Error handling
        checks['has_error_handling'] = self._check_error_handling(code)
        if not checks['has_error_handling']:
            issues.append("No error handling found")
            suggestions.append("Add try/except blocks for operations that could fail")
        
        # Check 3: Type hints
        checks['has_type_hints'] = self._check_type_hints(code)
        if not checks['has_type_hints']:
            issues.append("No type hints found")
            suggestions.append("Add type hints: def func(arg: Type) -> ReturnType")
        
        # Check 4: Docstrings
        checks['has_docstrings'] = self._check_docstrings(code)
        if not checks['has_docstrings']:
            issues.append("No docstrings found")
            suggestions.append("Add docstrings with Args, Returns, and complexity notes")
        
        # Check 5: Complexity analysis
        checks['has_complexity_notes'] = self._check_complexity(code)
        if not checks['has_complexity_notes']:
            issues.append("No complexity analysis found")
            suggestions.append("Add complexity comments: # Time: O(n), Space: O(1)")
        
        # Calculate overall score
        score = sum(checks.values()) / len(checks)
        
        return {
            'score': score,
            'checks': checks,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _check_tests(self, code: str) -> bool:
        """Check if code includes tests."""
        test_indicators = [
            'def test_',
            'import pytest',
            'import unittest',
            'from unittest',
            'assert ',
            '@pytest.',
            'TestCase'
        ]
        return any(indicator in code for indicator in test_indicators)
    
    def _check_error_handling(self, code: str) -> bool:
        """Check if code includes error handling."""
        return 'try:' in code and 'except' in code
    
    def _check_type_hints(self, code: str) -> bool:
        """Check if code includes type hints."""
        # Look for function signature type hints
        return ' -> ' in code or (': ' in code and 'def ' in code)
    
    def _check_docstrings(self, code: str) -> bool:
        """Check if code includes docstrings."""
        return '"""' in code or "'''" in code
    
    def _check_complexity(self, code: str) -> bool:
        """Check if code includes complexity analysis."""
        complexity_indicators = [
            'O(',
            'Time:',
            'Space:',
            'Complexity:',
            'time complexity',
            'space complexity'
        ]
        return any(indicator in code for indicator in complexity_indicators)

# Example usage and testing
if __name__ == '__main__':
    checker = ProductionReadinessChecker()
    
    # Test with incomplete code
    sample_code_bad = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    result_bad = checker.analyze(sample_code_bad)
    print("Analysis of incomplete code:")
    print(f"Score: {result_bad['score']:.2f}")
    print(f"Issues ({len(result_bad['issues'])}):")
    for issue in result_bad['issues']:
        print(f"  ❌ {issue}")
    print(f"\nSuggestions ({len(result_bad['suggestions'])}):")
    for suggestion in result_bad['suggestions']:
        print(f"  💡 {suggestion}")
    
    # Test with complete code
    sample_code_good = """
def fibonacci(n: int) -> int:
    '''
    Calculate nth Fibonacci number.
    
    Args:
        n: Position in Fibonacci sequence
        
    Returns:
        The nth Fibonacci number
        
    Time: O(2^n)
    Space: O(n) from call stack
    '''
    try:
        if not isinstance(n, int) or n < 0:
            raise ValueError("n must be non-negative integer")
        
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)
    except RecursionError:
        raise ValueError("n too large, causing stack overflow")

def test_fibonacci():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(5) == 5
"""
    
    result_good = checker.analyze(sample_code_good)
    print("\n" + "="*80)
    print("Analysis of complete code:")
    print(f"Score: {result_good['score']:.2f}")
    print(f"Checks passed: {sum(result_good['checks'].values())}/{len(result_good['checks'])}")
```

### Deliverable
- `tool_generator.py` - Generation script
- `tools/generated_*.py` - 3 generated tool files

---

## Hour 8: Tool Registry & Dynamic Loading

### Goal
Build a registry that dynamically loads and manages generated tools.

### Implementation

```python
# tool_registry.py

import os
import importlib
import sys
from typing import Dict, Optional, Any
from pathlib import Path

class ToolRegistry:
    """
    Manages dynamically generated tools.
    
    Features:
    - Auto-discovery of generated tools
    - Dynamic import and instantiation
    - Tool execution with error handling
    - Registry metadata tracking
    """
    
    def __init__(self, tools_dir: str = 'tools'):
        self.tools_dir = tools_dir
        self.tools: Dict[str, Any] = {}
        self.tool_metadata: Dict[str, Dict] = {}
        
        # Add tools directory to Python path
        tools_path = os.path.abspath(tools_dir)
        if tools_path not in sys.path:
            sys.path.insert(0, tools_path)
        
        # Load all available tools
        self.discover_and_load_tools()
    
    def discover_and_load_tools(self) -> int:
        """
        Discover and load all generated tools from tools directory.
        
        Returns:
            Number of tools successfully loaded
        """
        if not os.path.exists(self.tools_dir):
            print(f"⚠️  Tools directory not found: {self.tools_dir}")
            return 0
        
        loaded_count = 0
        
        for filename in os.listdir(self.tools_dir):
            if filename.startswith('generated_') and filename.endswith('.py'):
                pattern_key = filename.replace('generated_', '').replace('.py', '')
                
                try:
                    self._load_tool(filename, pattern_key)
                    loaded_count += 1
                except Exception as e:
                    print(f"✗ Failed to load {filename}: {e}")
        
        print(f"\n✓ Loaded {loaded_count} tools from {self.tools_dir}")
        return loaded_count
    
    def _load_tool(self, filename: str, pattern_key: str):
        """
        Dynamically import and instantiate a tool.
        """
        module_name = filename.replace('.py', '')
        
        # Import module
        module = importlib.import_module(module_name)
        
        # Find the tool class (class with 'analyze' method)
        tool_class = None
        class_name = None
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # Check if it's a class with analyze method
            if (isinstance(attr, type) and 
                hasattr(attr, 'analyze') and 
                not attr_name.startswith('_')):
                tool_class = attr
                class_name = attr_name
                break
        
        if not tool_class:
            raise ValueError(f"No tool class found in {filename}")
        
        # Instantiate tool
        tool_instance = tool_class()
        
        # Register tool
        self.tools[pattern_key] = tool_instance
        self.tool_metadata[pattern_key] = {
            'module': module_name,
            'class_name': class_name,
            'filepath': os.path.join(self.tools_dir, filename)
        }
        
        print(f"✓ Loaded: {pattern_key} ({class_name})")
    
    def execute_tool(
        self,
        pattern_key: str,
        code: str,
        **kwargs
    ) -> Optional[Dict]:
        """
        Execute a tool if it exists.
        
        Args:
            pattern_key: Key of tool to execute
            code: Code to analyze
            **kwargs: Additional arguments for tool
            
        Returns:
            Tool analysis results or None if tool not found
        """
        if pattern_key not in self.tools:
            print(f"⚠️  Tool not found: {pattern_key}")
            return None
        
        try:
            tool = self.tools[pattern_key]
            result = tool.analyze(code, **kwargs)
            return result
        except Exception as e:
            print(f"✗ Tool execution failed for {pattern_key}: {e}")
            return {
                'score': 0.0,
                'checks': {},
                'issues': [f"Tool execution error: {str(e)}"],
                'suggestions': []
            }
    
    def get_tool(self, pattern_key: str) -> Optional[Any]:
        """Get tool instance by key."""
        return self.tools.get(pattern_key)
    
    def available_tools(self) -> list:
        """List all available tool keys."""
        return list(self.tools.keys())
    
    def tool_info(self, pattern_key: str) -> Optional[Dict]:
        """Get metadata for a specific tool."""
        return self.tool_metadata.get(pattern_key)
    
    def print_registry(self):
        """Print formatted registry information."""
        print("\n" + "="*80)
        print("TOOL REGISTRY")
        print("="*80)
        print(f"Tools directory: {self.tools_dir}")
        print(f"Tools loaded: {len(self.tools)}\n")
        
        if not self.tools:
            print("No tools available.")
            return
        
        for pattern_key, metadata in self.tool_metadata.items():
            print(f"🔧 {pattern_key}")
            print(f"   Class: {metadata['class_name']}")
            print(f"   File: {metadata['filepath']}")
            print()
    
    def reload_tool(self, pattern_key: str) -> bool:
        """
        Reload a specific tool (useful during development).
        """
        if pattern_key not in self.tool_metadata:
            print(f"⚠️  Tool not in registry: {pattern_key}")
            return False
        
        try:
            metadata = self.tool_metadata[pattern_key]
            filename = os.path.basename(metadata['filepath'])
            
            # Remove old instance
            del self.tools[pattern_key]
            del self.tool_metadata[pattern_key]
            
            # Reload module
            module_name = filename.replace('.py', '')
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            
            # Load tool again
            self._load_tool(filename, pattern_key)
            
            print(f"✓ Reloaded: {pattern_key}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to reload {pattern_key}: {e}")
            return False
    
    def reload_all(self) -> int:
        """
        Reload all tools (useful during development).
        
        Returns:
            Number of tools successfully reloaded
        """
        pattern_keys = list(self.tools.keys())
        success_count = 0
        
        for pattern_key in pattern_keys:
            if self.reload_tool(pattern_key):
                success_count += 1
        
        return success_count

# Usage Example
if __name__ == '__main__':
    # Create registry and load tools
    registry = ToolRegistry('tools')
    registry.print_registry()
    
    # Execute a tool
    sample_code = """
def add(a, b):
    return a + b
"""
    
    if 'production_readiness' in registry.available_tools():
        print("\n" + "="*80)
        print("TESTING: production_readiness tool")
        print("="*80)
        
        result = registry.execute_tool('production_readiness', sample_code)
        
        if result:
            print(f"\nScore: {result['score']:.2f}")
            print(f"\nChecks:")
            for check, passed in result['checks'].items():
                status = "✓" if passed else "✗"
                print(f"  {status} {check}: {passed}")
            
            if result['issues']:
                print(f"\nIssues found:")
                for issue in result['issues']:
                    print(f"  ❌ {issue}")
```

### Deliverable
- `tool_registry.py` - Registry system
- Loaded and tested tool instances

---

## Hour 9: Enhanced Agent with Tool Execution

### Goal
Integrate tools into the agent's response pipeline.

### Implementation

```python
# agent_with_tools.py

from agent import SelfEvolvingAgent
from tool_registry import ToolRegistry
from typing import Optional, Dict, List

class SelfEvolvingAgentWithTools(SelfEvolvingAgent):
    """
    Enhanced agent that executes tools before generating responses.
    
    Response Pipeline:
    1. Match patterns (from Phase 1)
    2. Identify relevant tools
    3. Execute tools on code
    4. Build prompt with tool results
    5. Generate final response
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.tool_registry = ToolRegistry()
        print(f"Agent initialized with {len(self.tool_registry.available_tools())} tools")
    
    def respond(
        self,
        query: str,
        code: Optional[str] = None,
        use_patterns: bool = True,
        use_tools: bool = True
    ) -> tuple[str, Dict]:
        """
        Enhanced response with tool execution.
        
        Args:
            query: User's question
            code: Optional code to analyze
            use_patterns: Whether to apply learned patterns
            use_tools: Whether to use auto-generated tools
            
        Returns:
            (response_text, metadata)
        """
        metadata = {
            'patterns_applied': [],
            'tools_executed': [],
            'tool_results': {},
            'execution_time_ms': 0
        }
        
        import time
        start_time = time.time()
        
        # Step 1: Pattern matching (from Phase 1)
        patterns = []
        if use_patterns:
            patterns = self.matcher.match(query)
            metadata['patterns_applied'] = self.matcher.get_pattern_names(patterns)
        
        # Step 2: Tool execution (NEW!)
        if use_tools and code:
            tool_results = self._execute_relevant_tools(query, code, patterns)
            metadata['tools_executed'] = list(tool_results.keys())
            metadata['tool_results'] = tool_results
        
        # Step 3: Build enhanced prompt
        system_prompt = self._build_prompt_with_tools(
            patterns=patterns,
            tool_results=metadata.get('tool_results', {})
        )
        
        # Step 4: Generate response
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": query}]
        )
        
        response_text = message.content[0].text
        
        metadata['execution_time_ms'] = int((time.time() - start_time) * 1000)
        
        return response_text, metadata
    
    def _execute_relevant_tools(
        self,
        query: str,
        code: str,
        patterns: List[Dict]
    ) -> Dict:
        """
        Determine which tools to run and execute them.
        
        Rules:
        - If query contains 'review'/'check'/'analyze' → run all analyzers
        - For each matched pattern, run corresponding tool if available
        - Always run production_readiness for code submissions
        """
        results = {}
        query_lower = query.lower()
        
        # Rule 1: Review-type queries run all tools
        if any(word in query_lower for word in ['review', 'check', 'analyze', 'assess']):
            for tool_key in self.tool_registry.available_tools():
                result = self.tool_registry.execute_tool(tool_key, code)
                if result:
                    results[tool_key] = result
        
        # Rule 2: Pattern-specific tools
        else:
            for pattern in patterns:
                pattern_key = self._pattern_to_tool_key(pattern['name'])
                if pattern_key in self.tool_registry.available_tools():
                    result = self.tool_registry.execute_tool(pattern_key, code)
                    if result:
                        results[pattern_key] = result
        
        return results
    
    def _pattern_to_tool_key(self, pattern_name: str) -> str:
        """
        Convert pattern name to tool key.
        
        Examples:
        - "Production Readiness Checker" -> "production_readiness"
        - "Gap Analysis & Completeness" -> "gap_analysis"
        """
        # Remove common suffixes
        name = pattern_name.lower()
        for suffix in [' checker', ' analyzer', ' & completeness', ' policing']:
            name = name.replace(suffix, '')
        
        # Convert to snake_case
        name = name.replace(' ', '_').replace('&', 'and')
        
        return name
    
    def _build_prompt_with_tools(
        self,
        patterns: List[Dict],
        tool_results: Dict
    ) -> str:
        """
        Build system prompt including tool analysis results.
        """
        # Start with base pattern prompt (from Phase 1)
        base_prompt = self._build_augmented_prompt(patterns) if patterns else \
                      "You are a coding assistant for Kartik."
        
        if not tool_results:
            return base_prompt
        
        # Add tool results section
        tool_section = "\n\n" + "="*80 + "\n"
        tool_section += "# AUTOMATED TOOL ANALYSIS RESULTS\n"
        tool_section += "="*80 + "\n\n"
        tool_section += "The following tools have analyzed the code:\n\n"
        
        for tool_name, result in tool_results.items():
            tool_section += f"## {tool_name.replace('_', ' ').title()}\n\n"
            
            # Overall score
            tool_section += f"**Score:** {result['score']:.2f}/1.00\n\n"
            
            # Checks passed/failed
            if result.get('checks'):
                passed = sum(result['checks'].values())
                total = len(result['checks'])
                tool_section += f"**Checks:** {passed}/{total} passed\n"
                
                for check_name, passed in result['checks'].items():
                    status = "✓" if passed else "✗"
                    tool_section += f"  {status} {check_name}\n"
                tool_section += "\n"
            
            # Issues found
            if result.get('issues'):
                tool_section += f"**Issues Found ({len(result['issues'])}):**\n"
                for issue in result['issues']:
                    tool_section += f"- {issue}\n"
                tool_section += "\n"
            
            # Suggestions
            if result.get('suggestions'):
                tool_section += f"**Suggestions ({len(result['suggestions'])}):**\n"
                for suggestion in result['suggestions']:
                    tool_section += f"- {suggestion}\n"
                tool_section += "\n"
            
            tool_section += "---\n\n"
        
        # Instructions for using tool results
        tool_section += """
# INSTRUCTIONS FOR USING TOOL RESULTS

1. **Incorporate tool findings** into your response
2. **Prioritize issues** by severity (failing checks are most critical)
3. **Explain suggestions** in context of the user's question
4. **Don't just list issues** - provide insight and guidance
5. **Reference specific checks** when giving feedback

Example: "The production readiness checker found that your code is missing error handling (score: 0.60). This is critical for production..."
"""
        
        return base_prompt + tool_section

# Usage Example
if __name__ == '__main__':
    agent = SelfEvolvingAgentWithTools()
    
    # Test code
    sample_code = """
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1
"""
    
    # Query without tools
    print("="*80)
    print("WITHOUT TOOLS")
    print("="*80)
    response_no_tools, metadata_no_tools = agent.respond(
        "Review this binary search implementation",
        code=sample_code,
        use_patterns=True,
        use_tools=False
    )
    print(f"\nPatterns applied: {metadata_no_tools['patterns_applied']}")
    print(f"\nResponse:\n{response_no_tools[:300]}...")
    
    # Query with tools
    print("\n" + "="*80)
    print("WITH TOOLS")
    print("="*80)
    response_with_tools, metadata_with_tools = agent.respond(
        "Review this binary search implementation",
        code=sample_code,
        use_patterns=True,
        use_tools=True
    )
    print(f"\nPatterns applied: {metadata_with_tools['patterns_applied']}")
    print(f"Tools executed: {metadata_with_tools['tools_executed']}")
    print(f"\nTool results summary:")
    for tool_name, result in metadata_with_tools['tool_results'].items():
        print(f"  - {tool_name}: score {result['score']:.2f}, {len(result['issues'])} issues")
    print(f"\nResponse:\n{response_with_tools[:300]}...")
    print(f"\nExecution time: {metadata_with_tools['execution_time_ms']}ms")
```

### Deliverable
- `agent_with_tools.py` - Enhanced agent
- Tested with tool execution

---

## Hour 9.5: Demo Interface with Tools

### Goal
Create Streamlit demo showcasing tool execution.

### Implementation

```python
# demo_with_tools.py

import streamlit as st
from agent_with_tools import SelfEvolvingAgentWithTools
import json

st.set_page_config(
    page_title="Self-Evolving Agent with Tools",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize agent
@st.cache_resource
def get_agent():
    return SelfEvolvingAgentWithTools()

agent = get_agent()

# Sidebar: Tool Registry
st.sidebar.title("🔧 Auto-Generated Tools")
st.sidebar.write(f"**{len(agent.tool_registry.available_tools())} tools available:**")

for tool_key in agent.tool_registry.available_tools():
    tool_info = agent.tool_registry.tool_info(tool_key)
    with st.sidebar.expander(f"📦 {tool_key}"):
        st.write(f"**Class:** `{tool_info['class_name']}`")
        st.write(f"**File:** `{tool_info['filepath']}`")

# Main interface
st.title("🤖 Self-Evolving Agent v2: Architectural Changes")
st.write("An agent that generates and executes tools")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Code Review with Tools",
    "Before/After Comparison",
    "Tool Generation Log",
    "Architecture Diagram"
])

# Tab 1: Interactive code review
with tab1:
    st.header("Code Review with Auto-Generated Tools")
    
    # Sample code examples
    code_examples = {
        "Simple function": """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)""",
        
        "With some improvements": """def fibonacci(n: int) -> int:
    '''Calculate nth Fibonacci number.'''
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def test_fibonacci():
    assert fibonacci(5) == 5""",
        
        "Production ready": """def fibonacci(n: int) -> int:
    '''
    Calculate nth Fibonacci number.
    
    Time: O(2^n), Space: O(n)
    '''
    try:
        if not isinstance(n, int) or n < 0:
            raise ValueError("n must be non-negative")
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)
    except RecursionError:
        raise ValueError("n too large")

def test_fibonacci():
    assert fibonacci(0) == 0
    assert fibonacci(5) == 5"""
    }
    
    selected_example = st.selectbox("Choose example or write your own:", list(code_examples.keys()) + ["Custom"])
    
    if selected_example == "Custom":
        code_input = st.text_area("Enter code to review:", height=300)
    else:
        code_input = st.text_area(
            "Enter code to review:",
            value=code_examples[selected_example],
            height=300
        )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        use_tools = st.checkbox("Use tools", value=True)
    
    if st.button("🔍 Review Code", type="primary"):
        if not code_input:
            st.warning("Please enter some code to review")
        else:
            with st.spinner("Analyzing code..."):
                response, metadata = agent.respond(
                    "Review this code",
                    code=code_input,
                    use_patterns=True,
                    use_tools=use_tools
                )
            
            # Show execution metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Patterns Applied", len(metadata['patterns_applied']))
            with col2:
                st.metric("Tools Executed", len(metadata['tools_executed']))
            with col3:
                st.metric("Execution Time", f"{metadata['execution_time_ms']}ms")
            
            # Show tool results
            if metadata['tools_executed']:
                st.subheader("🔧 Tool Analysis Results")
                
                for tool_name, result in metadata['tool_results'].items():
                    with st.expander(f"📊 {tool_name.replace('_', ' ').title()}", expanded=True):
                        # Score with progress bar
                        st.metric("Overall Score", f"{result['score']:.2f}")
                        st.progress(result['score'])
                        
                        # Checks
                        if result.get('checks'):
                            st.write("**Checks:**")
                            cols = st.columns(2)
                            for i, (check, passed) in enumerate(result['checks'].items()):
                                col = cols[i % 2]
                                with col:
                                    status = "✅" if passed else "❌"
                                    st.write(f"{status} {check}")
                        
                        # Issues and suggestions
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if result.get('issues'):
                                st.write("**Issues:**")
                                for issue in result['issues']:
                                    st.error(issue, icon="🚨")
                        
                        with col2:
                            if result.get('suggestions'):
                                st.write("**Suggestions:**")
                                for suggestion in result['suggestions']:
                                    st.info(suggestion, icon="💡")
            
            # Show Claude's response
            st.subheader("🤖 Claude's Response")
            st.markdown(response)

# Tab 2: Before/After comparison
with tab2:
    st.header("Before Tools vs After Tools")
    
    st.write("""
    See how the agent's responses improve when tools are available.
    """)
    
    comparison_code = """def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)"""
    
    st.code(comparison_code, language='python')
    
    if st.button("Generate Comparison"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("❌ Without Tools")
            st.caption("Pattern-based prompting only")
            
            with st.spinner("Generating..."):
                response_no_tools, metadata_no_tools = agent.respond(
                    "Review this code",
                    code=comparison_code,
                    use_patterns=True,
                    use_tools=False
                )
            
            st.info(f"Patterns: {len(metadata_no_tools['patterns_applied'])}")
            st.markdown(response_no_tools)
        
        with col2:
            st.subheader("✅ With Tools")
            st.caption("Pattern + automated tool analysis")
            
            with st.spinner("Analyzing..."):
                response_with_tools, metadata_with_tools = agent.respond(
                    "Review this code",
                    code=comparison_code,
                    use_patterns=True,
                    use_tools=True
                )
            
            st.success(f"Patterns: {len(metadata_with_tools['patterns_applied'])}, Tools: {len(metadata_with_tools['tools_executed'])}")
            
            # Show tool scores
            if metadata_with_tools['tool_results']:
                for tool_name, result in metadata_with_tools['tool_results'].items():
                    st.metric(
                        tool_name.replace('_', ' ').title(),
                        f"{result['score']:.2f}",
                        f"{len(result['issues'])} issues"
                    )
            
            st.markdown(response_with_tools)

# Tab 3: Tool generation log
with tab3:
    st.header("Tool Generation Process")
    
    st.write("""
    This shows how tools were automatically generated from your patterns.
    """)
    
    st.subheader("Pattern → Tool Mapping")
    
    # Show which patterns became tools
    for tool_key in agent.tool_registry.available_tools():
        tool_info = agent.tool_registry.tool_info(tool_key)
        
        with st.expander(f"🔧 {tool_key}", expanded=False):
            st.write(f"**Generated Class:** `{tool_info['class_name']}`")
            st.write(f"**File Location:** `{tool_info['filepath']}`")
            
            st.write("**Generation Steps:**")
            st.write("1. Pattern analyzed for automation potential")
            st.write("2. Claude API generated tool code")
            st.write("3. Code validated and saved")
            st.write("4. Tool loaded into registry")
            
            # Show code preview
            st.write("**Code Preview:**")
            try:
                with open(tool_info['filepath'], 'r') as f:
                    code = f.read()
                    # Show first 20 lines
                    preview = '\n'.join(code.split('\n')[:20])
                    st.code(preview + '\n...', language='python')
            except:
                st.write("Could not load file")

# Tab 4: Architecture diagram
with tab4:
    st.header("System Architecture")
    
    st.write("""
    The agent's architecture has evolved to include a tool execution layer.
    """)
    
    st.subheader("Phase 1: Pattern-Based Prompting")
    st.code("""
User Query → Pattern Matcher → Augmented Prompt → Claude API → Response
                    ↓
            Pattern Database
            (10 patterns)
    """)
    st.write("✓ Patterns applied via prompts")
    st.write("✗ Architecture is static")
    
    st.divider()
    
    st.subheader("Phase 1 + Level 2: Architectural Changes")
    st.code("""
User Query → Pattern Matcher → Tool Executor → Augmented Prompt → Claude API → Response
                    ↓                 ↓
            Pattern Database    Tool Registry
            (10 patterns)    (3 auto-generated tools)
                                      ↓
                            [ProductionReadinessChecker]
                            [GapAnalysisEvaluator]
                            [PrecisionValidator]
    """)
    st.write("✓ Patterns applied via prompts")
    st.write("✓ **Tools execute automated checks**")
    st.write("✓ **Architecture evolves** (new capabilities added)")
    
    st.divider()
    
    st.subheader("Key Innovation")
    st.info("""
    The agent doesn't just remember preferences—it **creates code** to automate them.
    
    When you repeatedly ask "What about tests?", the agent:
    1. Detects this repetitive pattern
    2. Generates a TestCoverageAnalyzer tool
    3. Adds it to the tool registry
    4. Automatically runs it on future code
    
    **This is true self-evolution: the agent improves its own architecture.**
    """)

# Footer
st.markdown("---")
st.caption("Self-Evolving Agent | Phase 1 CRAWL + Level 2 Architectural Changes")
```

### Deliverable
- `demo_with_tools.py` - Complete demo interface
- 4-tab interface showing tools in action

---

## CRAWL Phase Complete Summary

### What Was Added to Level 1 CRAWL

| Component | Time | Purpose |
|-----------|------|---------|
| **Tool Analyzer** | 1h | Identify tool-worthy patterns |
| **Tool Generator** | 1.5h | Generate Python tools via Claude API |
| **Tool Registry** | 1h | Manage and execute tools |
| **Enhanced Agent** | 0.5h | Integrate tools into response pipeline |
| **Demo with Tools** | 0.5h | Showcase tool execution |

**Total Time Added:** +4 hours (9.5 hours total)

### New Files Created

```
project/
├── tool_analyzer.py          # Pattern → tool opportunity analysis
├── tool_generator.py          # Claude API → Python tool code
├── tool_registry.py           # Dynamic tool loading & execution
├── agent_with_tools.py        # Enhanced agent
├── demo_with_tools.py         # Demo interface
└── tools/
    ├── generated_production_readiness.py
    ├── generated_gap_analysis.py
    └── generated_precision_policing.py
```

### Capabilities Demonstrated

✅ Agent analyzes patterns for automation potential
✅ Agent generates Python tools using Claude API
✅ Agent executes tools automatically before responding
✅ Agent incorporates tool results into responses
✅ Demo shows clear before/after with tools

### Key Insight

**The agent doesn't just learn preferences—it creates infrastructure.**

When you repeatedly ask "What about error handling?", instead of just mentioning it in responses, the agent:
1. Recognizes the pattern
2. Generates an `ErrorHandlingAnalyzer` tool
3. Adds it to the registry
4. Automatically runs it on all future code

**This is architectural evolution.**

---

# Incremental Additions: WALK Phase

**Base:** Level 1 WALK (8-12 hours - pattern + examples)
**Addition:** Example-driven tool generation (+3 hours)
**Total:** 11-15 hours

---

## Hour 10-11: Conversation Pattern Detection

### Goal
Analyze real conversations to find repetitive requests that should become tools.

### Why This Matters

**CRAWL approach:** "This pattern seems tool-worthy" (static analysis)
**WALK approach:** "User asked for this 47 times" (empirical data)

The WALK phase learns **when** to create tools, not just **how**.

### Implementation

```python
# conversation_pattern_detector.py

from conversation_db import ConversationDatabase
from typing import List, Dict, Tuple
from collections import Counter
import re

class ConversationPatternDetector:
    """
    Analyzes conversation history to detect repetitive requests.
    
    This goes beyond static pattern analysis to find empirical evidence
    of what users repeatedly ask for.
    """
    
    def __init__(self, conversation_db: ConversationDatabase):
        self.conversation_db = conversation_db
        self.repetitive_patterns = []
        self.follow_up_questions = []
    
    def analyze_conversations(self) -> Dict:
        """
        Main analysis pipeline.
        
        Returns:
            Dictionary with:
            - repetitive_requests: Things asked 3+ times
            - tool_suggestions: Recommended tools to create
            - frequency_map: Full frequency analysis
        """
        # Step 1: Extract all follow-up questions
        self.follow_up_questions = self._extract_all_follow_ups()
        
        # Step 2: Normalize and count
        frequency_map = self._count_normalized_questions()
        
        # Step 3: Filter for repetitive (3+ occurrences)
        self.repetitive_patterns = self._filter_repetitive(frequency_map)
        
        # Step 4: Generate tool suggestions
        tool_suggestions = self._generate_tool_suggestions()
        
        return {
            'total_conversations': len(self.conversation_db.conversations),
            'total_follow_ups': len(self.follow_up_questions),
            'repetitive_requests': self.repetitive_patterns,
            'tool_suggestions': tool_suggestions,
            'frequency_map': frequency_map
        }
    
    def _extract_all_follow_ups(self) -> List[Dict]:
        """
        Extract follow-up questions from all conversations.
        
        A "follow-up" is a user message after the first exchange that:
        - Starts with "What about", "How about", "Did you consider"
        - Asks for something missing from previous response
        """
        follow_ups = []
        
        for conv_id, conv in enumerate(self.conversation_db.conversations):
            messages = conv['messages']
            
            # Start from 3rd message (after initial Q&A)
            for i in range(2, len(messages)):
                if messages[i]['role'] != 'user':
                    continue
                
                content = messages[i]['content']
                
                # Detect follow-up patterns
                if self._is_follow_up_question(content):
                    follow_ups.append({
                        'conversation_id': conv_id,
                        'message_index': i,
                        'content': content,
                        'context': self._extract_context(messages, i)
                    })
        
        return follow_ups
    
    def _is_follow_up_question(self, message: str) -> bool:
        """
        Detect if message is a follow-up question.
        """
        follow_up_patterns = [
            r'^what about',
            r'^how about',
            r'^did you consider',
            r'^what if we need',
            r'^but what if',
            r"^you didn't mention",
            r"^i don't see",
            r"^where(?:'s| is) the",
            r"^shouldn't (?:you|we|it)",
        ]
        
        message_lower = message.lower().strip()
        
        return any(re.match(pattern, message_lower) for pattern in follow_up_patterns)
    
    def _extract_context(self, messages: List[Dict], index: int) -> str:
        """
        Extract context around a follow-up question.
        """
        # Get previous assistant message
        for i in range(index - 1, -1, -1):
            if messages[i]['role'] == 'assistant':
                return messages[i]['content'][:200]
        
        return ""
    
    def _count_normalized_questions(self) -> Counter:
        """
        Normalize follow-up questions and count occurrences.
        
        Examples:
        - "What about tests?" → "tests"
        - "Did you consider error handling?" → "error_handling"
        - "What about type hints?" → "type_hints"
        """
        normalized_questions = []
        
        for follow_up in self.follow_up_questions:
            normalized = self._normalize_question(follow_up['content'])
            if normalized:
                normalized_questions.append(normalized)
        
        return Counter(normalized_questions)
    
    def _normalize_question(self, question: str) -> str:
        """
        Extract the core topic from a follow-up question.
        
        Examples:
        - "What about tests?" → "tests"
        - "Did you consider error handling?" → "error_handling"
        - "How about adding type hints?" → "type_hints"
        """
        question_lower = question.lower()
        
        # Remove common question prefixes
        for prefix in ['what about', 'how about', 'did you consider', 
                       'what if we need', 'but what if', "you didn't mention",
                       "i don't see", "where's the", "where is the",
                       "shouldn't you", "shouldn't we"]:
            if question_lower.startswith(prefix):
                # Extract everything after prefix
                remainder = question_lower[len(prefix):].strip()
                
                # Remove question marks and clean up
                remainder = remainder.rstrip('?').strip()
                
                # Convert to snake_case identifier
                # "error handling" → "error_handling"
                remainder = remainder.replace(' ', '_').replace('-', '_')
                
                # Remove articles and prepositions
                for word in ['the', 'a', 'an', 'any', 'about', 'for']:
                    remainder = remainder.replace(f'_{word}_', '_')
                    remainder = remainder.replace(f'{word}_', '')
                
                return remainder
        
        return ""
    
    def _filter_repetitive(self, frequency_map: Counter, threshold: int = 3) -> List[Dict]:
        """
        Filter for questions asked threshold or more times.
        """
        repetitive = []
        
        for question, count in frequency_map.most_common():
            if count >= threshold:
                # Find example conversations
                examples = self._find_example_conversations(question)
                
                repetitive.append({
                    'question': question,
                    'count': count,
                    'percentage': (count / len(self.follow_up_questions)) * 100 if self.follow_up_questions else 0,
                    'example_conversations': examples[:3]  # Top 3 examples
                })
        
        return repetitive
    
    def _find_example_conversations(self, normalized_question: str) -> List[int]:
        """
        Find conversation IDs containing this question.
        """
        conversation_ids = []
        
        for follow_up in self.follow_up_questions:
            if self._normalize_question(follow_up['content']) == normalized_question:
                conv_id = follow_up['conversation_id']
                if conv_id not in conversation_ids:
                    conversation_ids.append(conv_id)
        
        return conversation_ids
    
    def _generate_tool_suggestions(self) -> List[Dict]:
        """
        Generate tool suggestions from repetitive patterns.
        """
        tool_suggestions = []
        
        # Mapping from question topics to tool capabilities
        tool_mappings = {
            'tests': {
                'name': 'TestCoverageAnalyzer',
                'capability': 'Analyze test coverage and suggest missing tests',
                'type': 'analyzer'
            },
            'test': {
                'name': 'TestCoverageAnalyzer',
                'capability': 'Analyze test coverage and suggest missing tests',
                'type': 'analyzer'
            },
            'error_handling': {
                'name': 'ErrorHandlingChecker',
                'capability': 'Identify functions needing error handling',
                'type': 'checker'
            },
            'errors': {
                'name': 'ErrorHandlingChecker',
                'capability': 'Identify functions needing error handling',
                'type': 'checker'
            },
            'type_hints': {
                'name': 'TypeHintValidator',
                'capability': 'Check for missing or incorrect type hints',
                'type': 'validator'
            },
            'typing': {
                'name': 'TypeHintValidator',
                'capability': 'Check for missing or incorrect type hints',
                'type': 'validator'
            },
            'edge_cases': {
                'name': 'EdgeCaseGenerator',
                'capability': 'Generate list of edge cases for algorithms',
                'type': 'generator'
            },
            'documentation': {
                'name': 'DocumentationChecker',
                'capability': 'Verify completeness of docstrings',
                'type': 'checker'
            },
            'docs': {
                'name': 'DocumentationChecker',
                'capability': 'Verify completeness of docstrings',
                'type': 'checker'
            },
            'performance': {
                'name': 'PerformanceAnalyzer',
                'capability': 'Detect performance anti-patterns',
                'type': 'analyzer'
            },
            'complexity': {
                'name': 'ComplexityAnalyzer',
                'capability': 'Calculate and validate complexity claims',
                'type': 'analyzer'
            }
        }
        
        for pattern in self.repetitive_patterns:
            question = pattern['question']
            
            # Check if we have a mapping for this question
            if question in tool_mappings:
                tool_info = tool_mappings[question]
                
                tool_suggestions.append({
                    'name': tool_info['name'],
                    'reason': f"User asked about '{question}' {pattern['count']} times ({pattern['percentage']:.1f}% of follow-ups)",
                    'capability': tool_info['capability'],
                    'type': tool_info['type'],
                    'priority': pattern['count'],  # Higher count = higher priority
                    'example_conversations': pattern['example_conversations']
                })
        
        # Sort by priority (count)
        tool_suggestions.sort(key=lambda x: x['priority'], reverse=True)
        
        # Deduplicate by name
        seen_names = set()
        unique_suggestions = []
        for suggestion in tool_suggestions:
            if suggestion['name'] not in seen_names:
                seen_names.add(suggestion['name'])
                unique_suggestions.append(suggestion)
        
        return unique_suggestions
    
    def print_analysis_report(self, analysis: Dict):
        """
        Print human-readable analysis report.
        """
        print("\n" + "="*80)
        print("CONVERSATION PATTERN ANALYSIS")
        print("="*80)
        
        print(f"\nAnalyzed {analysis['total_conversations']} conversations")
        print(f"Found {analysis['total_follow_ups']} follow-up questions")
        print(f"Identified {len(analysis['repetitive_requests'])} repetitive patterns (asked 3+ times)")
        
        print("\n" + "-"*80)
        print("REPETITIVE REQUESTS")
        print("-"*80)
        
        for i, pattern in enumerate(analysis['repetitive_requests'], 1):
            print(f"\n{i}. '{pattern['question']}'")
            print(f"   Asked {pattern['count']} times ({pattern['percentage']:.1f}% of all follow-ups)")
            print(f"   Example conversations: {pattern['example_conversations']}")
        
        print("\n" + "-"*80)
        print("TOOL SUGGESTIONS")
        print("-"*80)
        print(f"\nGenerated {len(analysis['tool_suggestions'])} tool suggestions:\n")
        
        for i, suggestion in enumerate(analysis['tool_suggestions'], 1):
            print(f"{i}. {suggestion['name']} ({suggestion['type']})")
            print(f"   Reason: {suggestion['reason']}")
            print(f"   Capability: {suggestion['capability']}")
            print(f"   Priority: {suggestion['priority']}")
            print()

# Usage Example
if __name__ == '__main__':
    # Load conversation database
    conversation_db = ConversationDatabase('conversations.json')
    
    # Run analysis
    detector = ConversationPatternDetector(conversation_db)
    analysis = detector.analyze_conversations()
    
    # Print report
    detector.print_analysis_report(analysis)
    
    # Save results
    import json
    with open('pattern_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print("\n✓ Analysis saved to pattern_analysis.json")
```

### Expected Output

```
================================================================================
CONVERSATION PATTERN ANALYSIS
================================================================================

Analyzed 19 conversations
Found 127 follow-up questions
Identified 5 repetitive patterns (asked 3+ times)

--------------------------------------------------------------------------------
REPETITIVE REQUESTS
--------------------------------------------------------------------------------

1. 'tests'
   Asked 47 times (37.0% of all follow-ups)
   Example conversations: [2, 5, 8]

2. 'error_handling'
   Asked 31 times (24.4% of all follow-ups)
   Example conversations: [1, 3, 7]

3. 'type_hints'
   Asked 23 times (18.1% of all follow-ups)
   Example conversations: [4, 6, 11]

4. 'edge_cases'
   Asked 18 times (14.2% of all follow-ups)
   Example conversations: [9, 12, 15]

5. 'documentation'
   Asked 8 times (6.3% of all follow-ups)
   Example conversations: [10, 13, 16]

--------------------------------------------------------------------------------
TOOL SUGGESTIONS
--------------------------------------------------------------------------------

Generated 5 tool suggestions:

1. TestCoverageAnalyzer (analyzer)
   Reason: User asked about 'tests' 47 times (37.0% of follow-ups)
   Capability: Analyze test coverage and suggest missing tests
   Priority: 47

2. ErrorHandlingChecker (checker)
   Reason: User asked about 'error_handling' 31 times (24.4% of follow-ups)
   Capability: Identify functions needing error handling
   Priority: 31

3. TypeHintValidator (validator)
   Reason: User asked about 'type_hints' 23 times (18.1% of follow-ups)
   Capability: Check for missing or incorrect type hints
   Priority: 23

4. EdgeCaseGenerator (generator)
   Reason: User asked about 'edge_cases' 18 times (14.2% of follow-ups)
   Capability: Generate list of edge cases for algorithms
   Priority: 18

5. DocumentationChecker (checker)
   Reason: User asked about 'documentation' 8 times (6.3% of follow-ups)
   Capability: Verify completeness of docstrings
   Priority: 8

✓ Analysis saved to pattern_analysis.json
```

### Deliverable
- `conversation_pattern_detector.py` - Analysis script
- `pattern_analysis.json` - Analysis results
- Report showing empirical tool suggestions

---

## Hour 12: Example-Based Tool Generation

### Goal
Generate tools using actual conversation examples (not just pattern descriptions).

### Key Difference

**CRAWL:** "Here's a pattern description. Generate a tool."
**WALK:** "Here are 3 conversations where user asked for tests. Generate a tool that matches what they wanted."

This produces tools that better match actual usage patterns.

### Implementation

```python
# example_based_tool_generator.py

import anthropic
from conversation_db import ConversationDatabase
from typing import List, Dict, Optional
import json

class ExampleBasedToolGenerator:
    """
    Generates tools using real conversation examples.
    
    Instead of just pattern descriptions, this uses actual examples
    of user requests and Claude's responses to create tools that
    match real usage patterns.
    """
    
    def __init__(
        self,
        conversation_db: ConversationDatabase,
        api_key: Optional[str] = None
    ):
        self.conversation_db = conversation_db
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"
    
    def generate_tool_from_examples(
        self,
        tool_suggestion: Dict
    ) -> tuple[str, str]:
        """
        Generate tool using conversation examples.
        
        Args:
            tool_suggestion: Dictionary from ConversationPatternDetector
                containing name, capability, example_conversations, etc.
        
        Returns:
            (tool_code, class_name)
        """
        # Extract relevant conversations
        example_convs = self._get_example_conversations(
            tool_suggestion['example_conversations']
        )
        
        # Build generation prompt with examples
        generation_prompt = self._build_example_based_prompt(
            tool_name=tool_suggestion['name'],
            capability=tool_suggestion['capability'],
            tool_type=tool_suggestion['type'],
            example_conversations=example_convs,
            reason=tool_suggestion['reason']
        )
        
        # Generate tool code
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.3,
            system="""You are an expert at creating Python tools that automate repetitive tasks.
            
You analyze conversation examples to understand:
- What the user repeatedly asks for
- How responses should be structured
- What checks or analysis should be automated

Generate production-quality tools with proper error handling, type hints, and documentation.""",
            messages=[{"role": "user", "content": generation_prompt}]
        )
        
        tool_code = message.content[0].text
        
        # Extract code
        if "```python" in tool_code:
            tool_code = tool_code.split("```python")[1].split("```")[0].strip()
        
        return tool_code, tool_suggestion['name']
    
    def _get_example_conversations(
        self,
        conversation_ids: List[int]
    ) -> List[Dict]:
        """
        Retrieve full conversation objects by ID.
        """
        example_convs = []
        
        for conv_id in conversation_ids:
            if conv_id < len(self.conversation_db.conversations):
                conv = self.conversation_db.conversations[conv_id]
                example_convs.append(conv)
        
        return example_convs
    
    def _build_example_based_prompt(
        self,
        tool_name: str,
        capability: str,
        tool_type: str,
        example_conversations: List[Dict],
        reason: str
    ) -> str:
        """
        Build prompt including conversation examples.
        """
        prompt = f"""# Tool Generation Request

## Context
{reason}

I need a tool that automates this request.

## Tool Specification
**Name:** {tool_name}
**Type:** {tool_type}
**Capability:** {capability}

## Real Conversation Examples

Here are actual conversations showing what the user asks for:

"""
        # Add conversation examples
        for i, conv in enumerate(example_conversations[:3], 1):
            prompt += f"### Example {i}:\n\n"
            prompt += self._format_conversation_example(conv)
            prompt += "\n" + "-"*80 + "\n\n"
        
        prompt += """
## Generation Requirements

Based on these examples, generate a Python tool that:

1. **Automates the checks** the user repeatedly asks for
2. **Returns structured results** similar to what Claude provides
3. **Matches the user's expectations** from the examples

**Class Structure:**
```python
class {tool_name}:
    '''
    Auto-generated tool from conversation patterns.
    
    Analyzes code for: {capability}
    '''
    
    def analyze(self, code: str) -> dict:
        '''
        Args:
            code: Python code to analyze
            
        Returns:
            {{
                'score': float (0-1),
                'checks': dict,
                'issues': list,
                'suggestions': list
            }}
        '''
        # Implementation that matches user expectations from examples
```

**Implementation Guidelines:**
- Look at what the user asked for in the examples
- Implement checks that detect those specific concerns
- Structure output similar to how Claude responds
- Include comprehensive error handling
- Add type hints and docstrings

Generate ONLY the Python code.
""".format(tool_name=tool_name, capability=capability)
        
        return prompt
    
    def _format_conversation_example(self, conversation: Dict) -> str:
        """
        Format a conversation for inclusion in prompt.
        """
        formatted = ""
        
        messages = conversation.get('messages', [])
        
        # Show first user question
        for i, msg in enumerate(messages):
            if msg['role'] == 'user':
                formatted += f"**User:** {msg['content'][:300]}\n\n"
                
                # Find next assistant response
                if i + 1 < len(messages) and messages[i + 1]['role'] == 'assistant':
                    formatted += f"**Assistant:** {messages[i + 1]['content'][:300]}...\n\n"
                
                # Look for follow-up about the tool topic
                for j in range(i + 2, len(messages)):
                    if messages[j]['role'] == 'user':
                        user_msg = messages[j]['content'].lower()
                        
                        # Check if this is a relevant follow-up
                        if any(word in user_msg for word in [
                            'what about', 'how about', 'did you',
                            "you didn't", "i don't see"
                        ]):
                            formatted += f"**User Follow-up:** {messages[j]['content'][:200]}\n\n"
                            
                            # Get assistant's response to follow-up
                            if j + 1 < len(messages) and messages[j + 1]['role'] == 'assistant':
                                formatted += f"**Assistant:** {messages[j + 1]['content'][:200]}...\n\n"
                            
                            break  # One follow-up per example is enough
                
                break  # One exchange per example
        
        return formatted
    
    def generate_all_suggested_tools(
        self,
        tool_suggestions: List[Dict],
        output_dir: str = 'tools'
    ) -> Dict[str, str]:
        """
        Generate all suggested tools from conversation analysis.
        
        Returns:
            Dictionary mapping tool_name to filepath
        """
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        results = {}
        
        for i, suggestion in enumerate(tool_suggestions, 1):
            print(f"\n{'='*80}")
            print(f"Generating tool {i}/{len(tool_suggestions)}: {suggestion['name']}")
            print(f"{'='*80}")
            print(f"Reason: {suggestion['reason']}")
            
            try:
                # Generate tool
                tool_code, tool_name = self.generate_tool_from_examples(suggestion)
                
                # Save to file
                filename = f"generated_{suggestion['name'].lower()}.py"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w') as f:
                    f.write(f"# Auto-generated from conversation examples\n")
                    f.write(f"# Pattern: User asked about '{suggestion['reason'].split(\"'\")[1]}'\n")
                    f.write(f"# Priority: {suggestion['priority']}\n\n")
                    f.write(tool_code)
                
                results[tool_name] = filepath
                print(f"✓ Successfully generated and saved: {filepath}")
                
            except Exception as e:
                print(f"✗ Failed to generate {suggestion['name']}: {e}")
                continue
        
        return results

# Usage Example
if __name__ == '__main__':
    # Load conversation database and pattern analysis
    conversation_db = ConversationDatabase('conversations.json')
    
    with open('pattern_analysis.json', 'r') as f:
        pattern_analysis = json.load(f)
    
    tool_suggestions = pattern_analysis['tool_suggestions']
    
    # Generate tools from examples
    generator = ExampleBasedToolGenerator(conversation_db)
    generated_tools = generator.generate_all_suggested_tools(
        tool_suggestions=tool_suggestions[:3],  # Top 3
        output_dir='tools'
    )
    
    print("\n" + "="*80)
    print("GENERATION COMPLETE")
    print("="*80)
    print(f"\nSuccessfully generated {len(generated_tools)} tools:")
    for tool_name, filepath in generated_tools.items():
        print(f"  ✓ {tool_name}: {filepath}")
```

### Example Generated Tool (From Conversations)

```python
# tools/generated_testcoverageanalyzer.py
# Auto-generated from conversation examples
# Pattern: User asked about 'tests'
# Priority: 47

from typing import Dict, List, Set
import ast
import re

class TestCoverageAnalyzer:
    """
    Auto-generated tool from conversation patterns.
    
    User repeatedly asked "What about tests?" across 47 conversations.
    This tool automates test coverage analysis based on those requests.
    """
    
    def analyze(self, code: str) -> Dict:
        """
        Analyze test coverage based on user's repeated requests.
        
        Checks learned from conversation examples:
        - Are there any test functions? (asked in 100% of cases)
        - Do tests cover edge cases? (asked in 73% of cases)
        - Are tests using pytest/unittest? (asked in 54% of cases)
        - Do tests check error conditions? (asked in 41% of cases)
        
        Args:
            code: Python code to analyze
            
        Returns:
            {
                'score': 0-1 overall test coverage score,
                'checks': individual check results,
                'issues': list of missing test aspects,
                'suggestions': specific improvements based on user patterns
            }
        """
        if not code:
            return self._empty_result()
        
        # Parse code
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                'score': 0.0,
                'checks': {},
                'issues': ['Code has syntax errors, cannot analyze'],
                'suggestions': ['Fix syntax errors first']
            }
        
        # Extract functions and test functions
        functions = self._extract_functions(tree)
        test_functions = self._extract_test_functions(tree)
        
        # Run checks (based on conversation patterns)
        checks = {}
        issues = []
        suggestions = []
        
        # Check 1: Are there ANY tests? (Most common request)
        checks['has_tests'] = len(test_functions) > 0
        if not checks['has_tests']:
            issues.append("No test functions found")
            suggestions.append("Add test functions with 'def test_' prefix or use pytest")
        
        # Check 2: Test framework used? (User preference from examples)
        checks['uses_test_framework'] = self._check_test_framework(code)
        if not checks['uses_test_framework']:
            suggestions.append("Consider using pytest or unittest framework")
        
        # Check 3: Edge cases tested? (Frequently asked)
        checks['tests_edge_cases'] = self._check_edge_case_tests(code, test_functions)
        if not checks['tests_edge_cases']:
            issues.append("Tests don't appear to cover edge cases")
            suggestions.append("Add tests for: empty input, None, boundary values, invalid types")
        
        # Check 4: Error conditions tested? (Asked in many conversations)
        checks['tests_error_conditions'] = self._check_error_tests(test_functions)
        if not checks['tests_error_conditions']:
            issues.append("No tests for error conditions/exceptions")
            suggestions.append("Add tests that verify proper error handling using pytest.raises or assertRaises")
        
        # Check 5: Coverage ratio (if functions exist)
        if functions:
            coverage_ratio = len(test_functions) / len(functions)
            checks['adequate_coverage'] = coverage_ratio >= 0.5
            
            if not checks['adequate_coverage']:
                issues.append(f"Low test coverage: {len(test_functions)} tests for {len(functions)} functions")
                suggestions.append(f"Add {len(functions) - len(test_functions)} more test functions")
        else:
            checks['adequate_coverage'] = True  # No functions to test
        
        # Calculate score
        score = sum(checks.values()) / len(checks) if checks else 0.0
        
        return {
            'score': score,
            'checks': checks,
            'issues': issues,
            'suggestions': suggestions,
            'metadata': {
                'total_functions': len(functions),
                'test_functions': len(test_functions),
                'coverage_ratio': len(test_functions) / len(functions) if functions else 0.0
            }
        }
    
    def _extract_functions(self, tree: ast.AST) -> List[str]:
        """Extract all function names."""
        return [node.name for node in ast.walk(tree) 
                if isinstance(node, ast.FunctionDef) 
                and not node.name.startswith('test_')]
    
    def _extract_test_functions(self, tree: ast.AST) -> List[str]:
        """Extract test function names."""
        return [node.name for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef)
                and (node.name.startswith('test_') or 'test' in node.name.lower())]
    
    def _check_test_framework(self, code: str) -> bool:
        """Check if pytest or unittest is used."""
        return any(framework in code for framework in [
            'import pytest',
            'import unittest',
            'from unittest',
            'from pytest',
            '@pytest.',
            'TestCase'
        ])
    
    def _check_edge_case_tests(self, code: str, test_functions: List[str]) -> bool:
        """
        Check if tests cover edge cases.
        Based on user's repeated requests for edge case testing.
        """
        edge_case_indicators = [
            'empty', 'none', 'null', 'zero', '[]', '{}',
            'boundary', 'negative', 'invalid', 'edge',
            'min', 'max', 'overflow'
        ]
        
        code_lower = code.lower()
        return any(indicator in code_lower for indicator in edge_case_indicators)
    
    def _check_error_tests(self, test_functions: List[str]) -> bool:
        """Check if error conditions are tested."""
        # Heuristic: look for test names suggesting error testing
        error_test_patterns = ['error', 'exception', 'invalid', 'raises', 'fail']
        
        return any(pattern in test_name.lower() 
                   for test_name in test_functions 
                   for pattern in error_test_patterns)
    
    def _empty_result(self) -> Dict:
        """Return result for empty/no code."""
        return {
            'score': 0.0,
            'checks': {},
            'issues': ['No code provided'],
            'suggestions': []
        }

# Example usage
if __name__ == '__main__':
    analyzer = TestCoverageAnalyzer()
    
    # Test with incomplete code (like user's typical submissions)
    sample_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    result = analyzer.analyze(sample_code)
    
    print("Test Coverage Analysis")
    print("="*80)
    print(f"Score: {result['score']:.2f}")
    print(f"\nChecks:")
    for check, passed in result['checks'].items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    
    print(f"\nIssues ({len(result['issues'])}):")
    for issue in result['issues']:
        print(f"  🚨 {issue}")
    
    print(f"\nSuggestions ({len(result['suggestions'])}):")
    for suggestion in result['suggestions']:
        print(f"  💡 {suggestion}")
```

### Key Difference from CRAWL

**CRAWL-generated tool:**
- Generic checks for "has tests"
- Based on pattern description

**WALK-generated tool:**
- Specific checks user actually asked for (edge cases, error conditions, frameworks)
- Based on 47 real examples
- Matches user's actual expectations
- Includes frequency-based prioritization ("asked in 73% of cases")

### Deliverable
- `example_based_tool_generator.py` - Generator using conversations
- New tools in `tools/` directory generated from real usage patterns

---

## Hour 13: Adaptive Tool Creation

### Goal
Agent automatically creates tools when conversation patterns are detected.

### Implementation

```python
# adaptive_agent.py

from agent_with_tools import SelfEvolvingAgentWithTools
from conversation_pattern_detector import ConversationPatternDetector
from example_based_tool_generator import ExampleBasedToolGenerator
from conversation_db import ConversationDatabase
from typing import Optional
import json
import os
from datetime import datetime

class AdaptiveSelfEvolvingAgent(SelfEvolvingAgentWithTools):
    """
    Agent that automatically generates new tools based on usage patterns.
    
    Features:
    - Monitors conversation patterns
    - Detects repetitive requests
    - Automatically generates tools when threshold is reached
    - Reloads tool registry dynamically
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        auto_generate_threshold: int = 3
    ):
        super().__init__(api_key)
        
        # Add conversation tracking
        self.conversation_db = ConversationDatabase('conversations.json')
        self.pattern_detector = ConversationPatternDetector(self.conversation_db)
        self.tool_generator = ExampleBasedToolGenerator(self.conversation_db)
        
        # Configuration
        self.auto_generate_threshold = auto_generate_threshold
        self.last_analysis_time = None
        self.pending_tool_suggestions = []
        
        # Check if new tools should be generated
        self._check_for_new_tool_opportunities()
    
    def _check_for_new_tool_opportunities(self):
        """
        Analyze conversation patterns and generate tools if needed.
        
        This runs periodically to check if repetitive patterns warrant
        creating new automation tools.
        """
        print("\n🔍 Checking for new tool opportunities...")
        
        # Run pattern analysis
        analysis = self.pattern_detector.analyze_conversations()
        
        # Get tool suggestions
        tool_suggestions = analysis.get('tool_suggestions', [])
        
        if not tool_suggestions:
            print("✓ No new tools needed")
            return
        
        # Filter for high-priority suggestions (above threshold)
        high_priority = [
            s for s in tool_suggestions
            if s['priority'] >= self.auto_generate_threshold
        ]
        
        if not high_priority:
            print(f"✓ No suggestions above threshold ({self.auto_generate_threshold})")
            return
        
        # Check which tools don't exist yet
        existing_tools = set(self.tool_registry.available_tools())
        
        new_suggestions = [
            s for s in high_priority
            if s['name'].lower() not in existing_tools
        ]
        
        if not new_suggestions:
            print("✓ All suggested tools already exist")
            return
        
        # Generate new tools
        print(f"\n🔧 Found {len(new_suggestions)} new tool opportunities:")
        for suggestion in new_suggestions:
            print(f"  - {suggestion['name']}: {suggestion['reason']}")
        
        self._generate_new_tools(new_suggestions)
    
    def _generate_new_tools(self, suggestions: list):
        """
        Generate and load new tools.
        """
        print("\n" + "="*80)
        print("AUTO-GENERATING TOOLS")
        print("="*80)
        
        generated_count = 0
        
        for suggestion in suggestions:
            try:
                print(f"\nGenerating: {suggestion['name']}")
                
                # Generate tool from examples
                tool_code, tool_name = self.tool_generator.generate_tool_from_examples(
                    suggestion
                )
                
                # Save tool
                filename = f"generated_{tool_name.lower()}.py"
                filepath = os.path.join('tools', filename)
                
                with open(filepath, 'w') as f:
                    f.write(f"# Auto-generated from conversation patterns\n")
                    f.write(f"# Detected: {datetime.now().isoformat()}\n")
                    f.write(f"# {suggestion['reason']}\n\n")
                    f.write(tool_code)
                
                print(f"✓ Saved: {filepath}")
                
                # Reload tool registry to include new tool
                pattern_key = tool_name.lower().replace('analyzer', '').replace('checker', '').replace('validator', '').strip('_')
                
                self.tool_registry._load_tool(filename, pattern_key)
                
                print(f"✓ Loaded into registry: {pattern_key}")
                
                generated_count += 1
                
            except Exception as e:
                print(f"✗ Failed to generate {suggestion['name']}: {e}")
        
        print("\n" + "="*80)
        print(f"✓ Successfully generated and loaded {generated_count} new tools")
        print("="*80)
        
        # Update last analysis time
        self.last_analysis_time = datetime.now()
    
    def record_conversation(self, query: str, response: str, metadata: dict):
        """
        Record conversation for future analysis.
        
        Call this after each interaction to build conversation history.
        """
        conversation = {
            'timestamp': datetime.now().isoformat(),
            'messages': [
                {'role': 'user', 'content': query},
                {'role': 'assistant', 'content': response}
            ],
            'metadata': metadata
        }
        
        # Append to conversation database
        self.conversation_db.conversations.append(conversation)
        
        # Periodically save and analyze
        if len(self.conversation_db.conversations) % 10 == 0:
            self._save_conversations()
            self._check_for_new_tool_opportunities()
    
    def _save_conversations(self):
        """Save conversation database to file."""
        try:
            with open('conversations.json', 'w') as f:
                json.dump({
                    'conversations': self.conversation_db.conversations
                }, f, indent=2)
            print(f"\n✓ Saved {len(self.conversation_db.conversations)} conversations")
        except Exception as e:
            print(f"\n✗ Failed to save conversations: {e}")

# Usage Example
if __name__ == '__main__':
    # Create adaptive agent
    agent = AdaptiveSelfEvolvingAgent(auto_generate_threshold=3)
    
    print(f"\nAgent initialized with {len(agent.tool_registry.available_tools())} tools")
    
    # Simulate conversation
    test_code = """
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)
"""
    
    print("\n" + "="*80)
    print("SIMULATING CONVERSATION")
    print("="*80)
    
    response, metadata = agent.respond(
        "Review this code",
        code=test_code,
        use_patterns=True,
        use_tools=True
    )
    
    print(f"\nResponse generated")
    print(f"Tools executed: {metadata['tools_executed']}")
    
    # Record conversation for future analysis
    agent.record_conversation(
        query="Review this code",
        response=response,
        metadata=metadata
    )
    
    print("\n✓ Conversation recorded")
    print(f"Total conversations: {len(agent.conversation_db.conversations)}")
```

### Deliverable
- `adaptive_agent.py` - Self-adapting agent
- Automatic tool generation on pattern detection

---

## WALK Phase Complete Summary

### What Was Added to Level 1 WALK

| Component | Time | Purpose |
|-----------|------|---------|
| **Pattern Detector** | 2h | Analyze conversations for repetitive requests |
| **Example-Based Generator** | 2h | Generate tools from conversation examples |
| **Adaptive Agent** | 1h | Automatically create tools when patterns detected |

**Total Time Added:** +5 hours (16-20 hours total with base WALK)

### New Capabilities

✅ Agent analyzes conversation history for patterns
✅ Agent detects "asked 47 times" empirically
✅ Agent generates tools from real examples (not just descriptions)
✅ Agent automatically creates tools when threshold reached
✅ Tools match actual user expectations from examples

### Key Innovation

**Agent learns WHEN to create tools, not just HOW.**

Instead of static "this pattern seems tool-worthy," the agent observes:
- "User asked about tests in 47/127 follow-ups (37%)"
- "This crossed threshold (3+), creating TestCoverageAnalyzer"
- "Using actual examples from conversations 2, 5, 8"

**This is empirical, data-driven tool generation.**

---

# Incremental Additions: RUN Phase

**Base:** Level 1 RUN (fine-tuned model for responses)
**Addition:** Fine-tuned model for tool generation (+1 day)
**Total:** 4-6 days

---

## Day 4: Tool Generation Training Data

### Goal
Create training examples that teach the model to generate tools.

### Why This Matters

**WALK:** Uses base Claude API to generate tools (requires full prompt each time)
**RUN:** Uses fine-tuned model (faster, more consistent, learns your tool style)

### Implementation

```python
# tool_generation_training_data.py

import json
from typing import List, Dict
from pathlib import Path

class ToolGenerationTrainingDataCreator:
    """
    Creates training examples for fine-tuning a model to generate tools.
    
    Training examples show:
    - Pattern description → Tool code
    - Conversation examples → Tool code
    - Tool improvement requests → Updated tool code
    """
    
    def __init__(self):
        self.training_examples = []
    
    def create_all_training_data(self) -> List[Dict]:
        """
        Create complete training dataset for tool generation.
        """
        # Type 1: Pattern-based tool generation
        pattern_examples = self._create_pattern_based_examples()
        self.training_examples.extend(pattern_examples)
        
        # Type 2: Example-based tool generation
        example_based = self._create_example_based_examples()
        self.training_examples.extend(example_based)
        
        # Type 3: Tool improvement examples
        improvement_examples = self._create_improvement_examples()
        self.training_examples.extend(improvement_examples)
        
        return self.training_examples
    
    def _create_pattern_based_examples(self) -> List[Dict]:
        """
        Examples of: Pattern description → Tool code
        """
        examples = []
        
        # Example 1: Production readiness
        example1 = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at generating Python tools from pattern descriptions."
                },
                {
                    "role": "user",
                    "content": """Generate a tool for this pattern:

**Pattern:** Production Readiness Checker
**Description:** Check code for tests, error handling, type hints, documentation
**Type:** static_analyzer

Generate Python class with analyze(code: str) -> dict method."""
                },
                {
                    "role": "assistant",
                    "content": """```python
class ProductionReadinessChecker:
    def analyze(self, code: str) -> dict:
        checks = {}
        issues = []
        suggestions = []
        
        # Check for tests
        checks['has_tests'] = 'def test_' in code or 'import pytest' in code
        if not checks['has_tests']:
            issues.append("No unit tests found")
            suggestions.append("Add test functions")
        
        # Check for error handling
        checks['has_error_handling'] = 'try:' in code and 'except' in code
        if not checks['has_error_handling']:
            issues.append("No error handling found")
            suggestions.append("Add try/except blocks")
        
        # Check for type hints
        checks['has_type_hints'] = ' -> ' in code or (': ' in code and 'def' in code)
        if not checks['has_type_hints']:
            issues.append("No type hints found")
            suggestions.append("Add type hints")
        
        # Check for docstrings
        checks['has_docstrings'] = '\"\"\"' in code or \"'''\" in code
        if not checks['has_docstrings']:
            issues.append("No docstrings found")
            suggestions.append("Add docstrings")
        
        score = sum(checks.values()) / len(checks)
        
        return {
            'score': score,
            'checks': checks,
            'issues': issues,
            'suggestions': suggestions
        }
```"""
                }
            ]
        }
        examples.append(example1)
        
        # Add 5-10 more similar examples for different patterns
        # (Gap analysis, precision policing, etc.)
        
        return examples
    
    def _create_example_based_examples(self) -> List[Dict]:
        """
        Examples of: Conversation history → Tool code
        """
        examples = []
        
        # Example: Test coverage analyzer from conversations
        example = {
            "messages": [
                {
                    "role": "system",
                    "content": "You generate tools from conversation patterns."
                },
                {
                    "role": "user",
                    "content": """User asked "What about tests?" 47 times across conversations.

Example conversation:
User: "Implement fibonacci"
Assistant: [gives implementation]
User: "What about tests?"
Assistant: "You should add test_fibonacci() function..."

Generate a tool that checks for tests automatically."""
                },
                {
                    "role": "assistant",
                    "content": """```python
class TestCoverageAnalyzer:
    '''Checks for test coverage based on user's repeated requests.'''
    
    def analyze(self, code: str) -> dict:
        checks = {}
        issues = []
        suggestions = []
        
        # User always asks: "Are there tests?"
        has_tests = 'def test_' in code or 'import pytest' in code
        checks['has_tests'] = has_tests
        
        if not has_tests:
            issues.append("No test functions found")
            suggestions.append("Add test functions with def test_ prefix")
        
        # User often asks: "Do tests cover edge cases?"
        tests_edge_cases = any(word in code.lower() for word in [
            'empty', 'none', 'zero', 'boundary'
        ])
        checks['tests_edge_cases'] = tests_edge_cases
        
        if not tests_edge_cases:
            issues.append("Tests don't cover edge cases")
            suggestions.append("Add tests for empty input, None, boundaries")
        
        score = sum(checks.values()) / len(checks)
        
        return {'score': score, 'checks': checks, 'issues': issues, 'suggestions': suggestions}
```"""
                }
            ]
        }
        examples.append(example)
        
        return examples
    
    def _create_improvement_examples(self) -> List[Dict]:
        """
        Examples of: "Tool needs X" → Improved tool code
        """
        examples = []
        
        # Example: Adding AST parsing to tool
        example = {
            "messages": [
                {
                    "role": "system",
                    "content": "You improve existing tools based on feedback."
                },
                {
                    "role": "user",
                    "content": """Current tool uses string matching to find tests.
This is unreliable. Improve it to use AST parsing.

Current code:
```python
def analyze(self, code: str) -> dict:
    has_tests = 'def test_' in code
    # ...
```

Make it more robust using ast module."""
                },
                {
                    "role": "assistant",
                    "content": """```python
import ast

def analyze(self, code: str) -> dict:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {'score': 0.0, 'issues': ['Syntax error in code']}
    
    # Find all function definitions
    test_functions = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith('test_')
    ]
    
    has_tests = len(test_functions) > 0
    
    # Rest of analysis...
```"""
                }
            ]
        }
        examples.append(example)
        
        return examples
    
    def save_training_data(self, output_file: str = 'tool_generation_training.jsonl'):
        """
        Save training examples in JSONL format for fine-tuning.
        """
        with open(output_file, 'w') as f:
            for example in self.training_examples:
                f.write(json.dumps(example) + '\n')
        
        print(f"✓ Saved {len(self.training_examples)} training examples to {output_file}")
    
    def augment_with_real_tools(self, tools_dir: str = 'tools'):
        """
        Create training examples from actually generated tools.
        
        This captures your actual tool generation style.
        """
        tools_path = Path(tools_dir)
        
        for tool_file in tools_path.glob('generated_*.py'):
            # Read tool code
            with open(tool_file, 'r') as f:
                tool_code = f.read()
            
            # Extract metadata from comments
            lines = tool_code.split('\n')
            pattern_line = [l for l in lines if l.startswith('# Pattern:')]
            
            if pattern_line:
                pattern_name = pattern_line[0].replace('# Pattern:', '').strip()
                
                # Create training example
                example = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "Generate a Python tool from this pattern."
                        },
                        {
                            "role": "user",
                            "content": f"Generate a tool for: {pattern_name}"
                        },
                        {
                            "role": "assistant",
                            "content": tool_code
                        }
                    ]
                }
                
                self.training_examples.append(example)
        
        print(f"✓ Augmented with {len(list(tools_path.glob('generated_*.py')))} real tool examples")

# Usage
if __name__ == '__main__':
    creator = ToolGenerationTrainingDataCreator()
    
    # Create synthetic examples
    examples = creator.create_all_training_data()
    
    # Augment with real generated tools
    creator.augment_with_real_tools('tools')
    
    # Save for fine-tuning
    creator.save_training_data('tool_generation_training.jsonl')
    
    print(f"\n✓ Total training examples: {len(creator.training_examples)}")
```

### Training Data Strategy

**Mix of:**
1. **Pattern-based** (10-15 examples): Pattern description → Tool code
2. **Example-based** (10-15 examples): Conversations → Tool code
3. **Real tools** (3-5 examples): Your actually generated tools
4. **Improvements** (5-10 examples): Feedback → Better tool

**Total:** 30-50 examples for tool generation specifically

**These get added to your main training data** (the 200-400 examples for response generation).

### Deliverable
- `tool_generation_training_data.py` - Creator script
- `tool_generation_training.jsonl` - Training data
- Combined with main training data for fine-tuning

---

## Day 4: Fine-Tuning with Tool Generation

### Process

```python
# Append tool generation data to main training data
import json

# Load main training data
with open('training_combined.jsonl', 'r') as f:
    main_data = [json.loads(line) for line in f]

# Load tool generation data
with open('tool_generation_training.jsonl', 'r') as f:
    tool_data = [json.loads(line) for line in f]

# Combine
combined = main_data + tool_data

# Save
with open('training_with_tools.jsonl', 'w') as f:
    for example in combined:
        f.write(json.dumps(example) + '\n')

print(f"Combined training data: {len(combined)} examples")
print(f"  - Response generation: {len(main_data)}")
print(f"  - Tool generation: {len(tool_data)}")

# Now fine-tune as usual (OpenAI or HuggingFace)
```

### Fine-Tuned Tool Generator

```python
# finetuned_tool_generator.py

import openai  # or your fine-tuned model

class FineTunedToolGenerator:
    """
    Uses fine-tuned model for tool generation.
    
    Benefits vs. base model:
    - Faster (no long prompts needed)
    - More consistent (learned your style)
    - Better quality (trained on your examples)
    """
    
    def __init__(self, finetuned_model_id: str):
        self.model_id = finetuned_model_id
    
    def generate_tool(self, pattern: Dict) -> str:
        """
        Generate tool using fine-tuned model.
        
        Much simpler prompt than WALK approach.
        """
        prompt = f"""Generate a tool for: {pattern['name']}
Description: {pattern['description']}
Type: {pattern.get('tool_type', 'analyzer')}"""
        
        response = openai.ChatCompletion.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # Low temp for consistent code
            max_tokens=2000
        )
        
        return response['choices'][0]['message']['content']
    
    def generate_from_conversations(self, reason: str) -> str:
        """
        Generate tool from conversation pattern.
        
        Even simpler - model learned this pattern.
        """
        prompt = f"User asked about this {reason}. Generate appropriate tool."
        
        response = openai.ChatCompletion.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2000
        )
        
        return response['choices'][0]['message']['content']
```

---

## RUN Phase Complete Summary

### What Was Added to Level 1 RUN

| Component | Time | Purpose |
|-----------|------|---------|
| **Tool Training Data** | 4h | Create examples for tool generation |
| **Fine-Tuning** | 2-4h | Train model on tool generation |
| **Fine-Tuned Generator** | 1h | Use fine-tuned model for tools |

**Total Time Added:** +1 day (5-6 days total with base RUN)

### Benefits Over WALK

| Aspect | WALK (Base Model) | RUN (Fine-Tuned) |
|--------|-------------------|------------------|
| **Prompt Length** | 2000-3000 tokens | 100-200 tokens |
| **Generation Time** | 10-15s | 3-5s |
| **Consistency** | Varies | Very consistent |
| **Quality** | Good | Matches your style exactly |
| **Cost per Tool** | $0.03-0.05 | $0.01-0.02 |

### Key Innovation

**Model internalized tool generation patterns.**

Instead of teaching it each time via prompt, the model learned:
- Your tool structure preferences
- Your naming conventions
- Your error handling style
- Your documentation format

**Tool generation becomes a native capability.**

---

# Complete Level 2 Comparison

## CRAWL: Static Tool Generation

**Time:** +4 hours (9.5h total)

**Process:**
1. Analyze patterns for tool-worthiness
2. Generate tools via Claude API (with pattern descriptions)
3. Load tools into registry
4. Agent executes tools

**Tools Created:** 3 (from patterns)

**Demo:** "Agent identified tool-worthy patterns and created automation"

---

## WALK: Adaptive Tool Generation

**Time:** +5 hours (16-20h total)

**Process:**
1. Analyze conversations for repetitive requests
2. Generate tools via Claude API (with conversation examples)
3. Agent automatically creates tools when threshold reached
4. Tools match actual user expectations

**Tools Created:** 5 (from empirical data)

**Demo:** "Agent learned I asked for tests 47 times, automatically created TestCoverageAnalyzer"

---

## RUN: Fine-Tuned Tool Generation

**Time:** +1 day (5-6 days total)

**Process:**
1. Train model on tool generation examples
2. Fine-tuned model generates tools (faster, more consistent)
3. Agent uses fine-tuned model for all tool generation
4. Tools match your exact style

**Tools Created:** Unlimited (model capability)

**Demo:** "Agent's fine-tuned model generates tools 3x faster with perfect style consistency"

---

# Recommendation for Hackathon

## What to Implement

**✅ Level 1 CRAWL:** 5.5 hours
- Memory-augmented prompting
- Pattern-based responses
- Clear before/after demo

**✅ Level 2 CRAWL (if time):** +4 hours (9.5h total)
- Tool generation from patterns
- 3 auto-generated tools
- Tool execution in pipeline
- Shows real "evolution"

**❌ Level 2 WALK:** Skip for hackathon (needs conversation data)

**❌ Level 2 RUN:** Skip for hackathon (too complex)

## Future Work Slide

"**Phase 2: Adaptive Tool Generation** (Post-hackathon)
- Analyze 50+ conversations
- Detect 'asked 47 times' patterns
- Auto-generate tools from examples
- True self-evolution

**Phase 3: Fine-Tuned Tool Generation** (Production)
- Train model on tool generation
- 3x faster tool creation
- Perfect style consistency
- Unlimited tool capabilities"

---

# Final File Structure

```
project/
├── 01_extracted_patterns.md
├── 02_synthetic_conversations.md
├── 03_preference_profile.md
├── 04_training_implementation_plan.md
├── 05_level2_architectural_changes.md  ← THIS DOCUMENT
│
├── patterns.json
├── conversations.json
├── pattern_analysis.json
│
├── tool_analyzer.py
├── tool_generator.py
├── tool_registry.py
├── conversation_pattern_detector.py
├── example_based_tool_generator.py
├── adaptive_agent.py
├── finetuned_tool_generator.py
│
├── agent.py                       # Level 1 CRAWL
├── agent_with_tools.py            # Level 2 CRAWL
├── agent_v2.py                    # Level 1 WALK
├── adaptive_agent.py              # Level 2 WALK
│
├── demo.py                        # Level 1 CRAWL demo
├── demo_with_tools.py             # Level 2 CRAWL demo
├── demo_v2.py                     # Level 1 WALK demo
│
└── tools/
    ├── generated_production_readiness.py
    ├── generated_gap_analysis.py
    ├── generated_precision_policing.py
    ├── generated_testcoverageanalyzer.py
    └── generated_errorhandlingchecker.py
```

---

**You now have complete documentation for both Level 1 (Memory-Augmented) and Level 2 (Architectural Changes) across all three phases (CRAWL/WALK/RUN).**

Good luck with your hackathon! 🚀
