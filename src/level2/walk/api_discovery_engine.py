"""
API Discovery Engine - Discovers and ranks third-party APIs

Searches multiple sources for APIs that can fulfill capability gaps:
- APIs.guru (OpenAPI directory)
- Public API lists
- Curated API collections

Note: RapidAPI requires paid subscription, so this implementation
focuses on free/open API discovery sources.
"""

import requests
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthType(Enum):
    """API authentication types"""
    NONE = "none"
    API_KEY = "apiKey"
    OAUTH2 = "oauth2"
    BEARER = "bearer"
    BASIC = "basic"


@dataclass
class APICandidate:
    """
    An API candidate from discovery.

    Attributes:
        name: API name
        description: Short description
        base_url: API base URL
        category: API category (e.g., "weather", "finance")
        auth_type: Authentication method required
        pricing: Pricing model (free, freemium, paid)
        rate_limit: Rate limit info (if available)
        documentation_url: Link to docs
        openapi_spec_url: OpenAPI/Swagger spec URL (if available)
        maturity_score: 0.0-1.0 score based on maturity signals
        relevance_score: 0.0-1.0 score based on search relevance
        overall_score: Combined ranking score
        metadata: Additional API metadata
    """
    name: str
    description: str
    base_url: str
    category: Optional[str] = None
    auth_type: AuthType = AuthType.NONE
    pricing: str = "unknown"
    rate_limit: Optional[str] = None
    documentation_url: Optional[str] = None
    openapi_spec_url: Optional[str] = None
    maturity_score: float = 0.0
    relevance_score: float = 0.0
    overall_score: float = 0.0
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class APIDiscoveryEngine:
    """
    Discovers APIs from multiple sources.

    Sources:
    1. APIs.guru - Comprehensive OpenAPI directory
    2. Public APIs GitHub repo - Curated list
    3. Custom API catalog (future)
    """

    APIS_GURU_URL = "https://api.apis.guru/v2/list.json"
    PUBLIC_APIS_URL = "https://api.publicapis.org/entries"

    def __init__(self):
        """Initialize API discovery engine."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'self-evolving-agent/1.0 (api-discovery)'
        })
        self._apis_guru_cache = None
        self._public_apis_cache = None

    def search_apis(
        self,
        pattern: Dict,
        missing_capabilities: List[str],
        max_results: int = 10
    ) -> List[APICandidate]:
        """
        Search for APIs matching the pattern and capabilities.

        Args:
            pattern: Pattern dictionary with 'name' and 'description'
            missing_capabilities: List of capability descriptions needed
            max_results: Maximum number of results to return

        Returns:
            List of APICandidate ranked by overall_score (descending)
        """
        # Build search query
        search_query = self._build_search_query(pattern, missing_capabilities)

        logger.info(f"Searching APIs for: {search_query}")

        # Search multiple sources
        candidates = []

        # Source 1: APIs.guru (OpenAPI directory)
        apis_guru_results = self._search_apis_guru(search_query)
        candidates.extend(apis_guru_results)

        # Source 2: Public APIs list
        public_api_results = self._search_public_apis(search_query)
        candidates.extend(public_api_results)

        if not candidates:
            logger.warning(f"No APIs found for query: {search_query}")
            return []

        # Calculate relevance scores
        for candidate in candidates:
            candidate.relevance_score = self._calculate_relevance_score(
                candidate, pattern, missing_capabilities
            )

        # Calculate maturity scores
        for candidate in candidates:
            candidate.maturity_score = self._calculate_maturity_score(candidate)

        # Overall score: weighted average (maturity 30%, relevance 70%)
        # APIs are riskier than libraries, so relevance is more important
        for candidate in candidates:
            candidate.overall_score = (
                0.3 * candidate.maturity_score +
                0.7 * candidate.relevance_score
            )

        # Sort by overall score and return top results
        ranked = sorted(candidates, key=lambda c: c.overall_score, reverse=True)

        # Deduplicate by name (keep highest scoring)
        seen_names = set()
        deduplicated = []
        for api in ranked:
            if api.name not in seen_names:
                seen_names.add(api.name)
                deduplicated.append(api)

        return deduplicated[:max_results]

    def _build_search_query(self, pattern: Dict, missing_capabilities: List[str]) -> str:
        """
        Build search query from pattern and capabilities.

        Args:
            pattern: Pattern dictionary
            missing_capabilities: List of capabilities

        Returns:
            Search query string
        """
        # Extract key terms from pattern name
        pattern_terms = pattern['name'].lower().split()

        # Extract key terms from capabilities (top 2)
        capability_terms = []
        for cap in missing_capabilities[:2]:
            words = cap.lower().split()
            # Filter common verbs
            filtered = [w for w in words if w not in ['check', 'validate', 'analyze', 'detect']]
            capability_terms.extend(filtered[:2])

        # Combine
        all_terms = pattern_terms + capability_terms[:3]
        query = ' '.join(all_terms)

        return query

    def _search_apis_guru(self, query: str) -> List[APICandidate]:
        """
        Search APIs.guru directory.

        APIs.guru provides OpenAPI specs for thousands of public APIs.

        Args:
            query: Search query

        Returns:
            List of API candidates
        """
        try:
            # Lazy load APIs.guru list (cached)
            if self._apis_guru_cache is None:
                logger.info("Fetching APIs.guru directory...")
                response = self.session.get(self.APIS_GURU_URL, timeout=10)
                if response.status_code == 200:
                    self._apis_guru_cache = response.json()
                else:
                    logger.error(f"APIs.guru fetch failed: {response.status_code}")
                    return []

            # Search through APIs
            query_terms = set(query.lower().split())
            candidates = []

            for api_key, api_data in list(self._apis_guru_cache.items())[:1000]:
                # Get latest version
                versions = api_data.get('versions', {})
                if not versions:
                    continue

                latest_version = sorted(versions.keys())[-1]
                version_data = versions[latest_version]

                # Extract info
                info = version_data.get('info', {})
                name = info.get('title', api_key)
                description = info.get('description', '')
                base_url = version_data.get('swaggerUrl', '').split('/swagger')[0]

                # Simple keyword matching
                searchable_text = f"{name} {description}".lower()
                if not any(term in searchable_text for term in query_terms):
                    continue

                # Determine auth type
                auth_type = self._detect_auth_type(version_data)

                # Create candidate
                candidate = APICandidate(
                    name=name,
                    description=description[:200],
                    base_url=base_url or "https://api.example.com",
                    auth_type=auth_type,
                    pricing="unknown",
                    openapi_spec_url=version_data.get('swaggerUrl'),
                    documentation_url=info.get('x-origin', [{}])[0].get('url') if info.get('x-origin') else None,
                    metadata={
                        'source': 'apis.guru',
                        'version': latest_version,
                        'contact': info.get('contact', {})
                    }
                )

                candidates.append(candidate)

            logger.info(f"APIs.guru: Found {len(candidates)} matches")
            return candidates[:20]  # Limit to top 20

        except Exception as e:
            logger.error(f"APIs.guru search failed: {e}")
            return []

    def _search_public_apis(self, query: str) -> List[APICandidate]:
        """
        Search public-apis.org list.

        A curated list of free public APIs.

        Args:
            query: Search query

        Returns:
            List of API candidates
        """
        try:
            # Fetch public APIs list
            if self._public_apis_cache is None:
                logger.info("Fetching public-apis.org list...")
                response = self.session.get(self.PUBLIC_APIS_URL, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self._public_apis_cache = data.get('entries', [])
                else:
                    logger.error(f"Public APIs fetch failed: {response.status_code}")
                    return []

            # Search through APIs
            query_terms = set(query.lower().split())
            candidates = []

            for api in self._public_apis_cache:
                # Extract info
                name = api.get('API', '')
                description = api.get('Description', '')
                category = api.get('Category', '')

                # Keyword matching
                searchable_text = f"{name} {description} {category}".lower()
                if not any(term in searchable_text for term in query_terms):
                    continue

                # Determine auth type
                auth_str = api.get('Auth', '').lower()
                if auth_str == 'apikey' or 'api' in auth_str:
                    auth_type = AuthType.API_KEY
                elif 'oauth' in auth_str:
                    auth_type = AuthType.OAUTH2
                else:
                    auth_type = AuthType.NONE

                # Create candidate
                candidate = APICandidate(
                    name=name,
                    description=description,
                    base_url=api.get('Link', 'https://api.example.com'),
                    category=category,
                    auth_type=auth_type,
                    pricing="free",  # Public APIs list is all free
                    documentation_url=api.get('Link'),
                    metadata={
                        'source': 'public-apis',
                        'https': api.get('HTTPS', False),
                        'cors': api.get('Cors', 'unknown')
                    }
                )

                candidates.append(candidate)

            logger.info(f"Public APIs: Found {len(candidates)} matches")
            return candidates[:20]  # Limit to top 20

        except Exception as e:
            logger.error(f"Public APIs search failed: {e}")
            return []

    def _detect_auth_type(self, version_data: Dict) -> AuthType:
        """
        Detect authentication type from OpenAPI spec.

        Args:
            version_data: OpenAPI version data

        Returns:
            AuthType enum value
        """
        security_definitions = version_data.get('securityDefinitions', {})

        if not security_definitions:
            return AuthType.NONE

        # Check first security definition
        for sec_def in security_definitions.values():
            sec_type = sec_def.get('type', '').lower()
            if sec_type == 'apikey':
                return AuthType.API_KEY
            elif sec_type == 'oauth2':
                return AuthType.OAUTH2
            elif sec_type == 'http':
                scheme = sec_def.get('scheme', '').lower()
                if scheme == 'bearer':
                    return AuthType.BEARER
                elif scheme == 'basic':
                    return AuthType.BASIC

        return AuthType.NONE

    def _calculate_relevance_score(
        self,
        candidate: APICandidate,
        pattern: Dict,
        missing_capabilities: List[str]
    ) -> float:
        """
        Calculate how relevant an API is to the pattern.

        Args:
            candidate: API candidate
            pattern: Pattern being searched for
            missing_capabilities: Capabilities needed

        Returns:
            Relevance score from 0.0 to 1.0
        """
        score = 0.0

        # 1. Name match (0.4 points)
        pattern_words = set(pattern['name'].lower().split())
        candidate_name_words = set(candidate.name.lower().split())

        name_overlap = len(pattern_words & candidate_name_words)
        if name_overlap > 0:
            score += 0.4 * (name_overlap / len(pattern_words))

        # 2. Description match (0.4 points)
        if candidate.description:
            desc_lower = candidate.description.lower()
            pattern_desc_lower = pattern.get('description', '').lower()

            pattern_keywords = set(pattern_desc_lower.split())
            desc_keywords = set(desc_lower.split())

            keyword_overlap = len(pattern_keywords & desc_keywords)
            if keyword_overlap > 0:
                score += 0.4 * min(keyword_overlap / max(len(pattern_keywords), 1), 1.0)

        # 3. Category match (0.2 points)
        if candidate.category:
            pattern_text = pattern['name'].lower()
            if candidate.category.lower() in pattern_text or pattern_text in candidate.category.lower():
                score += 0.2

        return min(score, 1.0)

    def _calculate_maturity_score(self, candidate: APICandidate) -> float:
        """
        Calculate maturity score based on API metadata.

        Args:
            candidate: API candidate

        Returns:
            Maturity score from 0.0 to 1.0
        """
        score = 0.0

        # 1. Has OpenAPI spec (0.3 points)
        if candidate.openapi_spec_url:
            score += 0.3

        # 2. Free pricing (0.2 points)
        if candidate.pricing == "free":
            score += 0.2

        # 3. Has documentation (0.2 points)
        if candidate.documentation_url:
            score += 0.2

        # 4. HTTPS support (0.15 points)
        if candidate.metadata.get('https') == True:
            score += 0.15
        elif 'https://' in candidate.base_url.lower():
            score += 0.15

        # 5. Authentication present (0.15 points)
        # Having auth indicates a more mature API
        if candidate.auth_type != AuthType.NONE:
            score += 0.15

        return min(score, 1.0)


# Example usage and testing
if __name__ == "__main__":
    print("API Discovery Engine - Test Mode\n")

    engine = APIDiscoveryEngine()

    # Test case 1: Weather API search
    print("=" * 80)
    print("Test 1: Search for Weather APIs")
    print("=" * 80)

    pattern = {
        'name': 'Weather Data',
        'description': 'Get current weather and forecasts'
    }

    capabilities = [
        'Get current weather',
        'Get weather forecast',
        'Search by location'
    ]

    results = engine.search_apis(pattern, capabilities, max_results=5)

    print(f"\nFound {len(results)} APIs:\n")
    for i, api in enumerate(results, 1):
        print(f"{i}. {api.name}")
        print(f"   Description: {api.description[:80]}...")
        print(f"   Base URL: {api.base_url}")
        print(f"   Auth: {api.auth_type.value} | Pricing: {api.pricing}")
        print(f"   Score: {api.overall_score:.2f} (maturity: {api.maturity_score:.2f}, relevance: {api.relevance_score:.2f})")
        print()

    # Test case 2: Currency exchange API
    print("=" * 80)
    print("Test 2: Search for Currency Exchange APIs")
    print("=" * 80)

    pattern2 = {
        'name': 'Currency Exchange',
        'description': 'Convert between currencies'
    }

    capabilities2 = [
        'Get exchange rates',
        'Convert currency amounts',
        'Historical rates'
    ]

    results2 = engine.search_apis(pattern2, capabilities2, max_results=3)

    print(f"\nFound {len(results2)} APIs:\n")
    for i, api in enumerate(results2, 1):
        print(f"{i}. {api.name}")
        print(f"   Overall Score: {api.overall_score:.2f}")
        print(f"   Has OpenAPI Spec: {'Yes' if api.openapi_spec_url else 'No'}")
        print()

    print("=" * 80)
