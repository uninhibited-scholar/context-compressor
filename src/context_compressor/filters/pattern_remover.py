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
from difflib import SequenceMatcher
from typing import Dict, List, Tuple

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？])\s+")


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


class PatternRemover:
    """Remove repeated boilerplate phrasing across a document."""

    def __init__(self, similarity_threshold: float = 0.9,
                 min_phrase_length: int = 20) -> None:
        self.similarity_threshold = similarity_threshold
        self.min_phrase_length = min_phrase_length

    def filter(self, text: str) -> Tuple[str, Dict[str, int]]:
        seen: List[str] = []
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
                if self._is_repeat(norm, seen):
                    removed += 1
                    continue
                seen.append(norm)
                kept_sentences.append(sentence)
            if kept_sentences:
                out_paragraphs.append(" ".join(kept_sentences))
        return "\n".join(out_paragraphs), {"phrases_removed": removed}

    def _is_repeat(self, norm: str, seen: List[str]) -> bool:
        for prev in seen:
            if abs(len(prev) - len(norm)) / max(len(prev), len(norm)) > (
                1 - self.similarity_threshold
            ):
                continue
            if SequenceMatcher(None, prev, norm).ratio() >= self.similarity_threshold:
                return True
        return False
