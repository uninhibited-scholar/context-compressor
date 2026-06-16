# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - 2026-06-16

### Added
- Rule-based compression pipeline: `NoiseFilter`, `DetailTrimmer`,
  `PatternRemover`, `RedundancyFilter`.
- Optional TextRank-style `ExtractiveSummarizer` used as a `target_ratio` fallback.
- `SecuritySummarizer` for severity-ranked briefs from scanner output.
- `TokenCounter` with optional `tiktoken` backend and heuristic fallback.
- `ContextCompressor` orchestrator with per-stage metrics.
- `context-compress` command-line interface.
- `aggressive` / `conservative` config presets.
- Test suite (~94% coverage) and runnable examples.
