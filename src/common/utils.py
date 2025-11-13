"""
Common utility functions for self-evolving agents.

This module provides shared utilities used across both Level 1 and Level 2.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from functools import wraps


def load_json(filepath: Path) -> Dict[str, Any]:
    """
    Load JSON data from file.

    Args:
        filepath: Path to JSON file

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], filepath: Path, indent: int = 2) -> None:
    """
    Save data to JSON file.

    Args:
        data: Data to save
        filepath: Path to save to
        indent: JSON indentation level
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=indent)


def load_jsonl(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load JSONL (JSON Lines) data from file.

    Args:
        filepath: Path to JSONL file

    Returns:
        List of parsed JSON objects
    """
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def save_jsonl(data: List[Dict[str, Any]], filepath: Path) -> None:
    """
    Save data to JSONL (JSON Lines) file.

    Args:
        data: List of data objects to save
        filepath: Path to save to
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')


def timer(func):
    """
    Decorator to time function execution.

    Usage:
        @timer
        def my_function():
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_ms = int((end_time - start_time) * 1000)
        print(f"⏱️  {func.__name__} took {elapsed_ms}ms")
        return result
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Decorator to retry function on failure.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Usage:
        @retry(max_attempts=3, delay=2.0)
        def my_function():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        print(f"⚠️  Attempt {attempt + 1}/{max_attempts} failed: {e}")
                        print(f"   Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        print(f"❌ All {max_attempts} attempts failed")

            raise last_exception

        return wrapper
    return decorator


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_code_blocks(text: str, language: Optional[str] = None) -> List[str]:
    """
    Extract code blocks from markdown text.

    Args:
        text: Markdown text
        language: Optional language filter (e.g., "python")

    Returns:
        List of code block contents
    """
    import re

    if language:
        pattern = f"```{language}\\n(.*?)```"
    else:
        pattern = r"```(?:\w+)?\n(.*?)```"

    matches = re.findall(pattern, text, re.DOTALL)
    return [match.strip() for match in matches]


def format_metadata(metadata: Dict[str, Any]) -> str:
    """
    Format metadata dictionary for display.

    Args:
        metadata: Metadata dictionary

    Returns:
        Formatted string
    """
    lines = []
    for key, value in metadata.items():
        key_formatted = key.replace('_', ' ').title()
        if isinstance(value, list):
            value_formatted = ', '.join(str(v) for v in value)
        else:
            value_formatted = str(value)
        lines.append(f"{key_formatted}: {value_formatted}")
    return '\n'.join(lines)


def safe_filename(text: str, max_length: int = 50) -> str:
    """
    Convert text to safe filename.

    Args:
        text: Text to convert
        max_length: Maximum filename length

    Returns:
        Safe filename string
    """
    import re

    # Remove or replace unsafe characters
    safe = re.sub(r'[^\w\s-]', '', text)
    safe = re.sub(r'[-\s]+', '_', safe)
    safe = safe.strip('_')

    # Truncate if too long
    if len(safe) > max_length:
        safe = safe[:max_length]

    return safe.lower()


class ProgressTracker:
    """Simple progress tracker for long-running operations."""

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()

    def update(self, n: int = 1) -> None:
        """Update progress by n steps."""
        self.current += n
        self._print_progress()

    def _print_progress(self) -> None:
        """Print current progress."""
        percentage = (self.current / self.total) * 100
        elapsed = time.time() - self.start_time
        rate = self.current / elapsed if elapsed > 0 else 0

        print(f"\r{self.description}: {self.current}/{self.total} "
              f"({percentage:.1f}%) - {rate:.1f} items/s", end='')

        if self.current >= self.total:
            print()  # New line when complete


if __name__ == "__main__":
    # Test utilities
    print("Testing common utilities...")

    # Test timer
    @timer
    def slow_function():
        time.sleep(0.1)

    slow_function()

    # Test truncate
    long_text = "This is a very long string that should be truncated"
    print(f"Truncated: {truncate_string(long_text, 20)}")

    # Test safe filename
    unsafe = "My File: Test (2024)!"
    print(f"Safe filename: {safe_filename(unsafe)}")

    print("\n✅ Utilities working")
