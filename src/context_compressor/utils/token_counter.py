"""Token counting with an optional ``tiktoken`` backend.

The compressor reasons about budgets in *tokens*, not characters. When
``tiktoken`` is installed we use the real BPE tokenizer (matching OpenAI /
Anthropic-style accounting closely). When it is not, we fall back to a fast
heuristic that is good enough for ratio reporting and target budgeting.

The package has **no required dependencies** — ``tiktoken`` is optional.
"""

from __future__ import annotations

import re
from functools import lru_cache

# A word, a run of digits, or a single non-space symbol. This matches the rough
# granularity of a BPE tokenizer well enough for budgeting when tiktoken is
# unavailable.
_HEURISTIC_TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


@lru_cache(maxsize=8)
def _load_encoding(model: str):
    """Load and cache a tiktoken encoding, or return ``None`` if unavailable."""
    try:
        import tiktoken
    except ImportError:
        return None
    try:
        return tiktoken.encoding_for_model(model)
    except Exception:
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None


class TokenCounter:
    """Count tokens in text.

    Parameters
    ----------
    model:
        Model name passed to ``tiktoken`` (e.g. ``"gpt-4"``). Ignored by the
        heuristic backend.
    """

    def __init__(self, model: str = "gpt-4") -> None:
        self.model = model
        self._encoding = _load_encoding(model)

    @property
    def backend(self) -> str:
        """Return ``"tiktoken"`` or ``"heuristic"`` so callers can report it."""
        return "tiktoken" if self._encoding is not None else "heuristic"

    def count(self, text: str) -> int:
        """Return the number of tokens in ``text``."""
        if not text:
            return 0
        if self._encoding is not None:
            return len(self._encoding.encode(text))
        return self._heuristic_count(text)

    @staticmethod
    def _heuristic_count(text: str) -> int:
        # Roughly one token per word/symbol, with a small uplift for long words
        # which BPE tends to split into multiple pieces.
        pieces = _HEURISTIC_TOKEN_RE.findall(text)
        tokens = 0
        for piece in pieces:
            # Long alphanumeric runs split into ~one token per 4 chars.
            tokens += 1 + (len(piece) - 1) // 4 if len(piece) > 4 else 1
        return tokens
