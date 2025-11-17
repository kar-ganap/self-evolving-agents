"""
PyPI Search Engine - Discovers and ranks Python libraries from PyPI

Enables the system to search for external libraries that can fulfill
capability gaps instead of generating code from scratch.
"""

import requests
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LibraryCandidate:
    """
    A library candidate from PyPI search.

    Attributes:
        name: Package name (e.g., "requests")
        version: Latest version
        description: Short description
        author: Package author
        downloads: Monthly download count (if available)
        stars: GitHub stars (if available)
        license: Package license
        homepage: Project homepage URL
        repository: Repository URL (typically GitHub)
        last_updated: Last release date
        python_requires: Python version requirements
        dependencies: List of dependencies
        maturity_score: 0.0-1.0 score based on maturity signals
        relevance_score: 0.0-1.0 score based on search relevance
        overall_score: Combined ranking score
    """
    name: str
    version: str
    description: str
    author: str
    downloads: Optional[int] = None
    stars: Optional[int] = None
    license: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    last_updated: Optional[datetime] = None
    python_requires: Optional[str] = None
    dependencies: List[str] = None
    maturity_score: float = 0.0
    relevance_score: float = 0.0
    overall_score: float = 0.0


class PyPISearchEngine:
    """
    Search PyPI for libraries matching capability requirements.

    Uses PyPI's JSON API and search API to discover packages,
    then ranks them by relevance, maturity, and popularity.
    """

    PYPI_SEARCH_URL = "https://pypi.org/search/"
    PYPI_JSON_URL = "https://pypi.org/pypi/{package}/json"

    def __init__(self):
        """Initialize PyPI search engine."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'self-evolving-agent/1.0 (capability-evolution)'
        })

    def search_libraries(
        self,
        pattern: Dict,
        missing_capabilities: List[str],
        max_results: int = 10
    ) -> List[LibraryCandidate]:
        """
        Search PyPI for libraries matching the pattern and capabilities.

        Args:
            pattern: Pattern dictionary with 'name' and 'description'
            missing_capabilities: List of capability descriptions needed
            max_results: Maximum number of results to return

        Returns:
            List of LibraryCandidate ranked by overall_score (descending)
        """
        # Build search query from pattern and capabilities
        search_query = self._build_search_query(pattern, missing_capabilities)

        logger.info(f"Searching PyPI for: {search_query}")

        # Search PyPI
        raw_results = self._search_pypi(search_query, max_results * 2)

        if not raw_results:
            logger.warning(f"No PyPI results found for query: {search_query}")
            return []

        # Enrich with detailed metadata
        candidates = []
        for result in raw_results[:max_results * 2]:
            try:
                candidate = self._enrich_package_data(result)
                if candidate:
                    candidates.append(candidate)
            except Exception as e:
                logger.warning(f"Failed to enrich package {result.get('name')}: {e}")
                continue

        # Rank by maturity and relevance
        ranked_candidates = self._rank_candidates(candidates, pattern, missing_capabilities)

        return ranked_candidates[:max_results]

    def _build_search_query(self, pattern: Dict, missing_capabilities: List[str]) -> str:
        """
        Build search query from pattern and capabilities.

        Args:
            pattern: Pattern dictionary
            missing_capabilities: List of capabilities

        Returns:
            Search query string optimized for PyPI search
        """
        # Extract key terms from pattern name and description
        pattern_terms = []

        # Pattern name (e.g., "JSON Schema Validation" -> "json schema validation")
        pattern_terms.append(pattern['name'].lower())

        # Extract key nouns from capabilities
        capability_terms = []
        for cap in missing_capabilities[:3]:  # Use top 3 capabilities
            # Remove common verbs and get key nouns
            words = cap.lower().split()
            filtered = [w for w in words if w not in ['check', 'detect', 'validate', 'analyze', 'measure']]
            capability_terms.extend(filtered)

        # Combine (pattern name is most important)
        all_terms = pattern_terms + capability_terms[:3]
        query = ' '.join(all_terms)

        return query

    def _search_pypi(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search PyPI using their search API.

        Args:
            query: Search query
            limit: Max results to fetch

        Returns:
            List of raw package search results
        """
        try:
            # PyPI search endpoint (using their RSS feed for simplicity)
            # Alternative: could scrape search results or use PyPI XML-RPC (deprecated)
            # For production, consider using PyPI's BigQuery dataset

            # Using PyPI JSON API with search approximation
            # We'll search via package names and descriptions heuristically

            # For now, use a simple approach: try common package patterns
            # In production, would integrate with PyPI Warehouse API or BigQuery

            # Simplified approach: construct likely package names
            results = []

            # Try exact match first
            package_name = query.replace(' ', '-').lower()
            metadata = self._get_package_metadata(package_name)
            if metadata:
                results.append({'name': package_name, 'metadata': metadata})

            # Try variations
            variations = [
                query.replace(' ', '-'),
                query.replace(' ', '_'),
                query.replace(' ', ''),
                f"python-{query.replace(' ', '-')}",
                f"{query.replace(' ', '-')}-python",
            ]

            for variant in variations[:5]:
                variant = variant.lower()
                if variant != package_name:  # Skip duplicates
                    metadata = self._get_package_metadata(variant)
                    if metadata:
                        results.append({'name': variant, 'metadata': metadata})

            # Note: In production, would use proper PyPI search API
            # or integrate with libraries like pypi-simple or warehouse

            return results

        except Exception as e:
            logger.error(f"PyPI search failed: {e}")
            return []

    def _get_package_metadata(self, package_name: str) -> Optional[Dict]:
        """
        Get package metadata from PyPI JSON API.

        Args:
            package_name: Name of package

        Returns:
            Package metadata dict or None if not found
        """
        try:
            url = self.PYPI_JSON_URL.format(package=package_name)
            response = self.session.get(url, timeout=5)

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            logger.debug(f"Failed to fetch metadata for {package_name}: {e}")
            return None

    def _enrich_package_data(self, result: Dict) -> Optional[LibraryCandidate]:
        """
        Enrich package data with detailed metadata.

        Args:
            result: Raw search result with 'name' and 'metadata'

        Returns:
            LibraryCandidate with full metadata
        """
        metadata = result.get('metadata')
        if not metadata:
            return None

        info = metadata.get('info', {})

        # Extract basic info
        name = result['name']
        version = info.get('version', '0.0.0')
        description = info.get('summary', '')
        author = info.get('author', 'Unknown')
        license_type = info.get('license', 'Unknown')
        homepage = info.get('home_page') or info.get('project_url')

        # Parse repository URL
        repository = None
        project_urls = info.get('project_urls') or {}
        for key in ['Repository', 'Source', 'Source Code', 'GitHub']:
            if key in project_urls:
                repository = project_urls[key]
                break

        # Last updated
        releases = metadata.get('releases', {})
        last_updated = None
        if version in releases and releases[version]:
            upload_time = releases[version][0].get('upload_time_iso_8601')
            if upload_time:
                last_updated = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))

        # Python requirements
        python_requires = info.get('requires_python')

        # Dependencies (from latest version)
        dependencies = []
        requires_dist = info.get('requires_dist') or []
        for dep in requires_dist:
            # Parse "package (>=version)" format
            dep_name = dep.split()[0].split('[')[0]
            dependencies.append(dep_name)

        # Create candidate
        candidate = LibraryCandidate(
            name=name,
            version=version,
            description=description,
            author=author,
            license=license_type,
            homepage=homepage,
            repository=repository,
            last_updated=last_updated,
            python_requires=python_requires,
            dependencies=dependencies or []
        )

        # Calculate maturity score
        candidate.maturity_score = self._calculate_maturity_score(candidate, metadata)

        return candidate

    def _calculate_maturity_score(self, candidate: LibraryCandidate, metadata: Dict) -> float:
        """
        Calculate maturity score based on various signals.

        Args:
            candidate: LibraryCandidate to score
            metadata: Full PyPI metadata

        Returns:
            Maturity score from 0.0 to 1.0
        """
        score = 0.0

        # 1. Version maturity (0.2 points)
        version_parts = candidate.version.split('.')
        if len(version_parts) >= 3:
            major = int(version_parts[0]) if version_parts[0].isdigit() else 0
            if major >= 1:
                score += 0.2
            elif major == 0:
                minor = int(version_parts[1]) if version_parts[1].isdigit() else 0
                if minor >= 5:
                    score += 0.1  # Partial credit for 0.5+

        # 2. Recency (0.2 points)
        if candidate.last_updated:
            days_since_update = (datetime.now(candidate.last_updated.tzinfo) - candidate.last_updated).days
            if days_since_update < 90:
                score += 0.2  # Updated in last 3 months
            elif days_since_update < 365:
                score += 0.1  # Updated in last year

        # 3. License (0.1 points)
        if candidate.license and candidate.license.lower() not in ['unknown', 'none']:
            # Prefer permissive licenses
            permissive = ['mit', 'apache', 'bsd', 'python']
            if any(lic in candidate.license.lower() for lic in permissive):
                score += 0.1

        # 4. Documentation (0.2 points)
        if candidate.homepage or candidate.repository:
            score += 0.1
        info = metadata.get('info', {})
        if info.get('description') and len(info.get('description', '')) > 100:
            score += 0.1

        # 5. Dependencies (0.15 points)
        # Fewer dependencies is better (simpler, less risk)
        dep_count = len(candidate.dependencies)
        if dep_count == 0:
            score += 0.15
        elif dep_count <= 3:
            score += 0.1
        elif dep_count <= 10:
            score += 0.05

        # 6. Release count (0.15 points)
        releases = metadata.get('releases', {})
        release_count = len(releases)
        if release_count >= 20:
            score += 0.15
        elif release_count >= 10:
            score += 0.1
        elif release_count >= 5:
            score += 0.05

        return min(score, 1.0)

    def _rank_candidates(
        self,
        candidates: List[LibraryCandidate],
        pattern: Dict,
        missing_capabilities: List[str]
    ) -> List[LibraryCandidate]:
        """
        Rank candidates by relevance and maturity.

        Args:
            candidates: List of candidates to rank
            pattern: Pattern being searched for
            missing_capabilities: Capabilities needed

        Returns:
            Ranked list of candidates (descending by overall_score)
        """
        # Calculate relevance scores
        for candidate in candidates:
            candidate.relevance_score = self._calculate_relevance_score(
                candidate, pattern, missing_capabilities
            )

            # Overall score: weighted average (maturity 40%, relevance 60%)
            candidate.overall_score = (
                0.4 * candidate.maturity_score +
                0.6 * candidate.relevance_score
            )

        # Sort by overall score (descending)
        ranked = sorted(candidates, key=lambda c: c.overall_score, reverse=True)

        return ranked

    def _calculate_relevance_score(
        self,
        candidate: LibraryCandidate,
        pattern: Dict,
        missing_capabilities: List[str]
    ) -> float:
        """
        Calculate how relevant a library is to the pattern and capabilities.

        Args:
            candidate: Library candidate
            pattern: Pattern being searched for
            missing_capabilities: Capabilities needed

        Returns:
            Relevance score from 0.0 to 1.0
        """
        score = 0.0

        # 1. Name match (0.4 points)
        pattern_words = set(pattern['name'].lower().split())
        candidate_words = set(candidate.name.lower().replace('-', ' ').replace('_', ' ').split())

        name_overlap = len(pattern_words & candidate_words)
        if name_overlap > 0:
            score += 0.4 * (name_overlap / len(pattern_words))

        # 2. Description match (0.4 points)
        if candidate.description:
            desc_lower = candidate.description.lower()
            pattern_desc_lower = pattern.get('description', '').lower()

            # Check for keyword overlap
            pattern_keywords = set(pattern_desc_lower.split())
            desc_keywords = set(desc_lower.split())

            keyword_overlap = len(pattern_keywords & desc_keywords)
            if keyword_overlap > 0:
                score += 0.4 * min(keyword_overlap / max(len(pattern_keywords), 1), 1.0)

        # 3. Capability match (0.2 points)
        capability_text = ' '.join(missing_capabilities).lower()
        if candidate.description:
            # Check if capability terms appear in description
            matches = sum(1 for cap in missing_capabilities if cap.lower() in candidate.description.lower())
            if matches > 0:
                score += 0.2 * (matches / len(missing_capabilities))

        return min(score, 1.0)


# Example usage and testing
if __name__ == "__main__":
    print("PyPI Search Engine - Test Mode\n")

    engine = PyPISearchEngine()

    # Test case 1: JSON Schema Validation
    print("=" * 80)
    print("Test 1: Search for JSON Schema Validation library")
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

    results = engine.search_libraries(pattern, missing_capabilities, max_results=5)

    print(f"\nFound {len(results)} libraries:\n")
    for i, lib in enumerate(results, 1):
        print(f"{i}. {lib.name} v{lib.version}")
        print(f"   Description: {lib.description[:80]}...")
        print(f"   Maturity: {lib.maturity_score:.2f} | Relevance: {lib.relevance_score:.2f} | Overall: {lib.overall_score:.2f}")
        print(f"   License: {lib.license}")
        print(f"   Dependencies: {len(lib.dependencies)}")
        print()

    # Test case 2: Email Validation
    print("=" * 80)
    print("Test 2: Search for Email Validation library")
    print("=" * 80)

    pattern = {
        'name': 'Email Validation',
        'description': 'Validate email addresses according to RFC standards'
    }

    missing_capabilities = [
        'Check email format',
        'Verify domain exists',
        'Support internationalized emails'
    ]

    results = engine.search_libraries(pattern, missing_capabilities, max_results=5)

    print(f"\nFound {len(results)} libraries:\n")
    for i, lib in enumerate(results, 1):
        print(f"{i}. {lib.name} v{lib.version}")
        print(f"   Overall Score: {lib.overall_score:.2f}")
        print(f"   Last Updated: {lib.last_updated.strftime('%Y-%m-%d') if lib.last_updated else 'Unknown'}")
        print()

    print("=" * 80)
