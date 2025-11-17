"""
External API Integration Engine - WALK Phase Component

Combines API discovery, authentication handling, rate limiting, and wrapper generation
to autonomously integrate third-party APIs.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

from src.level2.walk.api_discovery_engine import APIDiscoveryEngine, APICandidate, AuthType
from src.level2.crawl.tool_acquisition_engine import ToolAcquisitionEngine, GeneratedTool
from src.level2.crawl.build_vs_buy_analyzer import BuyOption, AcquisitionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExternalAPIIntegrationResult:
    """
    Result of external API integration workflow.

    Attributes:
        success: Whether integration succeeded
        api: Selected API (if successful)
        tool: Generated wrapper tool (if successful)
        error: Error message if failed
    """
    success: bool
    api: Optional[APICandidate] = None
    tool: Optional[GeneratedTool] = None
    error: Optional[str] = None


class ExternalAPIEngine:
    """
    Orchestrates the complete external API integration workflow.

    Flow:
    1. Search for matching APIs (APIs.guru, public-apis.org)
    2. Rank and select best option
    3. Generate wrapper code with auth, rate limiting, retry logic
    4. Return ready-to-use tool

    This extends WALK phase from libraries to APIs.
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize external API engine.

        Args:
            gemini_api_key: Google API key for Gemini 2.5 Pro
        """
        self.search_engine = APIDiscoveryEngine()
        self.tool_engine = ToolAcquisitionEngine(gemini_api_key=gemini_api_key)

    def integrate_api(
        self,
        pattern: Dict,
        missing_capabilities: List[str]
    ) -> ExternalAPIIntegrationResult:
        """
        Search for, select, and wrap an external API.

        Args:
            pattern: Pattern dictionary with 'name' and 'description'
            missing_capabilities: List of missing capability descriptions

        Returns:
            ExternalAPIIntegrationResult with integration outcome
        """
        pattern_name = pattern['name']

        logger.info(f"Starting external API integration for: {pattern_name}")

        try:
            # Step 1: Search APIs
            logger.info("  [1/3] Searching for APIs...")
            candidates = self.search_engine.search_apis(
                pattern=pattern,
                missing_capabilities=missing_capabilities,
                max_results=5
            )

            if not candidates:
                return ExternalAPIIntegrationResult(
                    success=False,
                    error="No suitable APIs found"
                )

            # Select best candidate (highest overall_score)
            best_api = candidates[0]

            logger.info(f"  ✓ Selected: {best_api.name}")
            logger.info(f"    Score: {best_api.overall_score:.2f}")
            logger.info(f"    Auth: {best_api.auth_type.value}")
            logger.info(f"    Pricing: {best_api.pricing}")

            # Step 2: Create BuyOption for wrapper generation
            buy_option = self._create_buy_option(best_api)

            # Step 3: Generate enhanced wrapper with auth, rate limiting, retry logic
            logger.info("  [2/3] Generating API wrapper with Gemini 2.5 Pro...")
            tool = self._generate_api_wrapper(pattern, best_api, buy_option)

            logger.info(f"  ✓ Wrapper generated: {tool.name}")
            logger.info(f"    Code length: {len(tool.code)} characters")

            # Step 4: Save wrapper to file
            logger.info("  [3/3] Saving wrapper...")
            saved_path = self.tool_engine.save_tool(tool)
            logger.info(f"  ✓ Saved to: {saved_path}")

            return ExternalAPIIntegrationResult(
                success=True,
                api=best_api,
                tool=tool
            )

        except Exception as e:
            logger.error(f"Integration failed: {e}")
            return ExternalAPIIntegrationResult(
                success=False,
                error=str(e)
            )

    def search_and_rank(
        self,
        pattern: Dict,
        missing_capabilities: List[str],
        max_results: int = 10
    ) -> List[APICandidate]:
        """
        Search and rank APIs without generating wrapper.

        Useful for presenting options to user before committing.

        Args:
            pattern: Pattern dictionary
            missing_capabilities: List of capabilities needed
            max_results: Maximum number of results

        Returns:
            List of ranked APICandidate objects
        """
        return self.search_engine.search_apis(
            pattern=pattern,
            missing_capabilities=missing_capabilities,
            max_results=max_results
        )

    def _create_buy_option(self, api: APICandidate) -> BuyOption:
        """
        Create BuyOption from APICandidate.

        Args:
            api: API candidate

        Returns:
            BuyOption for tool generation
        """
        # Determine cost (convert pricing to monthly cost)
        cost_per_month = 0.0
        if api.pricing == "paid":
            cost_per_month = 30.0  # Assume $30/month default
        elif api.pricing == "freemium":
            cost_per_month = 0.0  # Free tier available

        return BuyOption(
            source=api.name,
            acquisition_type=AcquisitionType.API,
            cost_per_month=cost_per_month,
            setup_time=600,  # 10 minutes estimated for API integration
            maturity_score=api.maturity_score,
            details={
                'base_url': api.base_url,
                'auth_type': api.auth_type.value,
                'pricing': api.pricing,
                'rate_limit': api.rate_limit,
                'documentation_url': api.documentation_url,
                'openapi_spec_url': api.openapi_spec_url,
                'category': api.category
            }
        )

    def _generate_api_wrapper(
        self,
        pattern: Dict,
        api: APICandidate,
        buy_option: BuyOption
    ) -> GeneratedTool:
        """
        Generate enhanced API wrapper with authentication, rate limiting, and retry logic.

        Args:
            pattern: Pattern dictionary
            api: API candidate
            buy_option: BuyOption for metadata

        Returns:
            GeneratedTool with wrapper code
        """
        class_name = self.tool_engine._generate_class_name(pattern['name'])

        # Build enhanced prompt for API wrapper
        wrapper_prompt = self._build_api_wrapper_prompt(
            class_name=class_name,
            pattern=pattern,
            api=api
        )

        # Generate using Gemini
        from google.genai import types
        response = self.tool_engine.client.models.generate_content(
            model=self.tool_engine.model,
            contents=wrapper_prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=10000,  # API wrappers can be longer
            )
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
            acquisition_type='api',
            metadata={
                'api_name': api.name,
                'base_url': api.base_url,
                'auth_type': api.auth_type.value,
                'pricing': api.pricing,
                'maturity_score': api.maturity_score
            }
        )

    def _build_api_wrapper_prompt(
        self,
        class_name: str,
        pattern: Dict,
        api: APICandidate
    ) -> str:
        """
        Build comprehensive prompt for API wrapper generation.

        Args:
            class_name: Generated class name
            pattern: Pattern dictionary
            api: API candidate

        Returns:
            Prompt string for Gemini
        """
        # Determine auth instructions based on type
        auth_instructions = self._get_auth_instructions(api.auth_type)

        prompt = f"""Generate a production-quality Python API wrapper for: {api.name}

# Pattern
**Name:** {pattern['name']}
**Description:** {pattern['description']}

# API Details
**Base URL:** {api.base_url}
**Authentication:** {api.auth_type.value}
**Pricing:** {api.pricing}
{f"**Documentation:** {api.documentation_url}" if api.documentation_url else ""}
{f"**OpenAPI Spec:** {api.openapi_spec_url}" if api.openapi_spec_url else ""}

# Requirements

1. **Class Structure:**
   - Class name: `{class_name}`
   - Import `requests` library for HTTP calls
   - Main method: `analyze(self, code: str, file_path: str = None) -> dict`
   - Return standardized format: {{'score': float, 'checks': dict, 'issues': list, 'suggestions': list}}

2. **Authentication:**
{auth_instructions}

3. **Rate Limiting & Retry Logic:**
   - Implement exponential backoff for retries (3 attempts)
   - Handle 429 (rate limit) and 5xx (server error) responses
   - Add delays between requests to respect rate limits
   - Use try/except for network errors

4. **Error Handling:**
   - Try/except around all API calls
   - Fallback to safe defaults if API fails
   - Log errors but don't crash
   - Return meaningful error messages in result

5. **Response Caching:**
   - Cache successful responses for 5 minutes to reduce API calls
   - Use simple dict-based cache with timestamps

6. **API Call Implementation:**
   - Use requests.get() or requests.post() as appropriate
   - Set timeout (10 seconds)
   - Include proper headers (User-Agent, Accept)
   - Parse JSON responses
   - Convert API response to standardized format

7. **Example Usage:**
   ```python
   tool = {class_name}(api_key="your-api-key-here")  # If auth required
   result = tool.analyze(code_string)
   # Returns: {{'score': 0.75, 'checks': {{...}}, 'issues': [...], 'suggestions': [...]}}
   ```

Generate ONLY the Python code including all necessary imports. No explanation or markdown.
The code should be ready to execute immediately."""

        return prompt

    def _get_auth_instructions(self, auth_type: AuthType) -> str:
        """
        Get authentication instructions for prompt.

        Args:
            auth_type: Authentication type

        Returns:
            Instructions string
        """
        if auth_type == AuthType.NONE:
            return "   - No authentication required"

        elif auth_type == AuthType.API_KEY:
            return """   - Accept `api_key` parameter in __init__()
   - Pass API key in headers: `{'X-API-Key': self.api_key}` or as query param
   - Validate API key is provided before making requests"""

        elif auth_type == AuthType.BEARER:
            return """   - Accept `access_token` parameter in __init__()
   - Include in headers: `{'Authorization': f'Bearer {self.access_token}'}`
   - Validate token is provided before making requests"""

        elif auth_type == AuthType.OAUTH2:
            return """   - Accept `access_token` parameter in __init__()
   - Include in headers: `{'Authorization': f'Bearer {self.access_token}'}`
   - Add comment: "# OAuth2: User must obtain token externally"
   - Validate token is provided before making requests"""

        elif auth_type == AuthType.BASIC:
            return """   - Accept `username` and `password` parameters in __init__()
   - Use requests.auth.HTTPBasicAuth(username, password)
   - Validate credentials are provided before making requests"""

        else:
            return "   - Implement appropriate authentication based on API docs"


# Example usage and testing
if __name__ == "__main__":
    print("External API Integration Engine - Test Mode\n")

    engine = ExternalAPIEngine()

    # Test case 1: Weather API (search only)
    print("=" * 80)
    print("Test 1: Search for Weather APIs")
    print("=" * 80)

    pattern = {
        'name': 'Weather Forecast',
        'description': 'Get weather forecasts and current conditions'
    }

    capabilities = [
        'Get current weather',
        'Get forecast',
        'Search by location'
    ]

    # Search and rank
    print("\nSearching for APIs...")
    candidates = engine.search_and_rank(pattern, capabilities, max_results=3)

    print(f"\nTop {len(candidates)} APIs:\n")
    for i, api in enumerate(candidates, 1):
        print(f"{i}. {api.name}")
        print(f"   Auth: {api.auth_type.value} | Pricing: {api.pricing}")
        print(f"   Score: {api.overall_score:.2f}")
        print()

    # Test case 2: Currency Exchange API (full integration, dry-run)
    print("=" * 80)
    print("Test 2: Currency Exchange API Integration (Dry-Run)")
    print("=" * 80)

    pattern2 = {
        'name': 'Currency Conversion',
        'description': 'Convert between currencies using live exchange rates'
    }

    capabilities2 = [
        'Get exchange rates',
        'Convert amounts',
        'Support multiple currencies'
    ]

    print("\nRunning integration workflow...")
    print("(Wrapper generation will use Gemini 2.5 Pro)")

    print("\n" + "=" * 80)
    print("\nNote: Skipping actual API wrapper generation in test mode")
    print("To test full integration, run with GEMINI_API_KEY set:")
    print("  export GEMINI_API_KEY=your-key-here")
    print("  python -m src.level2.walk.external_api_engine")
    print("=" * 80)
