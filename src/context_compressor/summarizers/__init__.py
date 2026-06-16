"""Optional summarizers: generic extractive and security-domain specific."""

from .extractive import ExtractiveSummarizer
from .security_summarizer import SecuritySummarizer, Severity

__all__ = ["ExtractiveSummarizer", "SecuritySummarizer", "Severity"]
