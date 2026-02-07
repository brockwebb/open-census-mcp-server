"""Pytest configuration and fixtures.

Loads environment variables from .env file at test startup.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


def pytest_configure(config):
    """Load .env file before tests run."""
    # Find .env relative to repo root
    repo_root = Path(__file__).parent.parent
    env_file = repo_root / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
