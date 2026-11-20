# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-20

### Added
- Standard `pyproject.toml` with PEP 621 packaging metadata.
- Centralized `Settings` configuration dataclass in `src/config.py`.
- Architecture Decisions Record (`DECISIONS.md`).
- `FROST_WARNING` alert rule for near-freezing minimum temperatures ($\le 2^\circ\text{C}$).
- Multi-city forecast plot generation for all monitored fleet locations (not just the first location).
- GitHub Actions CI workflow (`.github/workflows/ci.yml`).

### Changed
- Refactored `main.py` with structured logging.
- Upgraded Streamlit dashboard with risk badges and multi-city selector.
