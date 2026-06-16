"""Context Compressor — shrink LLM context windows without losing signal.

Quick start
-----------
>>> from context_compressor import ContextCompressor
>>> compressor = ContextCompressor()
>>> result = compressor.compress(noisy_log_text)
>>> print(result.stats.summary())
>>> print(result.compressed)
"""

from .config import (
    CompressionConfig,
    NoiseConfig,
    RedundancyConfig,
    TrimConfig,
)
from .core.compressor import ContextCompressor
from .core.metrics import CompressionResult, CompressionStats, StageReport
from .filters.detail_trim import DetailTrimmer
from .filters.noise_filter import NoiseFilter
from .filters.pattern_remover import PatternRemover
from .filters.redundancy_filter import RedundancyFilter
from .summarizers.extractive import ExtractiveSummarizer
from .summarizers.security_summarizer import SecuritySummarizer, Severity
from .utils.token_counter import TokenCounter

__version__ = "0.2.0"

__all__ = [
    "ContextCompressor",
    "CompressionConfig",
    "NoiseConfig",
    "RedundancyConfig",
    "TrimConfig",
    "CompressionResult",
    "CompressionStats",
    "StageReport",
    "NoiseFilter",
    "RedundancyFilter",
    "DetailTrimmer",
    "PatternRemover",
    "ExtractiveSummarizer",
    "SecuritySummarizer",
    "Severity",
    "TokenCounter",
    "__version__",
]
