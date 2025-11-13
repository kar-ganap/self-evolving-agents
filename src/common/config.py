"""
Configuration management for self-evolving agents.

This module provides centralized configuration loading from environment
variables and config files.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration for the self-evolving agent system."""

    # Project Paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    CONVERSATIONS_DIR = DATA_DIR / "conversations"
    TRAINING_DIR = DATA_DIR / "training"
    TOOLS_DIR = PROJECT_ROOT / "src" / "level2" / "tools"

    # API Keys
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")

    # Model Configuration
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "claude-sonnet-4-5-20250929")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))

    # Level 1 Configuration
    PATTERNS_FILE: Path = DATA_DIR / os.getenv("PATTERNS_FILE", "patterns.json")
    CONVERSATIONS_FILE: Path = DATA_DIR / os.getenv("CONVERSATIONS_FILE", "conversations.json")

    # Level 2 Configuration
    GENERATED_TOOLS_PREFIX: str = os.getenv("GENERATED_TOOLS_PREFIX", "generated_")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[Path] = None
    log_file_env = os.getenv("LOG_FILE")
    if log_file_env:
        LOG_FILE = PROJECT_ROOT / log_file_env

    # Demo Configuration
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    DEMO_CACHE_ENABLED: bool = os.getenv("DEMO_CACHE_ENABLED", "true").lower() == "true"

    @classmethod
    def validate(cls) -> bool:
        """
        Validate that required configuration is present.

        Returns:
            True if configuration is valid, False otherwise
        """
        errors = []

        # Check required API keys
        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is not set")

        # Check required directories exist
        if not cls.DATA_DIR.exists():
            errors.append(f"Data directory does not exist: {cls.DATA_DIR}")

        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        return True

    @classmethod
    def ensure_directories(cls) -> None:
        """Create required directories if they don't exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
        cls.TRAINING_DIR.mkdir(parents=True, exist_ok=True)
        cls.TOOLS_DIR.mkdir(parents=True, exist_ok=True)

        if cls.LOG_FILE:
            cls.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def print_config(cls) -> None:
        """Print current configuration (masking sensitive values)."""
        print("=" * 80)
        print("CONFIGURATION")
        print("=" * 80)
        print(f"Project Root: {cls.PROJECT_ROOT}")
        print(f"Data Directory: {cls.DATA_DIR}")
        print(f"Conversations Directory: {cls.CONVERSATIONS_DIR}")
        print(f"Tools Directory: {cls.TOOLS_DIR}")
        print()
        print(f"Anthropic API Key: {'*' * 20 if cls.ANTHROPIC_API_KEY else 'NOT SET'}")
        print(f"Default Model: {cls.DEFAULT_MODEL}")
        print(f"Max Tokens: {cls.MAX_TOKENS}")
        print(f"Temperature: {cls.TEMPERATURE}")
        print()
        print(f"Patterns File: {cls.PATTERNS_FILE}")
        print(f"Conversations File: {cls.CONVERSATIONS_FILE}")
        print()
        print(f"Log Level: {cls.LOG_LEVEL}")
        print("=" * 80)


# Initialize directories on import
Config.ensure_directories()


if __name__ == "__main__":
    # Validate and print configuration
    Config.print_config()

    if Config.validate():
        print("\n✅ Configuration is valid")
    else:
        print("\n❌ Configuration has errors")
