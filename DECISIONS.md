# Architecture & Engineering Decisions (ADR)

## ADR 001: Multi-City Fleet Visualizations
- **Status:** Accepted
- **Context:** The previous visualization script plotted only the first location (`locations[0]`), silently dropping other monitored cities.
- **Decision:** Loop over all distinct locations present in the forecast payload and generate individual publication-grade forecast plots.
- **Consequences:** Provides full observational coverage across all monitored geographical locations.

## ADR 002: Structured Weather Rules Dataclasses
- **Status:** Accepted
- **Context:** If statements with hardcoded values in `src/rules.py` precluded dynamic threshold adjustments.
- **Decision:** Introduce a formal `RuleDefinition` dataclass allowing customized hazard boundaries.
- **Consequences:** Cleaner extensibility and transparent auditability.

## ADR 003: Relational Upsert Integrity
- **Status:** Accepted
- **Context:** Successive runs risk duplicate alert accumulation.
- **Decision:** Maintain `weather_daily` composite keys `(location_id, date)` and transactional logging for alerts.
- **Consequences:** Ensures database consistency across repeated execution runs.
