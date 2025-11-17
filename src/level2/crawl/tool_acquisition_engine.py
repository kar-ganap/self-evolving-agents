"""
Tool Acquisition Engine - Generates or acquires tools based on approved strategy

Implements both BUILD (internal code generation) and BUY (library wrapper) paths.
Uses Gemini 2.5 Pro for code generation.
"""

import os
import re
from dataclasses import dataclass
from typing import Dict, Optional
from pathlib import Path

from google import genai
from google.genai import types

from src.level2.crawl.build_vs_buy_analyzer import (
    BuildVsBuyRecommendation,
    BuildOption,
    BuyOption,
    AcquisitionType
)
from src.level2.crawl.approval_workflow import ApprovalResponse


@dataclass
class GeneratedTool:
    """
    A generated or acquired tool.

    Attributes:
        name: Tool class name (PascalCase)
        code: Python code for the tool
        pattern_name: Pattern this tool addresses
        acquisition_type: 'build', 'library', or 'api'
        metadata: Additional information about generation/acquisition
    """
    name: str
    code: str
    pattern_name: str
    acquisition_type: str  # 'build', 'library', 'api'
    metadata: Dict


class ToolAcquisitionEngine:
    """
    Implements the approved acquisition strategy.

    BUILD path:
    - Generate tool code using Gemini 2.5 Pro
    - Validate syntax
    - Save to src/level2/tools/generated/

    BUY path:
    - For libraries: Generate wrapper code
    - For APIs: Generate client wrapper (future)
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize the tool acquisition engine.

        Args:
            gemini_api_key: Google API key. If None, uses GEMINI_API_KEY env var
        """
        api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.5-pro'
        self.generation_config = types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=8000,
        )

    def acquire_tool(
        self,
        pattern: Dict,
        recommendation: BuildVsBuyRecommendation,
        approval: ApprovalResponse
    ) -> GeneratedTool:
        """
        Implement the approved acquisition strategy.

        Args:
            pattern: Pattern dictionary with 'name' and 'description'
            recommendation: BuildVsBuyRecommendation from analyzer
            approval: ApprovalResponse from workflow

        Returns:
            GeneratedTool ready to be registered and used
        """
        if approval.selected_option == 'build':
            return self._build_tool(pattern, recommendation.build_option)
        else:
            # Find the selected buy option
            buy_option = next(
                (opt for opt in recommendation.buy_options
                 if opt.source == approval.selected_option),
                None
            )
            if not buy_option:
                raise ValueError(f"Unknown option: {approval.selected_option}")

            if buy_option.acquisition_type == AcquisitionType.LIBRARY:
                return self._acquire_library(pattern, buy_option)
            else:
                return self._acquire_api(pattern, buy_option)

    def _build_tool(
        self,
        pattern: Dict,
        build_option: BuildOption
    ) -> GeneratedTool:
        """
        Generate tool code using Gemini 2.5 Pro.

        Args:
            pattern: Pattern dictionary with 'name' and 'description'
            build_option: BuildOption from analyzer

        Returns:
            GeneratedTool with generated code
        """
        class_name = self._generate_class_name(pattern['name'])

        generation_prompt = f"""Generate a production-quality Python tool that automates this pattern.

# Pattern Information
**Name:** {pattern['name']}
**Description:** {pattern['description']}

# Requirements

1. **Class Structure:**
   - Class name: `{class_name}`
   - Main method: `analyze(self, code: str, file_path: str = None) -> dict`
   - Return format: {{'score': float, 'checks': dict, 'issues': list, 'suggestions': list}}

2. **Functionality:**
   Based on the pattern description, implement checks that detect:
   - What the pattern looks for
   - Common issues related to this pattern
   - Suggestions for improvement

3. **Code Quality:**
   - Include comprehensive docstrings
   - Add type hints
   - Handle edge cases (empty input, None, malformed code)
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

Generate ONLY the Python code. No explanation, no markdown except code block."""

        response = self.client.models.generate_content(
            model=self.model,
            contents=generation_prompt,
            config=self.generation_config
        )

        tool_code = response.text

        # Extract Python code from markdown if present
        if "```python" in tool_code:
            tool_code = tool_code.split("```python")[1].split("```")[0].strip()
        elif "```" in tool_code:
            tool_code = tool_code.split("```")[1].split("```")[0].strip()

        # Validate syntax
        try:
            compile(tool_code, '<string>', 'exec')
        except SyntaxError as e:
            raise ValueError(f"Generated code has syntax errors: {e}")

        return GeneratedTool(
            name=class_name,
            code=tool_code,
            pattern_name=pattern['name'],
            acquisition_type='build',
            metadata={
                'build_option': {
                    'complexity': build_option.complexity,
                    'estimated_hours': build_option.estimated_hours,
                    'lines_of_code': build_option.lines_of_code
                },
                'generated_by': 'gemini-2.5-pro'
            }
        )

    def _acquire_library(
        self,
        pattern: Dict,
        buy_option: BuyOption
    ) -> GeneratedTool:
        """
        Generate wrapper code for library.

        Args:
            pattern: Pattern dictionary with 'name' and 'description'
            buy_option: BuyOption from analyzer

        Returns:
            GeneratedTool with wrapper code
        """
        class_name = self._generate_class_name(pattern['name'])

        wrapper_prompt = f"""Generate a Python wrapper class for the '{buy_option.source}' library.

# Pattern
**Name:** {pattern['name']}
**Description:** {pattern['description']}

# Library
**Name:** {buy_option.source}

# Requirements

1. **Class Structure:**
   - Class name: `{class_name}`
   - Import and wrap '{buy_option.source}' library
   - Main method: `analyze(self, code: str, file_path: str = None) -> dict`
   - Return standardized format: {{'score': float, 'checks': dict, 'issues': list, 'suggestions': list}}

2. **Functionality:**
   - Use {buy_option.source} to perform analysis
   - Convert library output to standardized format
   - Handle library-specific errors gracefully
   - Add meaningful interpretation of results

3. **Error Handling:**
   - Try/except around library calls
   - Fallback to safe defaults if library fails
   - Log errors but don't crash

4. **Example:**
   ```python
   tool = {class_name}()
   result = tool.analyze(code_string)
   # Returns: {{'score': 0.75, 'checks': {{...}}, 'issues': [...], 'suggestions': [...]}}
   ```

Generate ONLY the Python code including import statements. No explanation."""

        response = self.client.models.generate_content(
            model=self.model,
            contents=wrapper_prompt,
            config=self.generation_config
        )

        wrapper_code = response.text

        # Extract code from markdown
        if "```python" in wrapper_code:
            wrapper_code = wrapper_code.split("```python")[1].split("```")[0].strip()
        elif "```" in wrapper_code:
            wrapper_code = wrapper_code.split("```")[1].split("```")[0].strip()

        # Validate syntax
        try:
            compile(wrapper_code, '<string>', 'exec')
        except SyntaxError as e:
            raise ValueError(f"Generated wrapper has syntax errors: {e}")

        return GeneratedTool(
            name=class_name,
            code=wrapper_code,
            pattern_name=pattern['name'],
            acquisition_type='library',
            metadata={
                'library_name': buy_option.source,
                'library_cost': buy_option.cost_per_month,
                'maturity_score': buy_option.maturity_score
            }
        )

    def _acquire_api(
        self,
        pattern: Dict,
        buy_option: BuyOption
    ) -> GeneratedTool:
        """
        Generate API client wrapper.

        Args:
            pattern: Pattern dictionary
            buy_option: BuyOption for API

        Returns:
            GeneratedTool with API client wrapper

        Note:
            This is a placeholder for future WALK phase implementation
        """
        raise NotImplementedError("API acquisition not yet implemented (WALK phase)")

    def _generate_class_name(self, pattern_name: str) -> str:
        """
        Convert pattern name to PascalCase class name.

        Args:
            pattern_name: Pattern name (e.g., "Production Readiness")

        Returns:
            PascalCase class name (e.g., "ProductionReadiness")
        """
        # Remove special characters, convert to PascalCase
        clean_name = pattern_name.replace('&', 'And').replace('-', ' ')
        # Remove any other non-alphanumeric characters
        clean_name = re.sub(r'[^\w\s]', '', clean_name)
        words = clean_name.split()
        return ''.join(word.capitalize() for word in words)

    def save_tool(self, tool: GeneratedTool) -> Path:
        """
        Save generated tool to file.

        Args:
            tool: GeneratedTool to save

        Returns:
            Path to saved file
        """
        # Create generated tools directory
        project_root = Path(__file__).parent.parent.parent.parent
        tools_dir = project_root / "src/level2/tools/generated"
        tools_dir.mkdir(parents=True, exist_ok=True)

        # Convert class name to snake_case for filename
        filename = re.sub(r'(?<!^)(?=[A-Z])', '_', tool.name).lower() + '.py'
        file_path = tools_dir / filename

        # Save code to file
        with open(file_path, 'w') as f:
            f.write(tool.code)

        return file_path


# Example usage and testing
if __name__ == "__main__":
    print("Tool Acquisition Engine - Test Mode\n")

    engine = ToolAcquisitionEngine()

    # Test case 1: BUILD a simple tool
    print("=" * 80)
    print("Test 1: Generate tool for Production Readiness pattern")
    print("=" * 80)

    pattern = {
        'name': 'Production Readiness',
        'description': 'Check code for tests, type hints, error handling, and documentation'
    }

    build_option = BuildOption(
        complexity=5,
        estimated_hours=4.0,
        lines_of_code=300,
        dependencies=['ast', 'typing'],
        testing_effort=3,
        maintenance_score=3
    )

    print(f"\nPattern: {pattern['name']}")
    print(f"Generating tool using Gemini 2.5 Pro...")

    tool = engine._build_tool(pattern, build_option)

    print(f"\n✓ Tool generated successfully!")
    print(f"  Name: {tool.name}")
    print(f"  Type: {tool.acquisition_type}")
    print(f"  Code length: {len(tool.code)} characters")
    print(f"  Lines: {len(tool.code.split(chr(10)))}")

    # Validate structure
    if 'def analyze' in tool.code:
        print(f"  ✓ Has analyze() method")
    else:
        print(f"  ✗ Missing analyze() method")

    # Try to compile
    try:
        compile(tool.code, '<string>', 'exec')
        print(f"  ✓ Code compiles successfully")
    except SyntaxError as e:
        print(f"  ✗ Syntax error: {e}")

    # Save to file
    saved_path = engine.save_tool(tool)
    print(f"\n✓ Tool saved to: {saved_path}")

    print("\n" + "=" * 80)
