# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/).

## [0.2.0] - 2026-06-16

### Added
- LangChain / LlamaIndex adapters (`integrations.py`): `CompressorDocumentTransformer`
  and `compress_nodes`, dependency-free via duck typing.
- `ContextCompressor.compress_json()` convenience path for JSON blobs.
- Reproducible benchmark harness (`benchmarks/benchmark.py`) emitting a results
  table and a hand-rendered SVG chart; `BENCHMARKS.md`.

### Changed
- `PatternRemover` is now near-linear: an unbounded exact-match set plus a
  windowed, word-overlap-gated fuzzy comparison. Much faster on large inputs and
  **safer** — it no longer deletes distinct data lines that merely share
  structure (e.g. different scan findings).

### Fixed
- Over-aggressive phrase removal that could drop distinct records on large,
  structurally-similar inputs.

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
