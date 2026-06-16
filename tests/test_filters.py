from context_compressor.config import (
    NoiseConfig,
    RedundancyConfig,
    TrimConfig,
)
from context_compressor.filters.detail_trim import DetailTrimmer
from context_compressor.filters.noise_filter import NoiseFilter
from context_compressor.filters.pattern_remover import PatternRemover
from context_compressor.filters.redundancy_filter import RedundancyFilter


def test_noise_filter_drops_timestamps_and_progress():
    text = "\n".join([
        "2024-01-15 10:30:45",
        "real data line",
        "████████░░ 80%",
        "Connecting to host...",
        "another real line",
        "-------------------",
    ])
    cleaned, stats = NoiseFilter().filter(text)
    assert "real data line" in cleaned
    assert "another real line" in cleaned
    assert "2024-01-15" not in cleaned
    assert "80%" not in cleaned
    assert "Connecting" not in cleaned
    assert "----" not in cleaned
    assert stats.get("timestamp") == 1
    assert stats.get("progress_bar") == 1


def test_noise_filter_keeps_log_levels_by_default():
    text = "[ERROR] something broke\n[INFO]"
    cleaned, _ = NoiseFilter(NoiseConfig()).filter(text)
    # ERROR lines with payload are never matched; bare INFO only if opted in.
    assert "[ERROR] something broke" in cleaned
    assert "[INFO]" in cleaned


def test_noise_filter_collapses_blank_runs():
    text = "a\n\n\n\nb"
    cleaned, _ = NoiseFilter().filter(text)
    assert cleaned == "a\n\nb"


def test_redundancy_exact_dedup_annotates_counts():
    text = "port 22 open\nport 22 open\nport 22 open\nunique line"
    out, stats = RedundancyFilter().filter(text)
    assert "port 22 open  [x3]" in out
    assert "unique line" in out
    assert stats["exact_removed"] == 2


def test_redundancy_near_dedup_opt_in():
    cfg = RedundancyConfig(near_duplicate=True, similarity_threshold=0.8)
    text = "the server returned an error code 500\n" \
           "the server returned an error code 501"
    out, stats = RedundancyFilter(cfg).filter(text)
    assert stats["near_removed"] >= 1
    assert out.count("the server returned") == 1


def test_detail_trim_long_strings():
    long_val = "x" * 300
    text = f'{{"ua": "{long_val}"}}'
    out, n = DetailTrimmer().trim_long_strings(text)
    assert "[+" in out and "chars]" in out
    assert n == 1
    assert len(out) < len(text)


def test_detail_trim_json_depth_and_list():
    cfg = TrimConfig(max_json_depth=2, max_list_items=3)
    nested = '{"a": {"b": {"c": {"d": 1}}}, "items": [1,2,3,4,5,6]}'
    out, ok = DetailTrimmer(cfg).trim_json(nested)
    assert ok
    assert "more items" in out  # list truncated
    assert "keys" in out or "items]" in out  # depth capped


def test_detail_trim_tables():
    rows = "\n".join(f"| host{i} | open |" for i in range(30))
    cfg = TrimConfig(max_table_rows=5)
    out, n = DetailTrimmer(cfg).trim_tables(rows)
    assert "more rows" in out
    assert n == 25
    assert out.count("| host") == 5


def test_detail_trim_strips_log_metadata():
    line = "2024-01-15 10:30:45.123 - pid=42 - thread_id=7 - Error: boom"
    out, n = DetailTrimmer()._strip_log_metadata(line)
    assert out.strip() == "Error: boom"
    assert n == 1


def test_pattern_remover_collapses_repeated_phrasing():
    text = (
        "I have already queried the database for results.\n"
        "Now let me analyze the output carefully.\n"
        "I have already queried the database for results.\n"
    )
    out, stats = PatternRemover(similarity_threshold=0.9).filter(text)
    assert stats["phrases_removed"] == 1
    assert out.count("already queried the database") == 1
