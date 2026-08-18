"""
Configuration for N100 Financial Intelligence API.
"""

import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "DB" / "nifty100.db"

API_VERSION = "1.0.0"

START_TIME = time.time()