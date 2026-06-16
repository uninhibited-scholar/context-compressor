from context_compressor.summarizers.security_summarizer import (
    SecuritySummarizer,
    Severity,
)

SCAN = """
[10:00:01] Starting scan of 192.168.1.0/24
192.168.1.10 port 22 open
192.168.1.10 port 80 open
Possible SQL Injection at https://example.com/search?q=1 (CVE-2024-1234)
SQL injection confirmed https://example.com/item?id=2
Reflected XSS found at https://example.com/comment
Stored XSS at https://example.com/profile
Weak password detected for admin account
Default credentials on https://example.com/admin
Server uses cleartext password transmission over http
""".strip()


def test_classify_counts_and_severity():
    s = SecuritySummarizer()
    findings = s.classify(SCAN)
    assert "SQL Injection" in findings
    assert findings["SQL Injection"].severity == Severity.CRITICAL
    assert findings["SQL Injection"].count == 2
    assert "Cross-Site Scripting (XSS)" in findings
    assert findings["Cross-Site Scripting (XSS)"].count == 2
    assert "CVE-2024-1234" in findings["SQL Injection"].cves


def test_summary_orders_by_severity_and_is_compact():
    s = SecuritySummarizer()
    summary = s.summarize(SCAN)
    assert "Security Scan Summary" in summary
    # CRITICAL section appears before LOW (open port) section.
    assert summary.index("SQL Injection") < summary.index("Open Port")
    assert len(summary) < len(SCAN) * 2  # it's a brief, includes examples
    assert "https://example.com" in summary


def test_no_findings():
    summary = SecuritySummarizer().summarize("everything looks fine here")
    assert "No recognizable findings" in summary
