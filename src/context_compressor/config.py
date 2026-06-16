"""Configuration objects for the compression pipeline.

Everything is a plain :class:`dataclass` so configs are easy to construct,
serialize, and override. ``CompressionConfig`` is the single object you tune to
trade aggressiveness against fidelity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NoiseConfig:
    """Controls :class:`~context_compressor.filters.noise_filter.NoiseFilter`."""

    drop_timestamps: bool = True
    drop_progress_bars: bool = True
    drop_separators: bool = True
    drop_status_messages: bool = True
    drop_log_levels: bool = False  # log levels often carry signal; opt-in
    drop_stack_trace_frames: bool = True
    collapse_blank_lines: bool = True
    #: Extra ``(regex, label)`` pairs contributed by the caller.
    extra_patterns: List = field(default_factory=list)


@dataclass
class RedundancyConfig:
    """Controls deduplication of exact and near-duplicate lines."""

    drop_exact_duplicates: bool = True
    annotate_duplicate_counts: bool = True
    near_duplicate: bool = False
    #: SequenceMatcher ratio above which two lines are "the same".
    similarity_threshold: float = 0.92
    #: Lines shorter than this are never treated as near-duplicates (too noisy).
    min_line_length_for_fuzzy: int = 12


@dataclass
class TrimConfig:
    """Controls detail trimming of long strings, JSON, and tabular dumps."""

    max_string_length: int = 120
    keep_string_prefix: int = 60
    max_json_depth: int = 4
    max_list_items: int = 20
    #: When a block looks like >N repeated tabular rows, keep only the head.
    max_table_rows: int = 12
    strip_log_metadata: bool = True


@dataclass
class CompressionConfig:
    """Top-level configuration for :class:`ContextCompressor`.

    Attributes
    ----------
    target_ratio:
        Optional *desired* size relative to the original (0–1). The pipeline is
        rule-based, so this is advisory: it is reported against, and used to
        decide whether the optional extractive summarizer should kick in.
    model:
        Model name used by the token counter.
    """

    model: str = "gpt-4"
    target_ratio: Optional[float] = None

    enable_noise_filter: bool = True
    enable_redundancy_filter: bool = True
    enable_detail_trim: bool = True
    enable_pattern_remover: bool = True

    noise: NoiseConfig = field(default_factory=NoiseConfig)
    redundancy: RedundancyConfig = field(default_factory=RedundancyConfig)
    trim: TrimConfig = field(default_factory=TrimConfig)

    @classmethod
    def aggressive(cls) -> "CompressionConfig":
        """A preset that favours smaller output over fidelity."""
        cfg = cls(target_ratio=0.3)
        cfg.noise.drop_log_levels = True
        cfg.redundancy.near_duplicate = True
        cfg.trim.max_string_length = 80
        cfg.trim.keep_string_prefix = 40
        cfg.trim.max_list_items = 10
        cfg.trim.max_table_rows = 6
        return cfg

    @classmethod
    def conservative(cls) -> "CompressionConfig":
        """A preset that favours fidelity; only safe, lossless-ish removals."""
        cfg = cls(target_ratio=0.7)
        cfg.redundancy.near_duplicate = False
        cfg.trim.max_string_length = 240
        cfg.trim.keep_string_prefix = 160
        cfg.trim.max_list_items = 40
        cfg.trim.max_table_rows = 25
        return cfg
