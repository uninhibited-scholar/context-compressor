"""Collapse repeated *agent* phrasing — the "as I mentioned…" problem.

In multi-turn agent loops the model often re-states the same reasoning
("I have already queried the database", "Let me check the results again").
This filter detects sentences/phrases that recur across the text and keeps only
the first, dropping later near-identical restatements.

It is sentence-oriented (not line-oriented) so it complements
:class:`RedundancyFilter`, which works on whole lines.
"""

from __future__ import annotations

import re
from collections import deque
from difflib import SequenceMatcher
from typing import Dict, List, Tuple

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？])\s+")


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


class PatternRemover:
    """Remove repeated boilerplate phrasing across a document."""

    def __init__(self, similarity_threshold: float = 0.9,
                 min_phrase_length: int = 20, window: int = 64) -> None:
        """
        Parameters
        ----------
        window:
            Size of the rolling window used for the *fuzzy* (near-duplicate)
            comparison. Exact repeats are caught globally and cheaply via a set;
            only fuzzy matching is windowed, which keeps the cost at
            O(n·window) instead of O(n²). Boilerplate phrasing recurs locally,
            so a small window loses almost nothing while staying fast.
        """
        self.similarity_threshold = similarity_threshold
        self.min_phrase_length = min_phrase_length
        self.window = window

    def filter(self, text: str) -> Tuple[str, Dict[str, int]]:
        # Unbounded exact-match set: O(1), catches identical phrasing at any
        # distance and is always safe.
        seen_exact: set = set()
        # Small rolling window for the expensive fuzzy comparison only.
        recent: deque = deque(maxlen=self.window)
        removed = 0
        out_paragraphs: List[str] = []

        for paragraph in text.split("\n"):
            if not paragraph.strip():
                out_paragraphs.append(paragraph)
                continue
            kept_sentences: List[str] = []
            for sentence in _SENTENCE_SPLIT.split(paragraph):
                norm = _normalize(sentence)
                if len(norm) < self.min_phrase_length:
                    kept_sentences.append(sentence)
                    continue
                words = frozenset(norm.split())
                if norm in seen_exact or self._is_repeat(norm, words, recent):
                    removed += 1
                    continue
                seen_exact.add(norm)
                recent.append((norm, words))
                kept_sentences.append(sentence)
            if kept_sentences:
                out_paragraphs.append(" ".join(kept_sentences))
        return "\n".join(out_paragraphs), {"phrases_removed": removed}

    def _is_repeat(self, norm: str, words: frozenset, seen) -> bool:
        threshold = self.similarity_threshold
        n = len(norm)
        # A char-level ratio >= threshold implies a high word Jaccard, so gate
        # on a looser word-overlap bound first; SequenceMatcher (the expensive
        # part) then only runs on plausible candidates.
        word_gate = max(0.0, 2 * threshold - 1)  # e.g. 0.9 -> 0.8
        for prev, prev_words in seen:
            if abs(len(prev) - n) / max(len(prev), n) > (1 - threshold):
                continue
            union = len(words | prev_words)
            if union and len(words & prev_words) / union < word_gate:
                continue
            if SequenceMatcher(None, prev, norm).ratio() >= threshold:
                return True
        return False
