"""Basic usage: compress a noisy log and report token savings.

    python examples/basic_compress.py
"""

from context_compressor import ContextCompressor

RAW = """
2024-01-15 10:30:45 [INFO] starting worker pool
Connecting to database...
Connected to database
2024-01-15 10:30:46 [INFO] heartbeat
2024-01-15 10:30:47 [INFO] heartbeat
██████████ 100%
SELECT id, name FROM users; -- Rows returned: 1042
user 1: alice
user 1: alice
user 1: alice
WARNING: disk usage at 92% on /var
WARNING: disk usage at 92% on /var
ERROR: failed to write checkpoint: No space left on device
""".strip()


def main() -> None:
    compressor = ContextCompressor()
    result = compressor.compress(RAW)

    print("=" * 60)
    print("ORIGINAL:")
    print(RAW)
    print("=" * 60)
    print("COMPRESSED:")
    print(result.compressed)
    print("=" * 60)
    print(result.stats.summary())


if __name__ == "__main__":
    main()
