"""The unified compression pipeline.

:class:`ContextCompressor` wires the filters together, tracks per-stage
metrics, and reports token savings. The pipeline order matters:

1. **NoiseFilter** — drop low-signal lines first (cheap, lossless-ish).
2. **DetailTrimmer** — shorten long strings / tables / log metadata.
3. **PatternRemover** — collapse repeated agent phrasing.
4. **RedundancyFilter** — deduplicate whole lines, annotate counts.
5. *(optional)* **ExtractiveSummarizer** — only if a ``target_ratio`` is set
   and the rule-based stages did not reach it.
"""

from __future__ import annotations

from typing import Callable, List, Tuple

from ..config import CompressionConfig
from ..filters.detail_trim import DetailTrimmer
from ..filters.noise_filter import NoiseFilter
from ..filters.pattern_remover import PatternRemover
from ..filters.redundancy_filter import RedundancyFilter
from ..summarizers.extractive import ExtractiveSummarizer
from ..summarizers.security_summarizer import SecuritySummarizer
from ..utils.token_counter import TokenCounter
from .metrics import CompressionResult, CompressionStats, StageReport

# A stage takes text and returns (new_text, detail_stats).
Stage = Tuple[str, Callable[[str], Tuple[str, dict]]]


class ContextCompressor:
    """Compress free-form context (logs, transcripts, scan output)."""

    def __init__(self, config: CompressionConfig | None = None) -> None:
        self.config = config or CompressionConfig()
        self.token_counter = TokenCounter(self.config.model)
        self._build_stages()

    def _build_stages(self) -> None:
        cfg = self.config
        self._stages: List[Stage] = []
        if cfg.enable_noise_filter:
            self._stages.append(("noise", NoiseFilter(cfg.noise).filter))
        if cfg.enable_detail_trim:
            self._stages.append(("detail_trim", DetailTrimmer(cfg.trim).trim))
        if cfg.enable_pattern_remover:
            self._stages.append(("pattern", PatternRemover().filter))
        if cfg.enable_redundancy_filter:
            self._stages.append(
                ("redundancy", RedundancyFilter(cfg.redundancy).filter))

    def compress(self, text: str) -> CompressionResult:
        """Run the full pipeline and return text + metrics."""
        original_chars = len(text)
        original_tokens = self.token_counter.count(text)

        reports: List[StageReport] = []
        current = text
        for name, fn in self._stages:
            before = len(current)
            current, details = fn(current)
            reports.append(StageReport(
                name=name, chars_before=before, chars_after=len(current),
                details=details,
            ))

        # Optional extractive summarization if we still overshoot the target.
        if self.config.target_ratio is not None:
            current = self._maybe_summarize(text, current, reports)

        stats = CompressionStats(
            original_chars=original_chars,
            compressed_chars=len(current),
            original_tokens=original_tokens,
            compressed_tokens=self.token_counter.count(current),
            token_backend=self.token_counter.backend,
            stages=reports,
        )
        return CompressionResult(compressed=current, stats=stats)

    def _maybe_summarize(self, original: str, current: str,
                         reports: List[StageReport]) -> str:
        target = self.config.target_ratio
        cur_tokens = self.token_counter.count(current)
        orig_tokens = self.token_counter.count(original) or 1
        if cur_tokens / orig_tokens <= target:
            return current  # already small enough
        before = len(current)
        # Aim the summarizer at the remaining gap.
        inner_ratio = max(0.1, target * orig_tokens / max(cur_tokens, 1))
        summarized = ExtractiveSummarizer().summarize(current, ratio=inner_ratio)
        reports.append(StageReport(
            name="extractive", chars_before=before,
            chars_after=len(summarized), details={"applied": 1},
        ))
        return summarized

    # -- convenience ------------------------------------------------------
    def compress_text(self, text: str) -> str:
        """Return just the compressed string."""
        return self.compress(text).compressed

    def compress_security_scan(self, scan_output: str,
                               examples_per_type: int = 5) -> str:
        """Specialized path: summarize raw scanner output into a brief."""
        return SecuritySummarizer(
            examples_per_type=examples_per_type).summarize(scan_output)
