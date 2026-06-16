import io

import pytest

from context_compressor import cli


def _run(argv, stdin=""):
    import sys
    old_in = sys.stdin
    sys.stdin = io.StringIO(stdin)
    try:
        rc = cli.main(argv)
    finally:
        sys.stdin = old_in
    return rc


def test_cli_stdin_roundtrip(capsys):
    rc = _run([], stdin="Connecting...\nreal data\nreal data\n")
    out = capsys.readouterr().out
    assert rc == 0
    assert "real data" in out
    assert "Connecting" not in out


def test_cli_stats_to_stderr(capsys):
    rc = _run(["--stats"], stdin="port 22 open\nport 22 open\n")
    captured = capsys.readouterr()
    assert rc == 0
    assert "tokens" in captured.err
    assert "port 22 open" in captured.out


def test_cli_security_mode(capsys):
    scan = "SQL injection at https://x.com/a?id=1\nport 80 open\n"
    rc = _run(["--security"], stdin=scan)
    out = capsys.readouterr().out
    assert rc == 0
    assert "Security Scan Summary" in out


def test_cli_reads_file(tmp_path, capsys):
    p = tmp_path / "in.txt"
    p.write_text("Loading...\nkeep me\n")
    rc = cli.main([str(p)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "keep me" in out
    assert "Loading" not in out


def test_cli_preset_and_target(capsys):
    rc = _run(["--preset", "aggressive", "--target", "0.5"],
              stdin="alpha beta gamma\n")
    assert rc == 0
