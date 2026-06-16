"""Compress a multi-turn agent transcript before re-feeding it to the model.

Demonstrates the ``target_ratio`` path, which falls back to extractive
summarization when rule-based filtering alone is not enough.

    python examples/chat_history_compression.py
"""

from context_compressor import CompressionConfig, ContextCompressor

TRANSCRIPT = """
User: Can you find the slow query in the orders service?
Assistant: I have already queried the database for the slow query log.
Assistant: Let me analyze the slow query log to find the bottleneck.
Assistant: I have already queried the database for the slow query log.
Assistant: The slowest query is a full table scan on orders.created_at.
Assistant: I recommend adding an index on orders.created_at to fix it.
User: Great, can you also check the payments service?
Assistant: I have already queried the database for the payments service.
Assistant: The payments service has no obvious slow queries right now.
""".strip()


def main() -> None:
    cfg = CompressionConfig(target_ratio=0.5)
    result = ContextCompressor(cfg).compress(TRANSCRIPT)
    print("COMPRESSED TRANSCRIPT:\n")
    print(result.compressed)
    print("\n" + result.stats.summary())


if __name__ == "__main__":
    main()
