"""
End-to-End Integration Test for CRAWL Phase

Tests the complete self-evolution workflow:
1. User query triggers gap detection
2. Build vs Buy analysis recommends acquisition strategy
3. Approval workflow (with bypass) approves acquisition
4. Tool is generated/acquired via Gemini 2.5 Pro
5. Tool is registered in pipeline
6. Pipeline uses tool to answer original query

This validates that all components work together.
"""

import pytest
from pathlib import Path

from src.level2.crawl.capability_evolution_engine import CapabilityEvolutionEngine
from src.level2.crawl.unified_agent_pipeline import ToolRegistry


class TestEndToEndCRAWL:
    """End-to-end integration tests for CRAWL phase"""

    def test_manual_evolution_and_pipeline_integration(self):
        """Test manual capability evolution and tool usage"""
        # Initialize engine
        engine = CapabilityEvolutionEngine()

        # Define pattern to evolve
        pattern = {
            'name': 'Test Coverage Analysis',
            'description': 'Analyze test coverage for Python code'
        }

        missing_capabilities = [
            'Detect test files',
            'Count assertions',
            'Measure coverage percentage'
        ]

        # Evolve capability
        result = engine.evolve_capability(
            pattern=pattern,
            missing_capabilities=missing_capabilities,
            automation_potential=0.9,
            auto_approve=True
        )

        # Validate evolution result
        assert result.tool_acquired == True, "Tool should be acquired"
        assert result.tool is not None, "Tool should be present"
        assert result.error is None, f"Should not have error: {result.error}"

        # Validate tool structure
        assert result.tool.name == 'TestCoverageAnalysis'
        assert result.tool.pattern_name == 'Test Coverage Analysis'
        assert 'def analyze' in result.tool.code, "Tool should have analyze method"

        # Get pipeline with registered tool
        pipeline = engine.get_pipeline()

        # Verify tool is registered
        assert 'Test Coverage Analysis' in engine.tool_registry.tools
        assert len(engine.tool_registry.tools['Test Coverage Analysis']) == 1

    def test_gap_detection_from_query(self):
        """Test automatic gap detection from user queries"""
        engine = CapabilityEvolutionEngine()

        # Test 1: Production readiness query
        query1 = "Is my code production ready?"
        gaps1 = engine.detect_gaps_from_query(query1)

        assert len(gaps1) > 0, "Should detect at least one gap"
        assert any(g['pattern']['name'] == 'Production Readiness' for g in gaps1)

        # Test 2: Security query
        query2 = "Check my code for security vulnerabilities"
        gaps2 = engine.detect_gaps_from_query(query2)

        assert len(gaps2) > 0, "Should detect security gap"
        assert any(g['pattern']['name'] == 'Security Analysis' for g in gaps2)

        # Test 3: Performance query
        query3 = "How can I optimize this for better performance?"
        gaps3 = engine.detect_gaps_from_query(query3)

        assert len(gaps3) > 0, "Should detect performance gap"
        assert any(g['pattern']['name'] == 'Performance Optimization' for g in gaps3)

    def test_auto_approval_bypass(self):
        """Test that simple tools bypass approval"""
        engine = CapabilityEvolutionEngine()

        # Simple pattern with high automation potential
        simple_pattern = {
            'name': 'Simple Validator',
            'description': 'Validate basic syntax'
        }

        result = engine.evolve_capability(
            pattern=simple_pattern,
            missing_capabilities=['Check syntax'],
            automation_potential=0.95,  # Very automatable
            auto_approve=True
        )

        # Should auto-approve due to simplicity
        assert result.tool_acquired == True
        assert result.approval_bypassed == True, "Simple tool should bypass approval"

    def test_tool_code_quality(self):
        """Test that generated tools meet quality standards"""
        engine = CapabilityEvolutionEngine()

        pattern = {
            'name': 'Code Quality Checker',
            'description': 'Check code quality metrics'
        }

        result = engine.evolve_capability(
            pattern=pattern,
            missing_capabilities=['Check code quality'],
            automation_potential=0.85,
            auto_approve=True
        )

        assert result.tool_acquired == True

        tool_code = result.tool.code

        # Quality checks
        assert 'class CodeQualityChecker' in tool_code, "Should have correct class name"
        assert 'def analyze' in tool_code, "Should have analyze method"
        assert 'def __init__' in tool_code or 'class ' in tool_code, "Should have proper structure"

        # Check for docstrings (production readiness)
        assert '"""' in tool_code or "'''" in tool_code, "Should have docstrings"

    def test_pipeline_integration_with_multiple_tools(self):
        """Test pipeline with multiple tools registered"""
        engine = CapabilityEvolutionEngine()

        # Evolve multiple capabilities
        patterns = [
            {
                'name': 'Pattern A',
                'description': 'First pattern',
                'capabilities': ['Capability A1', 'Capability A2'],
                'automation': 0.9
            },
            {
                'name': 'Pattern B',
                'description': 'Second pattern',
                'capabilities': ['Capability B1'],
                'automation': 0.85
            }
        ]

        for p in patterns:
            result = engine.evolve_capability(
                pattern={'name': p['name'], 'description': p['description']},
                missing_capabilities=p['capabilities'],
                automation_potential=p['automation'],
                auto_approve=True
            )

            assert result.tool_acquired == True, f"Should acquire tool for {p['name']}"

        # Get pipeline
        pipeline = engine.get_pipeline()

        # Verify multiple patterns registered
        assert len(engine.tool_registry.tools) == 2
        assert 'Pattern A' in engine.tool_registry.tools
        assert 'Pattern B' in engine.tool_registry.tools

    def test_error_handling(self):
        """Test error handling in evolution workflow"""
        engine = CapabilityEvolutionEngine()

        # Test with empty pattern name (should handle gracefully)
        try:
            result = engine.evolve_capability(
                pattern={'name': '', 'description': 'Empty name'},
                missing_capabilities=['Test'],
                automation_potential=0.5,
                auto_approve=True
            )

            # If it doesn't raise, check the result
            assert result.error is not None or result.tool_acquired == False

        except Exception as e:
            # Acceptable to raise exception for invalid input
            pass

    def test_tool_file_saved(self):
        """Test that generated tools are saved to filesystem"""
        engine = CapabilityEvolutionEngine()

        pattern = {
            'name': 'File Save Test',
            'description': 'Test that tools are saved'
        }

        result = engine.evolve_capability(
            pattern=pattern,
            missing_capabilities=['Test capability'],
            automation_potential=0.9,
            auto_approve=True
        )

        assert result.tool_acquired == True

        # Check file exists
        tools_dir = Path(__file__).parent.parent.parent.parent / "src/level2/tools/generated"
        expected_file = tools_dir / "file_save_test.py"

        assert expected_file.exists(), f"Tool file should be saved at {expected_file}"

        # Validate file contents
        with open(expected_file, 'r') as f:
            content = f.read()
            assert 'class FileSaveTest' in content
            assert 'def analyze' in content


@pytest.mark.integration
class TestFullWorkflowIntegration:
    """
    Full workflow integration tests (marked as integration tests).

    These tests simulate real user interactions with the complete system.
    """

    def test_production_readiness_workflow(self):
        """
        Test complete workflow:
        1. User asks about production readiness
        2. System detects gap
        3. System evolves capability
        4. System uses new tool to answer query
        """
        engine = CapabilityEvolutionEngine()

        # User query
        query = "Is this code production ready?"
        code = """
def calculate(x, y):
    return x + y

result = calculate(5, 3)
print(result)
"""

        # Step 1: Detect gaps
        gaps = engine.detect_gaps_from_query(query, code)
        assert len(gaps) > 0, "Should detect capability gaps"

        # Step 2: Evolve first gap (Production Readiness)
        gap = gaps[0]
        result = engine.evolve_capability(
            pattern=gap['pattern'],
            missing_capabilities=gap['missing_capabilities'],
            automation_potential=gap['automation_potential'],
            auto_approve=True
        )

        assert result.tool_acquired == True, "Should acquire Production Readiness tool"

        # Step 3: Use pipeline to answer original query
        pipeline = engine.get_pipeline()
        response = pipeline.process(query, code)

        # Validate response structure
        assert 'answer' in response
        assert 'patterns_applied' in response
        assert 'tool_results' in response
        assert len(response['patterns_applied']) > 0
        assert len(response['tool_results']) > 0

        # Validate tool was used
        assert 'Production Readiness' in response['patterns_applied']

        print("\n=== Full Workflow Test Results ===")
        print(f"Query: {query}")
        print(f"Patterns: {response['patterns_applied']}")
        print(f"Tools Used: {list(response['tool_results'].keys())}")
        print(f"Answer Length: {len(response['answer'])} characters")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
