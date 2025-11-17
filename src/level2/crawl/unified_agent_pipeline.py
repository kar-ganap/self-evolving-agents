"""
Unified Agent Pipeline - Integrates pattern matching, tool execution, and LLM responses

Combines automated tool execution with Gemini 2.5 Pro for intelligent responses.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime

from google import genai
from google.genai import types

from src.level2.crawl.tool_acquisition_engine import GeneratedTool


class ToolRegistry:
    """
    Registry of available tools mapped to patterns.

    Manages dynamic loading and execution of generated tools.
    """

    def __init__(self):
        """Initialize empty tool registry."""
        self.tools: Dict[str, List] = {}  # pattern_name -> [tool instances]

    def register(self, tool: GeneratedTool, pattern_name: str):
        """
        Register a tool for a specific pattern.

        Args:
            tool: GeneratedTool with code to execute
            pattern_name: Pattern this tool applies to (e.g., "Production Readiness")
        """
        if pattern_name not in self.tools:
            self.tools[pattern_name] = []

        # Load tool code dynamically
        loaded_tool = self._load_tool(tool)
        self.tools[pattern_name].append(loaded_tool)

    def get_tools_for_pattern(self, pattern_name: str) -> List:
        """
        Get all registered tools for a pattern.

        Args:
            pattern_name: Pattern to look up

        Returns:
            List of tool instances for this pattern
        """
        return self.tools.get(pattern_name, [])

    def _load_tool(self, tool: GeneratedTool):
        """
        Dynamically load and instantiate tool from generated code.

        Args:
            tool: GeneratedTool with Python code

        Returns:
            Instance of the generated tool class
        """
        # Execute code in isolated namespace
        namespace = {}
        exec(tool.code, namespace)

        # Find the class (should match tool.name)
        tool_class = namespace.get(tool.name)
        if not tool_class:
            # Find first class in namespace
            tool_class = next(
                (v for v in namespace.values() if isinstance(v, type)),
                None
            )

        if not tool_class:
            raise ValueError(f"No class found in generated code for {tool.name}")

        # Instantiate and return
        return tool_class()


class UnifiedAgentPipeline:
    """
    Unified pipeline combining pattern-based tool execution with LLM responses.

    Flow:
    1. Match patterns from user query
    2. Execute relevant tools
    3. Build augmented prompt with tool results
    4. Get LLM response interpreting results
    """

    def __init__(
        self,
        gemini_api_key: Optional[str],
        tool_registry: ToolRegistry
    ):
        """
        Initialize pipeline.

        Args:
            gemini_api_key: Google API key (or None to use GEMINI_API_KEY env var)
            tool_registry: ToolRegistry with registered tools
        """
        self.tool_registry = tool_registry
        api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.5-pro'
        self.generation_config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=2000,
        )

    def process(self, query: str, code: Optional[str] = None) -> Dict:
        """
        Process user query through pattern + tool pipeline.

        Args:
            query: User's question or request
            code: Optional code to analyze

        Returns:
            dict with:
                - answer: LLM response
                - patterns_applied: List of matched patterns
                - tools_used: List of tools executed
                - tool_results: Dict of tool outputs
                - metadata: Query timestamp, etc.
        """
        # Step 1: Match patterns (simplified keyword matching)
        patterns = self._match_patterns(query)

        # Step 2: Execute tools for matched patterns
        tool_results = {}
        for pattern_name in patterns:
            tools = self.tool_registry.get_tools_for_pattern(pattern_name)
            for tool in tools:
                try:
                    result = tool.analyze(code or query)
                    tool_results[f"{pattern_name}_tool"] = result
                except Exception as e:
                    tool_results[f"{pattern_name}_tool"] = {
                        'error': str(e),
                        'score': 0.0
                    }

        # Step 3: Build augmented prompt with tool results
        prompt = self._build_prompt(query, code, patterns, tool_results)

        # Step 4: Get Gemini response
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self.generation_config
        )

        return {
            'answer': response.text,
            'patterns_applied': patterns,
            'tools_used': list(tool_results.keys()),
            'tool_results': tool_results,
            'metadata': {
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
        }

    def _match_patterns(self, query: str) -> List[str]:
        """
        Simple keyword-based pattern matching.

        Args:
            query: User query string

        Returns:
            List of matched pattern names
        """
        query_lower = query.lower()
        patterns = []

        # Pattern keywords (from Phase 0 patterns)
        pattern_keywords = {
            'Production Readiness': [
                'test', 'production', 'ready', 'deploy',
                'error handling', 'type hint', 'documentation'
            ],
            'Gap Analysis': [
                'missing', 'gap', 'what about', 'incomplete',
                'forgot', 'overlooked'
            ],
            'Tradeoff Analysis': [
                'vs', 'versus', 'compare', 'alternative',
                'option', 'tradeoff', 'pros', 'cons'
            ],
        }

        for pattern_name, keywords in pattern_keywords.items():
            if any(kw in query_lower for kw in keywords):
                patterns.append(pattern_name)

        return patterns

    def _build_prompt(
        self,
        query: str,
        code: Optional[str],
        patterns: List[str],
        tool_results: Dict
    ) -> str:
        """
        Build augmented prompt with pattern context and tool results.

        Args:
            query: User's query
            code: Optional code being analyzed
            patterns: Matched patterns
            tool_results: Results from tool execution

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        # System context
        prompt_parts.append("You are an expert coding assistant with access to automated analysis tools.")

        # Pattern context
        if patterns:
            prompt_parts.append("\nApply these learned patterns in your response:")
            for pattern in patterns:
                prompt_parts.append(f"- {pattern}")

        # Tool results
        if tool_results:
            prompt_parts.append("\n\nAUTOMATED ANALYSIS RESULTS:")
            for tool_name, result in tool_results.items():
                if 'error' in result:
                    prompt_parts.append(f"\n{tool_name}: Error - {result['error']}")
                    continue

                prompt_parts.append(f"\n{tool_name}:")
                prompt_parts.append(f"  Overall Score: {result.get('score', 0):.0%}")

                checks = result.get('checks', {})
                if checks:
                    prompt_parts.append("  Detailed Checks:")
                    for check, passed in checks.items():
                        symbol = "✓" if passed else "✗"
                        prompt_parts.append(f"    {symbol} {check}")

                issues = result.get('issues', [])
                if issues:
                    prompt_parts.append("  Issues Found:")
                    for issue in issues[:5]:  # Limit to top 5
                        prompt_parts.append(f"    - {issue}")

                suggestions = result.get('suggestions', [])
                if suggestions:
                    prompt_parts.append("  Suggestions:")
                    for suggestion in suggestions[:3]:  # Limit to top 3
                        prompt_parts.append(f"    - {suggestion}")

            prompt_parts.append("\nYOUR TASK:")
            prompt_parts.append("1. Interpret these automated results in context")
            prompt_parts.append("2. Prioritize issues by severity and impact")
            prompt_parts.append("3. Provide specific, actionable recommendations")
            prompt_parts.append("4. Explain WHY each issue matters for code quality")

        # User query
        prompt_parts.append(f"\n\nUSER QUERY:\n{query}")

        # Code context
        if code:
            prompt_parts.append(f"\n\nCODE TO ANALYZE:\n```python\n{code}\n```")

        return "\n".join(prompt_parts)


# Example usage and testing
if __name__ == "__main__":
    print("Unified Agent Pipeline - Test Mode\n")

    # Setup
    registry = ToolRegistry()

    # Load the pre-generated Production Readiness tool
    from pathlib import Path
    tool_file = Path(__file__).parent.parent.parent.parent / "src/level2/tools/generated/production_readiness.py"

    if tool_file.exists():
        with open(tool_file, 'r') as f:
            tool_code = f.read()

        # Create GeneratedTool object
        tool = GeneratedTool(
            name="ProductionReadiness",
            code=tool_code,
            pattern_name="Production Readiness",
            acquisition_type="build",
            metadata={"test": True}
        )

        # Register tool
        registry.register(tool, "Production Readiness")
        print("✓ Registered ProductionReadiness tool\n")

        # Create pipeline
        pipeline = UnifiedAgentPipeline(
            gemini_api_key=None,  # Uses GEMINI_API_KEY env var
            tool_registry=registry
        )

        # Test query with sample code
        test_code = """
def calculate(x, y):
    return x + y

result = calculate(5, 3)
print(result)
"""

        query = "Is this code production ready? What's missing?"

        print("=" * 80)
        print(f"Query: {query}")
        print("=" * 80)

        result = pipeline.process(query, test_code)

        print(f"\nPatterns Applied: {', '.join(result['patterns_applied'])}")
        print(f"Tools Used: {', '.join(result['tools_used'])}")

        print("\nTool Results:")
        for tool_name, tool_result in result['tool_results'].items():
            print(f"  {tool_name}: Score = {tool_result.get('score', 0):.0%}")

        print("\nLLM Response:")
        print(result['answer'])

        print("\n" + "=" * 80)
    else:
        print("✗ Production Readiness tool not found")
        print(f"  Expected at: {tool_file}")
