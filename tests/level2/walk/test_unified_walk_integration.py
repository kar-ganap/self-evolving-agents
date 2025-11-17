"""
Comprehensive integration tests for Unified WALK Orchestrator.

Tests the complete WALK phase workflow including:
- External library acquisition (PyPI)
- External API acquisition
- Tool memory integration
- Cost management integration
- Budget enforcement
- Performance tracking
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.level2.walk.unified_walk_orchestrator import (
    UnifiedWALKOrchestrator,
    AcquisitionSource,
    WALKAcquisitionResult
)
from src.level2.walk.cost_management_system import BudgetPeriod
from src.level2.walk.external_library_engine import ExternalLibraryIntegrationResult
from src.level2.walk.external_api_engine import ExternalAPIIntegrationResult
from src.level2.walk.pypi_search_engine import LibraryCandidate
from src.level2.walk.api_discovery_engine import APICandidate, AuthType
from src.level2.crawl.tool_acquisition_engine import GeneratedTool


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory for tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def orchestrator_no_tracking():
    """Orchestrator without cost tracking or tool memory."""
    return UnifiedWALKOrchestrator(
        gemini_api_key=None,
        enable_cost_tracking=False,
        enable_tool_memory=False
    )


@pytest.fixture
def orchestrator_with_tracking(temp_data_dir):
    """Orchestrator with all tracking enabled."""
    orchestrator = UnifiedWALKOrchestrator(
        gemini_api_key="test-key",
        enable_cost_tracking=True,
        enable_tool_memory=True
    )

    # Override database paths to use temp directory
    if orchestrator.cost_system:
        orchestrator.cost_system.db_path = temp_data_dir / "costs.db"
        orchestrator.cost_system._init_database()

    if orchestrator.tool_memory:
        orchestrator.tool_memory.db_path = temp_data_dir / "tool_memory.db"
        orchestrator.tool_memory._init_database()

    return orchestrator


@pytest.fixture
def sample_pattern():
    """Sample pattern for testing."""
    return {
        'name': 'JSON Schema Validation',
        'description': 'Validate JSON data against schemas'
    }


@pytest.fixture
def sample_capabilities():
    """Sample missing capabilities."""
    return [
        'Validate JSON against schema',
        'Support draft-07 schemas'
    ]


# =============================================================================
# Test 1: Initialization
# =============================================================================

def test_orchestrator_init_no_tracking():
    """Test orchestrator initialization without tracking."""
    orch = UnifiedWALKOrchestrator(
        enable_cost_tracking=False,
        enable_tool_memory=False
    )

    assert orch.library_engine is not None
    assert orch.api_engine is not None
    assert orch.cost_system is None
    assert orch.tool_memory is None


def test_orchestrator_init_with_tracking():
    """Test orchestrator initialization with tracking enabled."""
    orch = UnifiedWALKOrchestrator(
        enable_cost_tracking=True,
        enable_tool_memory=True
    )

    assert orch.library_engine is not None
    assert orch.api_engine is not None
    assert orch.cost_system is not None
    assert orch.tool_memory is not None


# =============================================================================
# Test 2: Library Acquisition
# =============================================================================

def test_library_acquisition_success(orchestrator_no_tracking, sample_pattern, sample_capabilities):
    """Test successful library acquisition from PyPI."""
    # Create mock objects with exact field names
    mock_library = LibraryCandidate(
        name="jsonschema",
        version="4.17.3",
        description="JSON Schema validator",
        author="Julian Berman",
        homepage="https://github.com/python-jsonschema/jsonschema",
        license="MIT",
        downloads=10000000,
        maturity_score=0.95,
        relevance_score=0.88
    )

    mock_tool = GeneratedTool(
        name="JSONSchemaValidator",
        code="def validate_json(data, schema): pass",
        pattern_name="JSON Schema Validation",
        acquisition_type="library",
        metadata={}
    )

    mock_result = ExternalLibraryIntegrationResult(
        success=True,
        library=mock_library,
        installation_result=None,
        tool=mock_tool,
        error=None
    )

    with patch.object(orchestrator_no_tracking.library_engine, 'integrate_library', return_value=mock_result):
        result = orchestrator_no_tracking.acquire_external_resource(
            pattern=sample_pattern,
            missing_capabilities=sample_capabilities,
            prefer_source=AcquisitionSource.LIBRARY
        )

    assert result.success is True
    assert result.source == AcquisitionSource.LIBRARY
    assert result.tool_name == "JSONSchemaValidator"
    assert result.cost == 0.02
    assert result.estimated_monthly_cost == 0.0
    assert 'library_name' in result.metadata


def test_library_acquisition_failure(orchestrator_no_tracking, sample_pattern, sample_capabilities):
    """Test library acquisition failure."""
    mock_library_result = ExternalLibraryIntegrationResult(
        success=False,
        library=None,
        installation_result=None,
        tool=None,
        error="No suitable library found"
    )

    mock_api_result = ExternalAPIIntegrationResult(
        success=False,
        api=None,
        tool=None,
        error="No suitable API found"
    )

    with patch.object(orchestrator_no_tracking.library_engine, 'integrate_library', return_value=mock_library_result), \
         patch.object(orchestrator_no_tracking.api_engine, 'integrate_api', return_value=mock_api_result):
        result = orchestrator_no_tracking.acquire_external_resource(
            pattern=sample_pattern,
            missing_capabilities=sample_capabilities,
            prefer_source=AcquisitionSource.LIBRARY
        )

    assert result.success is False
    # When prefer_source=LIBRARY but library fails, it only tries library (not API)
    # So the error is from library failure
    assert "No suitable library found" in result.error or "No suitable external resources found" in result.error


# =============================================================================
# Test 3: API Acquisition
# =============================================================================

def test_api_acquisition_success(orchestrator_no_tracking, sample_pattern, sample_capabilities):
    """Test successful API acquisition."""
    mock_api = APICandidate(
        name="JSON Validator API",
        base_url="https://api.jsonvalidator.com",
        description="Cloud JSON validation",
        auth_type=AuthType.API_KEY,
        pricing="freemium",
        maturity_score=0.80
    )

    mock_tool = GeneratedTool(
        name="JSONValidatorAPI",
        code="def validate_json_api(data, schema): pass",
        pattern_name="JSON Schema Validation",
        acquisition_type="api",
        metadata={}
    )

    mock_result = ExternalAPIIntegrationResult(
        success=True,
        api=mock_api,
        tool=mock_tool,
        error=None
    )

    with patch.object(orchestrator_no_tracking.api_engine, 'integrate_api', return_value=mock_result):
        result = orchestrator_no_tracking.acquire_external_resource(
            pattern=sample_pattern,
            missing_capabilities=sample_capabilities,
            prefer_source=AcquisitionSource.API
        )

    assert result.success is True
    assert result.source == AcquisitionSource.API
    assert result.tool_name == "JSONValidatorAPI"
    assert result.estimated_monthly_cost == 0.0  # Freemium


def test_api_acquisition_paid(orchestrator_no_tracking, sample_pattern, sample_capabilities):
    """Test acquisition of paid API."""
    mock_api = APICandidate(
        name="Premium Validator",
        base_url="https://api.premium.com",
        description="Premium validation service",
        auth_type=AuthType.OAUTH2,
        pricing="paid",
        maturity_score=0.90
    )

    mock_tool = GeneratedTool(
        name="PremiumValidator",
        code="def validate_premium(data): pass",
        pattern_name="JSON Schema Validation",
        acquisition_type="api",
        metadata={}
    )

    mock_result = ExternalAPIIntegrationResult(
        success=True,
        api=mock_api,
        tool=mock_tool,
        error=None
    )

    with patch.object(orchestrator_no_tracking.api_engine, 'integrate_api', return_value=mock_result):
        result = orchestrator_no_tracking.acquire_external_resource(
            pattern=sample_pattern,
            missing_capabilities=sample_capabilities,
            prefer_source=AcquisitionSource.API
        )

    assert result.success is True
    assert result.estimated_monthly_cost == 30.0  # Paid API estimate


# =============================================================================
# Test 4: Fallback Strategy
# =============================================================================

def test_fallback_library_to_api(orchestrator_no_tracking, sample_pattern, sample_capabilities):
    """Test fallback from library to API when library fails."""
    mock_library_result = ExternalLibraryIntegrationResult(
        success=False,
        library=None,
        installation_result=None,
        tool=None,
        error="No suitable library found"
    )

    mock_api = APICandidate(
        name="Validator API",
        base_url="https://api.validator.com",
        description="Validation API",
        auth_type=AuthType.API_KEY,
        pricing="freemium",
        maturity_score=0.75
    )

    mock_tool = GeneratedTool(
        name="ValidatorAPI",
        code="def validate_api(data): pass",
        pattern_name="JSON Schema Validation",
        acquisition_type="api",
        metadata={}
    )

    mock_api_result = ExternalAPIIntegrationResult(
        success=True,
        api=mock_api,
        tool=mock_tool,
        error=None
    )

    with patch.object(orchestrator_no_tracking.library_engine, 'integrate_library', return_value=mock_library_result), \
         patch.object(orchestrator_no_tracking.api_engine, 'integrate_api', return_value=mock_api_result):

        result = orchestrator_no_tracking.acquire_external_resource(
            pattern=sample_pattern,
            missing_capabilities=sample_capabilities,
            prefer_source=None  # Should try library first, then API
        )

    assert result.success is True
    assert result.source == AcquisitionSource.API  # Fell back to API


# =============================================================================
# Test 5: Budget Enforcement
# =============================================================================

def test_budget_blocks_acquisition(orchestrator_with_tracking, sample_pattern, sample_capabilities):
    """Test that insufficient budget blocks acquisition."""
    orchestrator_with_tracking.cost_system.set_budget(BudgetPeriod.DAILY, 0.01)

    result = orchestrator_with_tracking.acquire_external_resource(
        pattern=sample_pattern,
        missing_capabilities=sample_capabilities,
        max_cost=0.02
    )

    assert result.success is False
    assert "Insufficient budget" in result.error


def test_budget_allows_acquisition(orchestrator_with_tracking, sample_pattern, sample_capabilities):
    """Test that sufficient budget allows acquisition."""
    # Set all budget periods to accommodate default max_cost of 50
    orchestrator_with_tracking.cost_system.set_budget(BudgetPeriod.DAILY, 100.0)
    orchestrator_with_tracking.cost_system.set_budget(BudgetPeriod.WEEKLY, 100.0)
    orchestrator_with_tracking.cost_system.set_budget(BudgetPeriod.MONTHLY, 200.0)

    mock_library = LibraryCandidate(
        name="testlib",
        version="1.0.0",
        description="Test library",
        author="Test",
        homepage="https://test.com",
        license="MIT",
        maturity_score=0.80,
        relevance_score=0.75
    )

    mock_tool = GeneratedTool(
        name="TestTool",
        code="def test(): pass",
        pattern_name="JSON Schema Validation",
        acquisition_type="library",
        metadata={}
    )

    mock_result = ExternalLibraryIntegrationResult(
        success=True,
        library=mock_library,
        installation_result=None,
        tool=mock_tool,
        error=None
    )

    with patch.object(orchestrator_with_tracking.library_engine, 'integrate_library', return_value=mock_result):
        result = orchestrator_with_tracking.acquire_external_resource(
            pattern=sample_pattern,
            missing_capabilities=sample_capabilities,
            prefer_source=AcquisitionSource.LIBRARY
        )

    assert result.success is True

    # Verify cost was recorded
    status = orchestrator_with_tracking.cost_system.get_budget_status()
    assert status['daily']['current_spend'] > 0.0


# =============================================================================
# Test 6: Tool Memory Integration
# =============================================================================

def test_tool_memory_records_acquisition(orchestrator_with_tracking, sample_pattern, sample_capabilities):
    """Test that successful acquisition is recorded in tool memory."""
    # Set all budget periods to accommodate default max_cost of 50
    orchestrator_with_tracking.cost_system.set_budget(BudgetPeriod.DAILY, 100.0)
    orchestrator_with_tracking.cost_system.set_budget(BudgetPeriod.WEEKLY, 100.0)
    orchestrator_with_tracking.cost_system.set_budget(BudgetPeriod.MONTHLY, 200.0)

    mock_library = LibraryCandidate(
        name="memorylib",
        version="1.0.0",
        description="Memory test",
        author="Test",
        homepage="https://test.com",
        license="MIT",
        maturity_score=0.80,
        relevance_score=0.75
    )

    mock_tool = GeneratedTool(
        name="MemoryTool",
        code="def memory(): pass",
        pattern_name="JSON Schema Validation",
        acquisition_type="library",
        metadata={}
    )

    mock_result = ExternalLibraryIntegrationResult(
        success=True,
        library=mock_library,
        installation_result=None,
        tool=mock_tool,
        error=None
    )

    with patch.object(orchestrator_with_tracking.library_engine, 'integrate_library', return_value=mock_result):
        result = orchestrator_with_tracking.acquire_external_resource(
            pattern=sample_pattern,
            missing_capabilities=sample_capabilities,
            prefer_source=AcquisitionSource.LIBRARY
        )

    assert result.success is True

    # Verify tool memory recorded usage
    metrics = orchestrator_with_tracking.tool_memory.get_tool_metrics(
        "MemoryTool",
        "JSON Schema Validation"
    )

    assert metrics is not None
    assert metrics.total_uses == 1
    assert metrics.success_rate == 100.0


# =============================================================================
# Test 7: Performance Recording
# =============================================================================

def test_record_tool_performance(orchestrator_with_tracking):
    """Test manual performance recording."""
    orchestrator_with_tracking.record_tool_performance(
        tool_name="TestTool",
        pattern_name="Test Pattern",
        success=True,
        latency_ms=250.0,
        score=0.85
    )

    metrics = orchestrator_with_tracking.tool_memory.get_tool_metrics(
        "TestTool",
        "Test Pattern"
    )

    assert metrics is not None
    assert metrics.total_uses == 1
    assert metrics.success_rate == 100.0
    assert metrics.avg_latency_ms == 250.0
    assert metrics.avg_score == 0.85


# =============================================================================
# Test 8: Summary Methods
# =============================================================================

def test_get_cost_summary_disabled(orchestrator_no_tracking):
    """Test cost summary when cost tracking is disabled."""
    summary = orchestrator_no_tracking.get_cost_summary()

    assert summary['enabled'] is False


def test_get_cost_summary_enabled(orchestrator_with_tracking):
    """Test cost summary when cost tracking is enabled."""
    orchestrator_with_tracking.cost_system.set_budget(BudgetPeriod.DAILY, 10.0)
    orchestrator_with_tracking.cost_system.set_budget(BudgetPeriod.MONTHLY, 200.0)

    summary = orchestrator_with_tracking.get_cost_summary()

    assert summary['enabled'] is True
    assert 'budgets' in summary
    assert 'daily' in summary['budgets']
    assert 'monthly' in summary['budgets']


def test_get_tool_performance_summary(orchestrator_with_tracking):
    """Test performance summary."""
    orchestrator_with_tracking.record_tool_performance(
        tool_name="PerformanceTool",
        pattern_name="Performance Pattern",
        success=True,
        latency_ms=300.0,
        score=0.88
    )

    summary = orchestrator_with_tracking.get_tool_performance_summary()

    assert summary['enabled'] is True
    assert 'total_tools_tracked' in summary
    assert summary['total_tools_tracked'] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
