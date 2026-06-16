"""Trim long-tail detail while keeping the shape of the data intact.

Three independent operations:

* :meth:`trim_long_strings` — shorten very long quoted values in-line.
* :meth:`trim_json` — re-emit JSON with a depth cap and list truncation.
* :meth:`trim_tables` — collapse long runs of similar tabular rows to a head
  plus an ``... (+N more rows)`` marker.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

from ..config import TrimConfig

_LONG_STRING_RE = re.compile(r'("(?:[^"\\]|\\.)*")')
# A row that starts with a table-ish leading column (pipe table, CSV, "- item").
_TABLE_ROW_RE = re.compile(r"^\s*(\||[\w.:/-]+\s*[,|]\s)")


class DetailTrimmer:
    def __init__(self, config: TrimConfig | None = None) -> None:
        self.config = config or TrimConfig()

    def trim(self, text: str) -> Tuple[str, Dict[str, int]]:
        """Apply all trimming operations in sequence."""
        stats: Dict[str, int] = {}
        if self.config.strip_log_metadata:
            text, n = self._strip_log_metadata(text)
            stats["log_meta_stripped"] = n
        text, n = self.trim_tables(text)
        stats["table_rows_trimmed"] = n
        text, n = self.trim_long_strings(text)
        stats["strings_trimmed"] = n
        return text, stats

    # -- long strings -----------------------------------------------------
    def trim_long_strings(self, text: str) -> Tuple[str, int]:
        limit = self.config.max_string_length
        keep = self.config.keep_string_prefix
        count = 0

        def repl(match: re.Match) -> str:
            nonlocal count
            literal = match.group(1)
            inner = literal[1:-1]
            if len(inner) <= limit:
                return literal
            count += 1
            omitted = len(inner) - keep
            return f'"{inner[:keep]}… [+{omitted} chars]"'

        return _LONG_STRING_RE.sub(repl, text), count

    # -- JSON -------------------------------------------------------------
    def trim_json(self, json_str: str) -> Tuple[str, bool]:
        """Re-serialize JSON with depth and list caps. Returns (text, ok)."""
        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return json_str, False
        trimmed = self._trim_obj(data, self.config.max_json_depth)
        return json.dumps(trimmed, ensure_ascii=False, indent=2), True

    def _trim_obj(self, obj: Any, depth: int) -> Any:
        if depth <= 0:
            if isinstance(obj, dict):
                return f"{{… {len(obj)} keys}}"
            if isinstance(obj, list):
                return f"[… {len(obj)} items]"
            return obj
        if isinstance(obj, dict):
            return {k: self._trim_obj(v, depth - 1) for k, v in obj.items()}
        if isinstance(obj, list):
            cap = self.config.max_list_items
            head = [self._trim_obj(x, depth - 1) for x in obj[:cap]]
            if len(obj) > cap:
                head.append(f"… (+{len(obj) - cap} more items)")
            return head
        if isinstance(obj, str) and len(obj) > self.config.max_string_length:
            keep = self.config.keep_string_prefix
            return f"{obj[:keep]}… [+{len(obj) - keep} chars]"
        return obj

    # -- tabular runs -----------------------------------------------------
    def trim_tables(self, text: str) -> Tuple[str, int]:
        lines = text.split("\n")
        out: List[str] = []
        i = 0
        trimmed = 0
        max_rows = self.config.max_table_rows
        while i < len(lines):
            if _TABLE_ROW_RE.match(lines[i]):
                start = i
                while i < len(lines) and _TABLE_ROW_RE.match(lines[i]):
                    i += 1
                block = lines[start:i]
                if len(block) > max_rows:
                    out.extend(block[:max_rows])
                    hidden = len(block) - max_rows
                    out.append(f"… (+{hidden} more rows)")
                    trimmed += hidden
                else:
                    out.extend(block)
            else:
                out.append(lines[i])
                i += 1
        return "\n".join(out), trimmed

    # -- log metadata -----------------------------------------------------
    _LOG_PREFIX_RE = re.compile(
        r"^\s*\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}[.,\d]*Z?\s*[-|]?\s*"
        r"(?:pid[=:]?\s*\d+\s*[-|]?\s*)?"
        r"(?:thread[_\s-]*id[=:]?\s*\d+\s*[-|]?\s*)?",
        re.IGNORECASE,
    )

    def _strip_log_metadata(self, text: str) -> Tuple[str, int]:
        out: List[str] = []
        count = 0
        for line in text.split("\n"):
            new = self._LOG_PREFIX_RE.sub("", line)
            if new != line:
                count += 1
            out.append(new)
        return "\n".join(out), count
