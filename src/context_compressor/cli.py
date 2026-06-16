"""Command-line interface: ``context-compress``.

Read text from a file or stdin, compress it, and write the result to stdout.
Compression metrics go to stderr so the compressed text can be piped cleanly.

Examples
--------
    context-compress scan.log
    cat transcript.txt | context-compress --preset aggressive
    context-compress report.txt --security
    context-compress big.log --target 0.3 --stats
"""

from __future__ import annotations

import argparse
import sys

from .config import CompressionConfig
from .core.compressor import ContextCompressor


def _build_config(args: argparse.Namespace) -> CompressionConfig:
    if args.preset == "aggressive":
        cfg = CompressionConfig.aggressive()
    elif args.preset == "conservative":
        cfg = CompressionConfig.conservative()
    else:
        cfg = CompressionConfig()
    if args.target is not None:
        cfg.target_ratio = args.target
    if args.model:
        cfg.model = args.model
    return cfg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="context-compress",
        description="Compress LLM context (logs, transcripts, scan output).",
    )
    parser.add_argument("input", nargs="?", default="-",
                        help="Input file, or '-' for stdin (default).")
    parser.add_argument("--preset", choices=["default", "aggressive",
                                             "conservative"], default="default")
    parser.add_argument("--target", type=float, default=None,
                        help="Desired size ratio 0-1 (enables summarization).")
    parser.add_argument("--model", default=None,
                        help="Model name for token counting (e.g. gpt-4).")
    parser.add_argument("--security", action="store_true",
                        help="Summarize as a security scan instead.")
    parser.add_argument("--stats", action="store_true",
                        help="Print compression metrics to stderr.")
    args = parser.parse_args(argv)

    if args.input == "-":
        text = sys.stdin.read()
    else:
        with open(args.input, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()

    compressor = ContextCompressor(_build_config(args))

    if args.security:
        out = compressor.compress_security_scan(text)
        sys.stdout.write(out)
        return 0

    result = compressor.compress(text)
    sys.stdout.write(result.compressed)
    if not result.compressed.endswith("\n"):
        sys.stdout.write("\n")

    if args.stats:
        sys.stderr.write("\n" + result.stats.summary() + "\n")
        for stage in result.stats.stages:
            sys.stderr.write(
                f"  - {stage.name}: {stage.chars_removed} chars removed "
                f"{stage.details}\n"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
