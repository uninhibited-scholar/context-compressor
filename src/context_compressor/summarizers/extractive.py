"""A dependency-free extractive summarizer (TextRank-style).

Builds a sentence-similarity graph and ranks sentences by a PageRank-like
score, then returns the top-k in their original order. This is used as an
*optional* final stage when rule-based compression alone does not reach the
requested ``target_ratio``.

No external NLP dependencies — similarity is bag-of-words cosine over simple
tokenization, which is robust and fast for log/chat text.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import List

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？\n])\s+")
_WORD_RE = re.compile(r"\w+", re.UNICODE)

# Minimal stopword set; extractive ranking is not very sensitive to it.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "was",
    "were", "for", "on", "with", "as", "by", "at", "this", "that", "it",
    "be", "has", "have", "had", "i", "you", "we", "they", "he", "she",
}


def _sentences(text: str) -> List[str]:
    raw = [s.strip() for s in _SENTENCE_SPLIT.split(text)]
    return [s for s in raw if s]


def _vector(sentence: str) -> Counter:
    words = [w.lower() for w in _WORD_RE.findall(sentence)
             if w.lower() not in _STOPWORDS]
    return Counter(words)


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[w] * b[w] for w in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


class ExtractiveSummarizer:
    """Rank and select the most central sentences in a document."""

    def __init__(self, damping: float = 0.85, iterations: int = 30) -> None:
        self.damping = damping
        self.iterations = iterations

    def summarize(self, text: str, ratio: float = 0.3,
                  max_sentences: int | None = None) -> str:
        sents = _sentences(text)
        if len(sents) <= 2:
            return text.strip()

        target = max(1, int(round(len(sents) * ratio)))
        if max_sentences is not None:
            target = min(target, max_sentences)

        scores = self._textrank(sents)
        # Pick top-`target` by score, then restore document order.
        ranked = sorted(range(len(sents)), key=lambda i: scores[i], reverse=True)
        chosen = sorted(ranked[:target])
        return "\n".join(sents[i] for i in chosen)

    def _textrank(self, sents: List[str]) -> List[float]:
        n = len(sents)
        vectors = [_vector(s) for s in sents]
        # Weighted adjacency matrix.
        weights = [[0.0] * n for _ in range(n)]
        row_sums = [0.0] * n
        for i in range(n):
            for j in range(i + 1, n):
                sim = _cosine(vectors[i], vectors[j])
                weights[i][j] = weights[j][i] = sim
                row_sums[i] += sim
                row_sums[j] += sim

        scores = [1.0 / n] * n
        for _ in range(self.iterations):
            new = [(1 - self.damping) / n] * n
            for i in range(n):
                acc = 0.0
                for j in range(n):
                    if i == j or row_sums[j] == 0:
                        continue
                    acc += weights[j][i] / row_sums[j] * scores[j]
                new[i] += self.damping * acc
            scores = new
        return scores
