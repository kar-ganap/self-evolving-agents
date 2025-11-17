"""
External Library Integration Engine - WALK Phase Component

Combines PyPI search, library installation, and wrapper generation
to autonomously integrate external libraries.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.level2.walk.pypi_search_engine import PyPISearchEngine, LibraryCandidate
from src.level2.walk.library_installer import LibraryInstaller, InstallationResult
from src.level2.crawl.tool_acquisition_engine import ToolAcquisitionEngine, GeneratedTool
from src.level2.crawl.build_vs_buy_analyzer import BuyOption, AcquisitionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExternalLibraryIntegrationResult:
    """
    Result of external library integration workflow.

    Attributes:
        success: Whether integration succeeded
        library: Selected library (if successful)
        installation_result: Result of installation attempt
        tool: Generated wrapper tool (if successful)
        error: Error message if failed
    """
    success: bool
    library: Optional[LibraryCandidate] = None
    installation_result: Optional[InstallationResult] = None
    tool: Optional[GeneratedTool] = None
    error: Optional[str] = None


class ExternalLibraryEngine:
    """
    Orchestrates the complete external library integration workflow.

    Flow:
    1. Search PyPI for matching libraries
    2. Rank and select best option
    3. Install library using uv
    4. Generate wrapper code using Gemini 2.5 Pro
    5. Return ready-to-use tool

    This is the WALK phase extension of the CRAWL capabilities.
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize external library engine.

        Args:
            gemini_api_key: Google API key for Gemini 2.5 Pro
        """
        self.search_engine = PyPISearchEngine()
        self.installer = LibraryInstaller()
        self.tool_engine = ToolAcquisitionEngine(gemini_api_key=gemini_api_key)

    def integrate_library(
        self,
        pattern: Dict,
        missing_capabilities: List[str],
        auto_install: bool = True
    ) -> ExternalLibraryIntegrationResult:
        """
        Search for, install, and wrap an external library.

        Args:
            pattern: Pattern dictionary with 'name' and 'description'
            missing_capabilities: List of missing capability descriptions
            auto_install: Whether to automatically install (default: True)

        Returns:
            ExternalLibraryIntegrationResult with integration outcome
        """
        pattern_name = pattern['name']

        logger.info(f"Starting external library integration for: {pattern_name}")

        try:
            # Step 1: Search PyPI
            logger.info("  [1/4] Searching PyPI...")
            candidates = self.search_engine.search_libraries(
                pattern=pattern,
                missing_capabilities=missing_capabilities,
                max_results=5
            )

            if not candidates:
                return ExternalLibraryIntegrationResult(
                    success=False,
                    error="No suitable libraries found on PyPI"
                )

            # Select best candidate (highest overall_score)
            best_library = candidates[0]

            logger.info(f"  ✓ Selected: {best_library.name} v{best_library.version}")
            logger.info(f"    Score: {best_library.overall_score:.2f} (maturity: {best_library.maturity_score:.2f}, relevance: {best_library.relevance_score:.2f})")

            # Step 2: Install library
            if auto_install:
                logger.info("  [2/4] Installing library...")
                install_result = self.installer.install_library(
                    package_name=best_library.name,
                    version=best_library.version,
                    check_existing=True
                )

                if not install_result.success:
                    return ExternalLibraryIntegrationResult(
                        success=False,
                        library=best_library,
                        installation_result=install_result,
                        error=f"Installation failed: {install_result.error}"
                    )

                if install_result.already_installed:
                    logger.info(f"  ✓ Already installed (v{install_result.version})")
                else:
                    logger.info(f"  ✓ Successfully installed v{install_result.version}")
            else:
                # Skip installation (for dry-run)
                logger.info("  [2/4] Skipping installation (auto_install=False)")
                install_result = InstallationResult(
                    success=True,
                    package_name=best_library.name,
                    version=best_library.version,
                    already_installed=False
                )

            # Step 3: Create BuyOption for wrapper generation
            buy_option = BuyOption(
                source=best_library.name,
                acquisition_type=AcquisitionType.LIBRARY,
                cost_per_month=0.0,  # Free library
                setup_time=300,  # 5 minutes estimated
                maturity_score=best_library.maturity_score,
                details={
                    'version': best_library.version,
                    'license': best_library.license,
                    'homepage': best_library.homepage,
                    'repository': best_library.repository,
                    'dependencies': best_library.dependencies
                }
            )

            # Step 4: Generate wrapper code
            logger.info("  [3/4] Generating wrapper code with Gemini 2.5 Pro...")
            tool = self.tool_engine._acquire_library(pattern, buy_option)

            logger.info(f"  ✓ Wrapper generated: {tool.name}")
            logger.info(f"    Code length: {len(tool.code)} characters")

            # Step 5: Save wrapper to file
            logger.info("  [4/4] Saving wrapper...")
            saved_path = self.tool_engine.save_tool(tool)
            logger.info(f"  ✓ Saved to: {saved_path}")

            return ExternalLibraryIntegrationResult(
                success=True,
                library=best_library,
                installation_result=install_result,
                tool=tool
            )

        except Exception as e:
            logger.error(f"Integration failed: {e}")
            return ExternalLibraryIntegrationResult(
                success=False,
                error=str(e)
            )

    def search_and_rank(
        self,
        pattern: Dict,
        missing_capabilities: List[str],
        max_results: int = 10
    ) -> List[LibraryCandidate]:
        """
        Search and rank libraries without installing.

        Useful for presenting options to user before committing.

        Args:
            pattern: Pattern dictionary
            missing_capabilities: List of capabilities needed
            max_results: Maximum number of results

        Returns:
            List of ranked LibraryCandidate objects
        """
        return self.search_engine.search_libraries(
            pattern=pattern,
            missing_capabilities=missing_capabilities,
            max_results=max_results
        )


# Example usage and testing
if __name__ == "__main__":
    print("External Library Integration Engine - Test Mode\n")

    engine = ExternalLibraryEngine()

    # Test case 1: JSON Schema Validation
    print("=" * 80)
    print("Test 1: JSON Schema Validation (search only)")
    print("=" * 80)

    pattern = {
        'name': 'JSON Schema Validation',
        'description': 'Validate JSON data against schemas'
    }

    missing_capabilities = [
        'Validate JSON against schema',
        'Support draft-07 schemas',
        'Provide detailed error messages'
    ]

    # Step 1: Search and rank (no installation)
    print("\nSearching PyPI...")
    candidates = engine.search_and_rank(pattern, missing_capabilities, max_results=3)

    print(f"\nTop {len(candidates)} libraries:\n")
    for i, lib in enumerate(candidates, 1):
        print(f"{i}. {lib.name} v{lib.version}")
        print(f"   Overall Score: {lib.overall_score:.2f}")
        print(f"   Maturity: {lib.maturity_score:.2f} | Relevance: {lib.relevance_score:.2f}")
        print(f"   License: {lib.license}")
        print(f"   Dependencies: {len(lib.dependencies)}")
        print()

    # Test case 2: Email Validation (full integration, dry-run)
    print("\n" + "=" * 80)
    print("Test 2: Email Validation (dry-run integration)")
    print("=" * 80)

    pattern2 = {
        'name': 'Email Validation',
        'description': 'Validate email addresses according to RFC standards'
    }

    missing_capabilities2 = [
        'Check email format',
        'Verify domain exists',
        'Support internationalized emails'
    ]

    print("\nRunning integration workflow (without actual installation)...")
    result = engine.integrate_library(
        pattern=pattern2,
        missing_capabilities=missing_capabilities2,
        auto_install=False  # Dry-run mode
    )

    if result.success:
        print("\n✓ Integration would succeed!")
        print(f"  Selected Library: {result.library.name} v{result.library.version}")
        print(f"  Tool Name: {result.tool.name}")
        print(f"  Wrapper Code: {len(result.tool.code)} characters")
    else:
        print(f"\n✗ Integration failed: {result.error}")

    print("\n" + "=" * 80)
    print("\nNote: To test actual installation, set auto_install=True")
    print("=" * 80)
