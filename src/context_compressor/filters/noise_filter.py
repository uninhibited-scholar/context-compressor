"""Remove low-signal lines: timestamps, progress bars, status chatter, etc.

Noise removal is line-oriented and conservative by default — it only drops
lines that match a known, high-precision pattern, so it is very unlikely to
delete real data.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from ..config import NoiseConfig

# Each entry: (compiled regex, label, config-attribute-that-enables-it)
_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
    # ISO-ish leading timestamp on an otherwise structural line.
    (re.compile(r"^\s*\[?\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}[.,\d]*Z?\]?\s*$"),
     "timestamp", "drop_timestamps"),
    # Progress bars: blocky glyphs and/or a trailing percentage.
    (re.compile(r"^[\s░▒▓█=>\-#.\[\]]*\d{1,3}\s*%\s*$"),
     "progress_bar", "drop_progress_bars"),
    # Pure separators / rules.
    (re.compile(r"^[\s\-=_|*~#.<>+]{3,}$"), "separator", "drop_separators"),
    # Transient status chatter.
    (re.compile(r"^\s*(connecting|connected to|reconnecting|disconnected|"
                r"waiting|loading|initializing|please wait|establishing)\b.*$",
                re.IGNORECASE), "status_msg", "drop_status_messages"),
    # SQL execution statistics with no data payload.
    (re.compile(r"^\s*(rows?\s+(affected|returned)|query\s+(ok|executed)|"
                r"\d+\s+rows?\s+in\s+set)\b.*$", re.IGNORECASE),
     "sql_stats", "drop_status_messages"),
    # Bare log-level lines.
    (re.compile(r"^\s*\[?(debug|trace|info|notice)\]?\s*[:\-]?\s*$",
                re.IGNORECASE), "log_level", "drop_log_levels"),
    # Indented stack-trace frames ("    at com.foo.Bar(...)").
    (re.compile(r"^\s{2,}at\s+\S+", re.IGNORECASE), "stack_frame",
     "drop_stack_trace_frames"),
]


class NoiseFilter:
    """Drop lines that match high-precision noise patterns."""

    def __init__(self, config: NoiseConfig | None = None) -> None:
        self.config = config or NoiseConfig()
        self._patterns = [
            (rx, label) for rx, label, attr in _PATTERNS
            if getattr(self.config, attr, False)
        ]
        # User-supplied (pattern, label) pairs.
        for pattern, label in self.config.extra_patterns:
            self._patterns.append(
                (re.compile(pattern) if isinstance(pattern, str) else pattern,
                 label)
            )

    def filter(self, text: str) -> Tuple[str, Dict[str, int]]:
        """Return ``(cleaned_text, stats)`` where stats counts removals."""
        stats: Dict[str, int] = {}
        out: List[str] = []
        blank_run = 0

        for line in text.split("\n"):
            if not line.strip():
                blank_run += 1
                if self.config.collapse_blank_lines and blank_run > 1:
                    stats["blank_line"] = stats.get("blank_line", 0) + 1
                    continue
                out.append(line)
                continue
            blank_run = 0

            matched = False
            for rx, label in self._patterns:
                if rx.search(line):
                    stats[label] = stats.get(label, 0) + 1
                    matched = True
                    break
            if not matched:
                out.append(line)

        return "\n".join(out), stats
