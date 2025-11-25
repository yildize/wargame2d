from __future__ import annotations

from pathlib import Path

# Resolved project root (directory containing this file).
PROJECT_ROOT = Path(__file__).resolve().parent

# Common storage locations.
STORAGE_DIR = PROJECT_ROOT / "storage"
SCENARIO_STORAGE_DIR = STORAGE_DIR / "scenarios"
