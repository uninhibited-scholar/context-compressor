"""Turn thousands of lines of scanner output into a decision-ready brief.

    python examples/security_scan_compression.py
"""

from context_compressor import ContextCompressor

# A tiny stand-in for real Nessus/nmap/nuclei output.
SCAN = """
[*] Starting scan of 10.0.0.0/24
10.0.0.5 port 22 open (ssh)
10.0.0.5 port 80 open (http)
10.0.0.5 port 443 open (https)
[!] SQL Injection detected at https://shop.local/search?q=test (CVE-2024-2117)
[!] SQL injection confirmed at https://shop.local/item?id=42
[!] Reflected XSS at https://shop.local/feedback?msg=hello
[!] Stored XSS at https://shop.local/profile/bio
[!] Command injection via https://shop.local/ping?host=8.8.8.8
[!] Weak password policy on admin portal
[!] Default credentials found: admin/admin on https://shop.local/admin
[!] Cleartext password transmission over http on login form
[*] 4096 hosts scanned, 9 findings, scan complete in 1843s
""".strip()


def main() -> None:
    compressor = ContextCompressor()
    brief = compressor.compress_security_scan(SCAN, examples_per_type=2)
    print(brief)


if __name__ == "__main__":
    main()
