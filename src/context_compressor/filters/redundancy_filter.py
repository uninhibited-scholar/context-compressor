"""Collapse exact and near-duplicate lines, preserving counts.

Long agent transcripts and scan logs repeat the same line many times. Rather
than silently deleting repeats (which loses the fact that something happened N
times), this filter keeps the first occurrence and annotates it with a count.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Dict, List, Tuple

from ..config import RedundancyConfig


class RedundancyFilter:
    """Deduplicate repeated lines."""

    def __init__(self, config: RedundancyConfig | None = None) -> None:
        self.config = config or RedundancyConfig()

    def filter(self, text: str) -> Tuple[str, Dict[str, int]]:
        stats: Dict[str, int] = {"exact_removed": 0, "near_removed": 0}
        text, exact = self._exact(text)
        stats["exact_removed"] = exact
        if self.config.near_duplicate:
            text, near = self._near(text)
            stats["near_removed"] = near
        return text, stats

    # -- exact duplicates -------------------------------------------------
    def _exact(self, text: str) -> Tuple[str, int]:
        if not self.config.drop_exact_duplicates:
            return text, 0

        counts: Dict[str, int] = {}
        order: List[str] = []
        # Preserve leading whitespace of the first occurrence.
        first_seen: Dict[str, str] = {}

        for line in text.split("\n"):
            key = line.strip()
            if key == "":
                order.append(line)  # blanks handled by NoiseFilter
                first_seen.setdefault(f"__blank__{len(order)}", line)
                continue
            if key in counts:
                counts[key] += 1
            else:
                counts[key] = 1
                first_seen[key] = line
                order.append(key)

        out: List[str] = []
        removed = 0
        for token in order:
            if token.startswith("__blank__") or token not in counts:
                # blank placeholder: re-emit empty line
                out.append("")
                continue
            line = first_seen[token]
            n = counts[token]
            if n > 1:
                removed += n - 1
                if self.config.annotate_duplicate_counts:
                    out.append(f"{line}  [x{n}]")
                else:
                    out.append(line)
            else:
                out.append(line)
        return "\n".join(out), removed

    # -- near duplicates --------------------------------------------------
    def _near(self, text: str) -> Tuple[str, int]:
        kept: List[str] = []
        removed = 0
        threshold = self.config.similarity_threshold
        min_len = self.config.min_line_length_for_fuzzy

        for line in text.split("\n"):
            stripped = line.strip()
            if len(stripped) < min_len:
                kept.append(line)
                continue
            is_dup = False
            for prev in kept:
                p = prev.strip()
                if len(p) < min_len:
                    continue
                # Quick length gate before the O(n*m) matcher.
                if abs(len(p) - len(stripped)) / max(len(p), len(stripped)) > (
                    1 - threshold
                ):
                    continue
                if SequenceMatcher(None, p, stripped).ratio() >= threshold:
                    is_dup = True
                    removed += 1
                    break
            if not is_dup:
                kept.append(line)
        return "\n".join(kept), removed
