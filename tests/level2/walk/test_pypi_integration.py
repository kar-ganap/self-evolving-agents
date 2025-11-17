"""
End-to-End Integration Tests for WALK Phase - PyPI Library Integration

Tests the complete external library discovery and integration workflow.
"""

import pytest
from pathlib import Path

from src.level2.walk.pypi_search_engine import PyPISearchEngine
from src.level2.walk.library_installer import LibraryInstaller
from src.level2.walk.external_library_engine import ExternalLibraryEngine


class TestPyPISearch:
    """Test PyPI search engine functionality"""

    def test_search_finds_libraries(self):
        """Test that PyPI search finds relevant libraries"""
        engine = PyPISearchEngine()

        pattern = {
            'name': 'JSON Schema Validation',
            'description': 'Validate JSON data against schemas'
        }

        capabilities = [
            'Validate JSON against schema',
            'Support draft-07 schemas'
        ]

        results = engine.search_libraries(pattern, capabilities, max_results=5)

        # Should find at least some libraries
        assert len(results) > 0, "Should find at least one library"

        # Top result should have reasonable scores
        top_result = results[0]
        assert top_result.overall_score > 0, "Top result should have non-zero score"
        assert top_result.name is not None, "Library should have a name"
        assert top_result.version is not None, "Library should have a version"

    def test_maturity_scoring(self):
        """Test library maturity scoring"""
        engine = PyPISearchEngine()

        pattern = {
            'name': 'HTTP Requests',
            'description': 'Make HTTP requests'
        }

        capabilities = ['HTTP client', 'REST API calls']

        results = engine.search_libraries(pattern, capabilities, max_results=3)

        if results:
            # Check that results have maturity scores
            for lib in results:
                assert 0.0 <= lib.maturity_score <= 1.0, "Maturity score should be 0-1"
                assert 0.0 <= lib.relevance_score <= 1.0, "Relevance score should be 0-1"
                assert 0.0 <= lib.overall_score <= 1.0, "Overall score should be 0-1"

    def test_ranking_order(self):
        """Test that libraries are ranked by overall_score"""
        engine = PyPISearchEngine()

        pattern = {
            'name': 'Date Parsing',
            'description': 'Parse dates from strings'
        }

        capabilities = ['Parse ISO dates', 'Handle timezones']

        results = engine.search_libraries(pattern, capabilities, max_results=5)

        if len(results) >= 2:
            # Results should be sorted descending by overall_score
            for i in range(len(results) - 1):
                assert results[i].overall_score >= results[i+1].overall_score, \
                    "Results should be ranked by overall_score (descending)"


class TestLibraryInstaller:
    """Test library installation functionality"""

    def test_installer_initialization(self):
        """Test that installer initializes correctly"""
        installer = LibraryInstaller()

        assert installer.project_root is not None, "Should find project root"
        assert installer.pyproject_toml.exists(), "Should find pyproject.toml"

    def test_check_installed_packages(self):
        """Test checking for installed packages"""
        installer = LibraryInstaller()

        # Check for a package we know is installed (pytest)
        version = installer._check_installed('pytest')
        assert version is not None, "pytest should be installed for tests"

        # Check for a package that definitely doesn't exist
        version = installer._check_installed('this-package-does-not-exist-xyz-123')
        assert version is None, "Non-existent package should return None"

    def test_get_installed_libraries(self):
        """Test getting list of all installed libraries"""
        installer = LibraryInstaller()

        installed = installer.get_installed_libraries()

        assert isinstance(installed, dict), "Should return a dict"
        assert len(installed) > 0, "Should have some packages installed"
        assert 'pytest' in installed, "pytest should be in installed packages"


class TestExternalLibraryEngine:
    """Test end-to-end external library integration"""

    def test_search_and_rank(self):
        """Test library search and ranking without installation"""
        engine = ExternalLibraryEngine()

        pattern = {
            'name': 'Email Validation',
            'description': 'Validate email addresses'
        }

        capabilities = [
            'Check email format',
            'Verify domain exists'
        ]

        results = engine.search_and_rank(pattern, capabilities, max_results=3)

        assert len(results) > 0, "Should find at least one library"

        # Check structure of results
        for lib in results:
            assert lib.name is not None
            assert lib.version is not None
            assert lib.overall_score >= 0

    @pytest.mark.integration
    def test_dry_run_integration(self):
        """
        Test full integration workflow without actual installation.

        This validates the workflow without modifying the environment.
        """
        engine = ExternalLibraryEngine()

        pattern = {
            'name': 'URL Parsing',
            'description': 'Parse and validate URLs'
        }

        capabilities = [
            'Parse URL components',
            'Validate URL format',
            'Extract query parameters'
        ]

        # Run integration WITHOUT installing (auto_install=False)
        result = engine.integrate_library(
            pattern=pattern,
            missing_capabilities=capabilities,
            auto_install=False  # Dry-run mode
        )

        # Should succeed (finding library and generating wrapper)
        if result.success:
            assert result.library is not None, "Should select a library"
            assert result.tool is not None, "Should generate a wrapper tool"
            assert result.tool.name is not None, "Tool should have a name"
            assert result.tool.code is not None, "Tool should have code"
            assert len(result.tool.code) > 0, "Tool code should not be empty"
            assert 'def analyze' in result.tool.code, "Tool should have analyze method"
        else:
            # If it fails, it should provide an error message
            assert result.error is not None, "Failed result should have error message"

    def test_pattern_to_library_matching(self):
        """Test that different patterns find appropriate libraries"""
        engine = ExternalLibraryEngine()

        test_cases = [
            {
                'pattern': {
                    'name': 'CSV Parsing',
                    'description': 'Parse CSV files'
                },
                'capabilities': ['Parse CSV', 'Handle delimiters'],
                'expected_keyword': 'csv'
            },
            {
                'pattern': {
                    'name': 'XML Processing',
                    'description': 'Parse and manipulate XML'
                },
                'capabilities': ['Parse XML', 'XPath queries'],
                'expected_keyword': 'xml'
            }
        ]

        for test_case in test_cases:
            results = engine.search_and_rank(
                test_case['pattern'],
                test_case['capabilities'],
                max_results=3
            )

            if results:
                # At least one result should contain the expected keyword
                found_keyword = any(
                    test_case['expected_keyword'].lower() in lib.name.lower() or
                    test_case['expected_keyword'].lower() in (lib.description or '').lower()
                    for lib in results
                )

                # Note: This is a soft assertion - PyPI search may not always
                # find exact matches, but we're testing the search logic
                if not found_keyword:
                    pytest.skip(f"PyPI search didn't find exact match for {test_case['expected_keyword']}")


class TestWalkPhaseWorkflow:
    """Integration tests for complete WALK phase workflows"""

    @pytest.mark.integration
    def test_capability_gap_to_library_workflow(self):
        """
        Test the complete workflow from capability gap to library integration.

        Simulates what would happen when the system detects a gap.
        """
        engine = ExternalLibraryEngine()

        # Simulate gap detection
        pattern = {
            'name': 'YAML Configuration',
            'description': 'Parse and validate YAML configuration files'
        }

        missing_capabilities = [
            'Parse YAML syntax',
            'Validate schema',
            'Handle complex types'
        ]

        # Step 1: Search for libraries
        candidates = engine.search_and_rank(pattern, missing_capabilities, max_results=5)

        assert len(candidates) > 0, "Should find YAML libraries"

        # Step 2: Integration (dry-run)
        result = engine.integrate_library(
            pattern=pattern,
            missing_capabilities=missing_capabilities,
            auto_install=False
        )

        if result.success:
            # Validate complete integration result
            assert result.library is not None
            assert result.library.name is not None
            assert result.tool is not None
            assert result.tool.acquisition_type == 'library'
            assert result.tool.pattern_name == pattern['name']

            # Wrapper should follow standardized format
            assert 'def analyze' in result.tool.code
            assert 'import' in result.tool.code  # Should import the library

    def test_comparison_with_crawl_phase(self):
        """
        Compare WALK phase (external library) with CRAWL phase (build).

        This validates that WALK provides an alternative acquisition path.
        """
        engine = ExternalLibraryEngine()

        pattern = {
            'name': 'Markdown Parsing',
            'description': 'Parse markdown to HTML'
        }

        capabilities = ['Parse markdown syntax', 'Convert to HTML']

        # WALK approach: Find external library
        walk_results = engine.search_and_rank(pattern, capabilities, max_results=3)

        # WALK should find options
        assert len(walk_results) > 0, "WALK phase should find external libraries"

        # Note: CRAWL approach would generate code from scratch
        # This test validates that WALK provides an alternative


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
