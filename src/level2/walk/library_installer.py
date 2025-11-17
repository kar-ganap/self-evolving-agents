"""
Library Installer - Automates installation of PyPI packages using uv

Safely installs discovered libraries and tracks what's been installed.
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class InstallationResult:
    """
    Result of library installation attempt.

    Attributes:
        success: Whether installation succeeded
        package_name: Name of package
        version: Installed version
        error: Error message if failed
        already_installed: Whether package was already present
    """
    success: bool
    package_name: str
    version: Optional[str] = None
    error: Optional[str] = None
    already_installed: bool = False


class LibraryInstaller:
    """
    Handles automated installation of PyPI packages using uv.

    Uses uv instead of pip for faster, more reliable installations.
    Tracks installed packages to avoid redundant installations.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize library installer.

        Args:
            project_root: Project root directory (auto-detected if None)
        """
        self.project_root = project_root or self._find_project_root()
        self.pyproject_toml = self.project_root / "pyproject.toml"

    def _find_project_root(self) -> Path:
        """
        Find project root by locating pyproject.toml.

        Returns:
            Path to project root
        """
        current = Path(__file__).resolve()
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current
            current = current.parent

        raise ValueError("Could not find project root (no pyproject.toml found)")

    def install_library(
        self,
        package_name: str,
        version: Optional[str] = None,
        check_existing: bool = True
    ) -> InstallationResult:
        """
        Install a library using uv.

        Args:
            package_name: Name of package to install
            version: Specific version (None = latest)
            check_existing: Check if already installed before attempting

        Returns:
            InstallationResult with outcome
        """
        logger.info(f"Installing library: {package_name}")

        # Check if already installed (if requested)
        if check_existing:
            existing_version = self._check_installed(package_name)
            if existing_version:
                logger.info(f"  {package_name} already installed (v{existing_version})")
                return InstallationResult(
                    success=True,
                    package_name=package_name,
                    version=existing_version,
                    already_installed=True
                )

        # Build package specifier
        if version:
            package_spec = f"{package_name}=={version}"
        else:
            package_spec = package_name

        # Install using uv
        try:
            result = subprocess.run(
                ["uv", "add", package_spec],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                # Parse installed version from output
                installed_version = version or self._check_installed(package_name) or "unknown"

                logger.info(f"  ✓ Successfully installed {package_name} v{installed_version}")

                return InstallationResult(
                    success=True,
                    package_name=package_name,
                    version=installed_version
                )
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"  ✗ Installation failed: {error_msg}")

                return InstallationResult(
                    success=False,
                    package_name=package_name,
                    error=error_msg
                )

        except subprocess.TimeoutExpired:
            error_msg = "Installation timed out after 5 minutes"
            logger.error(f"  ✗ {error_msg}")

            return InstallationResult(
                success=False,
                package_name=package_name,
                error=error_msg
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"  ✗ Unexpected error: {error_msg}")

            return InstallationResult(
                success=False,
                package_name=package_name,
                error=error_msg
            )

    def _check_installed(self, package_name: str) -> Optional[str]:
        """
        Check if a package is already installed.

        Args:
            package_name: Package to check

        Returns:
            Installed version or None if not installed
        """
        try:
            # Use uv pip list to check
            result = subprocess.run(
                ["uv", "pip", "list", "--format=json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                import json
                packages = json.loads(result.stdout)

                for pkg in packages:
                    if pkg.get('name', '').lower() == package_name.lower():
                        return pkg.get('version')

            return None

        except Exception as e:
            logger.debug(f"Failed to check if {package_name} installed: {e}")
            return None

    def uninstall_library(self, package_name: str) -> bool:
        """
        Uninstall a library.

        Args:
            package_name: Package to uninstall

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Uninstalling library: {package_name}")

            result = subprocess.run(
                ["uv", "remove", package_name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.info(f"  ✓ Successfully uninstalled {package_name}")
                return True
            else:
                logger.error(f"  ✗ Uninstall failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"  ✗ Unexpected error: {e}")
            return False

    def get_installed_libraries(self) -> Dict[str, str]:
        """
        Get all installed libraries.

        Returns:
            Dict mapping package names to versions
        """
        try:
            result = subprocess.run(
                ["uv", "pip", "list", "--format=json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                import json
                packages = json.loads(result.stdout)

                return {
                    pkg['name']: pkg['version']
                    for pkg in packages
                }
            else:
                logger.error(f"Failed to list packages: {result.stderr}")
                return {}

        except Exception as e:
            logger.error(f"Error listing packages: {e}")
            return {}


# Example usage and testing
if __name__ == "__main__":
    print("Library Installer - Test Mode\n")

    installer = LibraryInstaller()

    print("=" * 80)
    print(f"Project Root: {installer.project_root}")
    print("=" * 80)

    # Test 1: Check currently installed libraries
    print("\nTest 1: List Installed Libraries")
    print("-" * 80)

    installed = installer.get_installed_libraries()
    print(f"Total packages: {len(installed)}")
    print(f"Sample packages:")
    for name, version in list(installed.items())[:10]:
        print(f"  - {name}: {version}")

    # Test 2: Check if specific library is installed
    print("\n" + "=" * 80)
    print("Test 2: Check Specific Library")
    print("=" * 80)

    test_package = "requests"
    version = installer._check_installed(test_package)
    if version:
        print(f"  ✓ {test_package} is installed (v{version})")
    else:
        print(f"  ✗ {test_package} is not installed")

    # Test 3: Dry-run installation check (don't actually install)
    print("\n" + "=" * 80)
    print("Test 3: Installation Check (read-only)")
    print("=" * 80)

    # Just check, don't install
    test_lib = "jsonschema"
    existing = installer._check_installed(test_lib)
    if existing:
        print(f"  {test_lib}: Already installed (v{existing})")
    else:
        print(f"  {test_lib}: Not installed (would require installation)")

    print("\n" + "=" * 80)
    print("\nNote: Skipping actual installation in test mode")
    print("To test installation, uncomment the install_library() call below:")
    print("  # result = installer.install_library('jsonschema')")
    print("=" * 80)
