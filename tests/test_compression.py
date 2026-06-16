from context_compressor import CompressionConfig, ContextCompressor
from context_compressor.utils.token_counter import TokenCounter


def _noisy_log(n=200):
    lines = []
    for i in range(n):
        lines.append(f"2024-01-15 10:30:{i % 60:02d} [INFO] heartbeat ok")
        lines.append("Connecting to upstream...")
        lines.append("port 22 open")
    lines.append("CRITICAL: disk almost full on /var")
    return "\n".join(lines)


def test_compress_reduces_tokens_and_keeps_signal():
    text = _noisy_log()
    result = ContextCompressor().compress(text)
    assert result.stats.compressed_tokens < result.stats.original_tokens
    assert result.stats.reduction_pct > 30
    # The single important line survives.
    assert "disk almost full" in result.compressed


def test_stats_consistency():
    text = _noisy_log(50)
    result = ContextCompressor().compress(text)
    s = result.stats
    assert s.original_chars == len(text)
    assert s.compressed_chars == len(result.compressed)
    assert 0 < s.token_ratio <= 1.0
    assert s.tokens_saved == s.original_tokens - s.compressed_tokens
    assert s.token_backend in ("tiktoken", "heuristic")
    assert len(s.stages) >= 1


def test_target_ratio_triggers_summarizer():
    # Genuinely distinct sentences so rule-based stages can't hit 0.2 and the
    # extractive summarizer has to kick in.
    topics = [
        "earthquakes", "rainfall", "harvest yields", "river levels",
        "bird migration", "solar flares", "traffic patterns", "stock prices",
        "vaccine trials", "coral reefs", "glacier melt", "wildfire spread",
    ]
    text = "\n".join(
        f"In {1900 + i} the researchers measured {topic} and recorded a "
        f"value of {i * 7 % 53} across the {topic} survey region."
        for i, topic in enumerate(topics * 5)
    )
    # Disable the rule stages so this test isolates the summarizer fallback:
    # when rules can't reach the target, extractive summarization must run.
    cfg = CompressionConfig(
        target_ratio=0.2,
        enable_noise_filter=False,
        enable_detail_trim=False,
        enable_pattern_remover=False,
        enable_redundancy_filter=False,
    )
    result = ContextCompressor(cfg).compress(text)
    stage_names = [s.name for s in result.stats.stages]
    assert "extractive" in stage_names
    assert result.stats.token_ratio < 1.0


def test_presets_construct_and_run():
    text = _noisy_log(30)
    for cfg in (CompressionConfig.aggressive(),
                CompressionConfig.conservative()):
        result = ContextCompressor(cfg).compress(text)
        assert result.compressed
        assert result.stats.compressed_tokens <= result.stats.original_tokens


def test_empty_input():
    result = ContextCompressor().compress("")
    assert result.compressed == ""
    assert result.stats.reduction_pct == 0.0


def test_token_counter_backend_and_counts():
    tc = TokenCounter()
    assert tc.count("") == 0
    assert tc.count("hello world") > 0
    assert tc.backend in ("tiktoken", "heuristic")
