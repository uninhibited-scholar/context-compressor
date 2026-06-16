"""Domain-specific summarizer for security scan output.

Vulnerability scanners (Nessus, nmap, nuclei, ZAP, …) emit thousands of lines
that are 90% boilerplate. This summarizer classifies findings by type, ranks
them by severity, keeps a few concrete examples (URLs / hosts) per class, and
produces a compact, decision-ready brief.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Tuple


class Severity(IntEnum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


_SEVERITY_ICON = {
    Severity.CRITICAL: "🔴",
    Severity.HIGH: "🟠",
    Severity.MEDIUM: "🟡",
    Severity.LOW: "🟢",
    Severity.INFO: "ℹ️",
}

# (label, compiled regex, default severity)
_VULN_RULES: List[Tuple[str, re.Pattern, Severity]] = [
    ("SQL Injection",
     re.compile(r"sql[\s_-]?injection|sqli\b|union\s+select", re.I),
     Severity.CRITICAL),
    ("Command Injection",
     re.compile(r"command[\s_-]?injection|os[\s_-]?command|rce\b|remote code",
                re.I), Severity.CRITICAL),
    ("Cross-Site Scripting (XSS)",
     re.compile(r"\bxss\b|cross[\s_-]?site[\s_-]?scripting", re.I),
     Severity.HIGH),
    ("Path Traversal",
     re.compile(r"path[\s_-]?traversal|directory[\s_-]?traversal|\.\./", re.I),
     Severity.HIGH),
    ("Sensitive Data / Cleartext",
     re.compile(r"cleartext|plain[\s_-]?text\s+password|unencrypted", re.I),
     Severity.HIGH),
    ("Weak / Default Credentials",
     re.compile(r"weak[\s_-]?password|default[\s_-]?credential|"
                r"anonymous\s+login", re.I), Severity.MEDIUM),
    ("Open Port / Service",
     re.compile(r"\bport\s+\d+\s+open|open\s+port|\bopen\b.*tcp", re.I),
     Severity.LOW),
    ("Outdated Component",
     re.compile(r"outdated|end[\s_-]?of[\s_-]?life|deprecated\s+version", re.I),
     Severity.MEDIUM),
    ("Misconfiguration",
     re.compile(r"misconfigur|improper\s+config|insecure\s+config|"
                r"directory\s+listing", re.I), Severity.MEDIUM),
]

_URL_RE = re.compile(r"https?://[^\s\"'<>]+")
_HOST_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b")
_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.I)


@dataclass
class Finding:
    label: str
    severity: Severity
    count: int = 0
    examples: List[str] = field(default_factory=list)
    cves: set = field(default_factory=set)


class SecuritySummarizer:
    """Classify and summarize raw scanner output."""

    def __init__(self, examples_per_type: int = 3) -> None:
        self.examples_per_type = examples_per_type

    def classify(self, scan_output: str) -> Dict[str, Finding]:
        findings: Dict[str, Finding] = {}
        for line in scan_output.split("\n"):
            for label, rx, severity in _VULN_RULES:
                if not rx.search(line):
                    continue
                f = findings.get(label)
                if f is None:
                    f = Finding(label=label, severity=severity)
                    findings[label] = f
                f.count += 1
                for cve in _CVE_RE.findall(line):
                    f.cves.add(cve.upper())
                if len(f.examples) < self.examples_per_type:
                    example = self._extract_example(line)
                    if example and example not in f.examples:
                        f.examples.append(example)
                break  # one classification per line
        return findings

    @staticmethod
    def _extract_example(line: str) -> str:
        m = _URL_RE.search(line) or _HOST_RE.search(line)
        if m:
            return m.group(0)[:100]
        return line.strip()[:100]

    def summarize(self, scan_output: str) -> str:
        findings = self.classify(scan_output)
        if not findings:
            return "【Security Scan Summary】\nNo recognizable findings detected."

        total = sum(f.count for f in findings.values())
        ordered = sorted(findings.values(),
                         key=lambda f: (f.severity, -f.count))

        lines = ["【Security Scan Summary】", "",
                 f"Detected {total} findings across {len(findings)} categories.",
                 ""]
        for f in ordered:
            icon = _SEVERITY_ICON[f.severity]
            header = f"{icon} {f.label} [{f.severity.name}]: {f.count}"
            if f.cves:
                header += f"  ({', '.join(sorted(f.cves)[:5])})"
            lines.append(header)
            for i, ex in enumerate(f.examples, 1):
                lines.append(f"    {i}. {ex}")
            remaining = f.count - len(f.examples)
            if remaining > 0:
                lines.append(f"    … and {remaining} more")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"
