"""Core pipeline: the compressor and its metric types."""

from .compressor import ContextCompressor
from .metrics import CompressionResult, CompressionStats, StageReport

__all__ = [
    "ContextCompressor",
    "CompressionResult",
    "CompressionStats",
    "StageReport",
]
