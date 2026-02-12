"""Census MCP Server configuration.

All parameters that affect outputs are externalized here.
Environment variables override defaults. No hardcoded values in server.py.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

# === Census API Configuration ===
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", "")

# === Data Product Defaults ===
# These defaults are used when the caller (LLM) does not specify.
# Update when new ACS vintages are released.
#
# ACS Release Schedule (as of 2025):
#   - ACS 1-year: Released September of the following year (e.g., 2024 data in Sep 2025)
#   - ACS 5-year: Released December of the following year (e.g., 2020-2024 in Dec 2025)
#
# IMPORTANT: When updating DEFAULT_YEAR, also verify the Census API
# endpoint is live at: https://api.census.gov/data/{year}/acs/{product}
DEFAULT_YEAR = int(os.environ.get("CENSUS_DEFAULT_YEAR", "2024"))
DEFAULT_PRODUCT = os.environ.get("CENSUS_DEFAULT_PRODUCT", "acs5")

# Supported products
SUPPORTED_PRODUCTS = {"acs5", "acs1"}

# === Pragmatics Configuration ===
PACKS_DIR = os.environ.get("PACKS_DIR", "packs")

# === Logging ===
LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING")
LOG_FILE = os.environ.get("CENSUS_LOG_FILE", "/tmp/census-mcp.log")

# === Server Metadata ===
SERVER_NAME = "census-mcp"
