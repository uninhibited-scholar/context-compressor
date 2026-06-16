# Context Compressor

**Shrink LLM context windows by 50–80% — removing noise, redundancy, and long-tail detail without losing the signal.**

[![CI](https://github.com/uninhibite-scholar/context-compressor/actions/workflows/ci.yml/badge.svg)](https://github.com/uninhibite-scholar/context-compressor/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Zero dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)](pyproject.toml)

Long agent loops, verbose tool output, and 10,000-line security scans blow past
even a 200K context window — and every redundant token you send costs latency
and money. **Context Compressor** is a small, fast, rule-based pipeline that
strips the fat out of any text *before* it reaches the model.

```python
from context_compressor import ContextCompressor

compressor = ContextCompressor()
result = compressor.compress(noisy_log_text)

print(result.stats.summary())   # 136 -> 65 tokens (52.2% smaller, backend=tiktoken)
print(result.compressed)        # the cleaned text, ready to send to your LLM
```

---

## Why

| Problem | What happens | What this does |
|---|---|---|
| **Context overflow** | Multi-turn agents accumulate history until the window overflows and the run breaks. | Collapse repeated turns and boilerplate phrasing. |
| **Verbose tool output** | A vuln scan or `SELECT *` dumps thousands of near-identical lines, 90% noise. | Drop noise, dedupe rows, trim long-tail detail. |
| **Token cost** | Every wasted token is latency + dollars on every call. | Typical 50–80% token reduction, measured with `tiktoken`. |

It works on **anything text**: chat transcripts, application logs, JSON blobs,
SQL result dumps, and security scanner output.

## Highlights

- **Zero required dependencies.** Pure Python standard library. `tiktoken` is
  optional — without it a built-in heuristic counter is used automatically.
- **Lossless-leaning by default.** Removals are high-precision; counts are
  preserved (`port 22 open  [x3]`) rather than silently dropped.
- **Composable pipeline.** Toggle each stage, tune thresholds, or add your own
  noise patterns via plain dataclass config.
- **Measured, not guessed.** Every run returns before/after token counts and a
  per-stage breakdown.
- **Security-aware.** A dedicated summarizer turns raw scanner output into a
  severity-ranked brief.
- **CLI included.** `cat scan.log | context-compress --stats`.

## Install

```bash
pip install context-compressor                 # zero dependencies
pip install "context-compressor[tiktoken]"     # exact OpenAI/Anthropic-style token counts
```

Or from source:

```bash
git clone https://github.com/uninhibite-scholar/context-compressor
cd context-compressor
pip install -e ".[dev]"
pytest
```

## How it works

The pipeline runs cheap, high-precision stages first, then optionally falls back
to extractive summarization only if a `target_ratio` is requested and the rules
didn't get there:

```
raw text
   │
   ▼  1. NoiseFilter        drop timestamps, progress bars, status chatter, separators
   ▼  2. DetailTrimmer      shorten long strings, cap JSON depth, collapse table runs, strip log metadata
   ▼  3. PatternRemover     collapse repeated agent phrasing ("as I mentioned…")
   ▼  4. RedundancyFilter   dedupe identical/near-identical lines, keep counts
   ▼  5. ExtractiveSummarizer   (optional) TextRank-style, only if still over target
   │
   ▼
compressed text  +  full token/stage metrics
```

## Usage

### Presets

```python
from context_compressor import ContextCompressor, CompressionConfig

ContextCompressor(CompressionConfig.conservative())  # safe, lossless-ish
ContextCompressor()                                  # balanced default
ContextCompressor(CompressionConfig.aggressive())    # smallest output
```

### Hit a target size

```python
cfg = CompressionConfig(target_ratio=0.3)   # aim for 30% of the original
result = ContextCompressor(cfg).compress(long_transcript)
```

### Tune any stage

```python
from context_compressor import CompressionConfig, NoiseConfig

cfg = CompressionConfig()
cfg.noise.drop_log_levels = True
cfg.redundancy.near_duplicate = True
cfg.trim.max_list_items = 10
cfg.noise.extra_patterns.append((r"^TRACE:.*$", "trace_line"))  # your own rule
```

### Security scan brief

```python
brief = ContextCompressor().compress_security_scan(nessus_output, examples_per_type=3)
print(brief)
```

```
【Security Scan Summary】

Detected 11 findings across 6 categories.

🔴 SQL Injection [CRITICAL]: 2  (CVE-2024-2117)
    1. https://shop.local/search?q=test
    2. https://shop.local/item?id=42
🟠 Cross-Site Scripting (XSS) [HIGH]: 2
    ...
🟢 Open Port / Service [LOW]: 3
    1. 10.0.0.5
    … and 2 more
```

### Command line

```bash
context-compress scan.log --stats
cat transcript.txt | context-compress --preset aggressive
context-compress nessus.txt --security
context-compress big.log --target 0.3 > small.log
```

Compressed text goes to **stdout**; metrics go to **stderr**, so pipes stay clean.

## Reading the metrics

```python
result = compressor.compress(text)
s = result.stats

s.original_tokens      # 136
s.compressed_tokens    # 65
s.reduction_pct        # 52.2
s.token_backend        # "tiktoken" or "heuristic"
for stage in s.stages:
    print(stage.name, stage.chars_removed, stage.details)
```

## Integrating with an agent loop

```python
from context_compressor import ContextCompressor, CompressionConfig

compressor = ContextCompressor(CompressionConfig(target_ratio=0.4))

def before_model_call(history: str) -> str:
    # Compress accumulated context before each turn to stay under the window.
    return compressor.compress(history).compressed
```

## API at a glance

| Object | Purpose |
|---|---|
| `ContextCompressor` | The pipeline. `.compress(text) -> CompressionResult`. |
| `CompressionConfig` | All knobs; `.aggressive()` / `.conservative()` presets. |
| `CompressionResult` | `.compressed` text + `.stats`. |
| `NoiseFilter`, `RedundancyFilter`, `DetailTrimmer`, `PatternRemover` | Stages, usable standalone. |
| `ExtractiveSummarizer` | Dependency-free TextRank-style summarizer. |
| `SecuritySummarizer` | Scanner output → severity-ranked brief. |
| `TokenCounter` | tiktoken-backed counter with heuristic fallback. |

## Development

```bash
pip install -e ".[dev]"
pytest --cov=context_compressor      # 24 tests, ~94% coverage
```

## 中文简介

**Context Compressor** 是一个零依赖的 Python 库，用于在把文本送入大模型之前
压缩上下文：去除噪音（时间戳、进度条、状态消息）、合并重复行、裁剪长字符串/
深层 JSON、折叠 Agent 重复话术，并可选地做抽取式摘要。典型可减少 50–80% 的
Token，配合 `tiktoken` 可获得与 OpenAI/Anthropic 对齐的精确计数。内置面向网络
安全扫描结果的专属摘要器，可将上万行扫描日志归纳为按风险等级排序的简报。

## License

[MIT](LICENSE)
