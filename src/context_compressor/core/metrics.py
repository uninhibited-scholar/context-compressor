"""Result and metric types returned by the compressor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class StageReport:
    """What a single pipeline stage did."""

    name: str
    chars_before: int
    chars_after: int
    details: Dict[str, int] = field(default_factory=dict)

    @property
    def chars_removed(self) -> int:
        return self.chars_before - self.chars_after


@dataclass
class CompressionStats:
    """Aggregate before/after numbers for a compression run."""

    original_chars: int
    compressed_chars: int
    original_tokens: int
    compressed_tokens: int
    token_backend: str
    stages: List[StageReport] = field(default_factory=list)

    @property
    def char_ratio(self) -> float:
        """Compressed size as a fraction of the original (chars)."""
        if self.original_chars == 0:
            return 1.0
        return self.compressed_chars / self.original_chars

    @property
    def token_ratio(self) -> float:
        """Compressed size as a fraction of the original (tokens)."""
        if self.original_tokens == 0:
            return 1.0
        return self.compressed_tokens / self.original_tokens

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.compressed_tokens

    @property
    def reduction_pct(self) -> float:
        """Percentage of tokens removed (the headline number)."""
        return (1.0 - self.token_ratio) * 100.0

    def summary(self) -> str:
        return (
            f"{self.original_tokens} -> {self.compressed_tokens} tokens "
            f"({self.reduction_pct:.1f}% smaller, backend={self.token_backend})"
        )


@dataclass
class CompressionResult:
    """The output of :meth:`ContextCompressor.compress`."""

    compressed: str
    stats: CompressionStats

    def __str__(self) -> str:  # convenient: print(result)
        return self.compressed
