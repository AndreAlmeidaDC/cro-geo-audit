#!/usr/bin/env python3
"""
Technical Audit Script for CRO/GEO Analysis.
Runs automated checks on a target URL: performance, headers, robots.txt, sitemap, SSL.
Usage: python technical_audit.py <url>
Output: JSON report to stdout.

Security note on subprocess usage:
This script calls `curl` via subprocess.run with an argument LIST (never a shell
string) and never uses shell=True. The target URL is passed as an isolated list
element, so it cannot be interpreted as a shell command or inject extra arguments.
Each call sets an explicit timeout. This is a deliberate, allowlisted command with
structured arguments, not dynamic code execution.
"""

import sys
import json
import time
import ssl
import socket
from urllib.parse import urlparse
import subprocess

def run_curl_timing(url: str) -> dict:
    """Measure response times via curl."""
    fmt = json.dumps({
        "dns_lookup": "%{time_namelookup}",
        "tcp_connect": "%{time_connect}",
        "ssl_handshake": "%{time_appconnect}",
        "ttfb": "%{time_starttransfer}",
        "total": "%{time_total}",
        "http_code": "%{http_code}",
        "size_download": "%{size_download}",
        "speed_download": "%{speed_download}",
    })
    try:
        result = subprocess.run(
            ["curl", "-o", "/dev/null", "-s", "-w", fmt, "-L", "--max-time", "15", url],
            capture_output=True, text=True, timeout=20
        )
        data = json.loads(result.stdout)
        return {k: float(v) if k != "http_code" else int(float(v)) for k, v in data.items()}
    except Exception as e:
        return {"error": str(e)}

def get_headers(url: str) -> dict:
    """Fetch HTTP response headers."""
    try:
        result = subprocess.run(
            ["curl", "-sI", "-L", "--max-time", "10", url],
            capture_output=True, text=True, timeout=15
        )
        headers = {}
        for line in result.stdout.strip().split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip().lower()] = val.strip()
        return headers
    except Exception as e:
        return {"error": str(e)}

def check_security_headers(headers: dict) -> list:
    """Evaluate security headers presence."""
    checks = [
        ("strict-transport-security", "HSTS"),
        ("x-content-type-options", "X-Content-Type-Options"),
        ("x-frame-options", "X-Frame-Options"),
        ("content-security-policy", "CSP"),
        ("referrer-policy", "Referrer-Policy"),
        ("permissions-policy", "Permissions-Policy"),
        ("x-xss-protection", "X-XSS-Protection"),
    ]
    results = []
    for header_key, label in checks:
        present = header_key in headers
        results.append({
            "header": label,
            "present": present,
            "value": headers.get(header_key, ""),
            "severity": "low" if present else ("high" if label in ["HSTS", "CSP"] else "medium"),
        })
    return results

def check_robots_txt(url: str) -> dict:
    """Fetch and analyze robots.txt for AI crawler blocking."""
    robots_url = url.rstrip("/") + "/robots.txt"
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "10", robots_url],
            capture_output=True, text=True, timeout=15
        )
        content = result.stdout
        ai_bots = [
            "GPTBot", "Google-Extended", "ChatGPT-User", "CCBot",
            "anthropic-ai", "ClaudeBot", "Bytespider", "Amazonbot",
            "FacebookBot", "PerplexityBot", "Applebot-Extended", "Cohere-ai"
        ]
        blocked = []
        allowed = []
        for bot in ai_bots:
            if bot.lower() in content.lower():
                lines = content.lower().split("\n")
                is_blocked = any("disallow: /" in l for l in lines if bot.lower() in "".join(lines[max(0, lines.index(l)-3):lines.index(l)+1]))
                if is_blocked or f"user-agent: {bot.lower()}" in content.lower():
                    blocked.append(bot)
                else:
                    allowed.append(bot)
            else:
                allowed.append(bot)
        # Simple heuristic: check for blanket disallow after specific user-agents
        blanket_blocks = content.lower().count("disallow: /\n")
        user_agents_count = content.lower().count("user-agent:")
        return {
            "exists": len(content) > 10,
            "content_length": len(content),
            "ai_bots_total": len(ai_bots),
            "ai_bots_blocked": blocked,
            "ai_bots_allowed": allowed,
            "blocked_count": len(blocked),
            "allowed_count": len(allowed),
            "blanket_disallow_count": blanket_blocks,
            "user_agents_count": user_agents_count,
        }
    except Exception as e:
        return {"exists": False, "error": str(e)}

def check_sitemap(url: str) -> dict:
    """Check sitemap.xml existence and basic stats."""
    sitemap_url = url.rstrip("/") + "/sitemap.xml"
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "10", "-o", "/dev/null", "-w", "%{http_code}", sitemap_url],
            capture_output=True, text=True, timeout=15
        )
        code = int(result.stdout.strip())
        if code == 200:
            content = subprocess.run(
                ["curl", "-s", "--max-time", "10", sitemap_url],
                capture_output=True, text=True, timeout=15
            ).stdout
            url_count = content.lower().count("<url>") or content.lower().count("<loc>")
            return {"exists": True, "http_code": code, "url_count": url_count}
        return {"exists": False, "http_code": code}
    except Exception as e:
        return {"exists": False, "error": str(e)}

def check_ssl(hostname: str) -> dict:
    """Check SSL certificate validity and expiration."""
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(10)
            s.connect((hostname, 443))
            cert = s.getpeercert()
            return {
                "valid": True,
                "issuer": dict(x[0] for x in cert.get("issuer", [])).get("organizationName", "Unknown"),
                "expires": cert.get("notAfter", "Unknown"),
                "subject": dict(x[0] for x in cert.get("subject", [])).get("commonName", "Unknown"),
            }
    except Exception as e:
        return {"valid": False, "error": str(e)}

def main():
    if len(sys.argv) < 2:
        print("Usage: python technical_audit.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    if not url.startswith("http"):
        url = "https://" + url

    hostname = urlparse(url).hostname
    print(json.dumps({"status": "starting", "url": url}, indent=2), file=sys.stderr)

    report = {
        "url": url,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "performance": run_curl_timing(url),
        "headers": {},
        "security_headers": [],
        "robots_txt": {},
        "sitemap": {},
        "ssl": {},
    }

    raw_headers = get_headers(url)
    report["headers"] = raw_headers
    report["security_headers"] = check_security_headers(raw_headers)
    report["robots_txt"] = check_robots_txt(url)
    report["sitemap"] = check_sitemap(url)
    report["ssl"] = check_ssl(hostname)

    # Calculate scores
    perf = report["performance"]
    if "error" not in perf:
        ttfb = perf.get("ttfb", 5)
        total = perf.get("total", 10)
        perf_score = max(0, min(100, int(100 - (ttfb * 30) - (total * 5))))
    else:
        perf_score = 0

    sec_present = sum(1 for h in report["security_headers"] if h["present"])
    sec_score = int((sec_present / len(report["security_headers"])) * 100) if report["security_headers"] else 0

    robots = report["robots_txt"]
    geo_blocked = robots.get("blocked_count", 0)
    geo_total = robots.get("ai_bots_total", 12)
    geo_score = max(0, int(((geo_total - geo_blocked) / geo_total) * 100)) if geo_total > 0 else 0

    report["scores"] = {
        "performance": perf_score,
        "security": sec_score,
        "geo_visibility": geo_score,
    }

    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
