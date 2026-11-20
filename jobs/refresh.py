"""Periodic weather refresh job (run via cron or APScheduler)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from main import main

if __name__ == "__main__":
    main()
