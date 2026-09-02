#!/usr/bin/env python3
"""Collect transport, header, robots and sitemap evidence without synthetic scores."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any

from audit_common import FetchResult, evidence, fetch_text, join_origin, validate_public_url

SCHEMA_VERSION = "3.0"
SECURITY_HEADERS = {
    "strict-transport-security": "HSTS is relevant only on HTTPS responses and should be evaluated with max-age and includeSubDomains context.",
    "content-security-policy": "Presence alone does not prove an effective policy; inspect directives and report-only versus enforced mode.",
    "x-content-type-options": "Commonly expected as nosniff.",
    "referrer-policy": "Evaluate value and product needs; presence alone is not a grade.",
    "permissions-policy": "Evaluate allowed features against actual product requirements.",
    "cross-origin-opener-policy": "Useful for isolation in some applications; applicability is contextual.",
}


def _header_observations(headers: dict[str, str]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for name, note in SECURITY_HEADERS.items():
        output[name] = evidence("observed", "http_response_headers", "high", "response", {
            "present": name in headers,
            "value": headers.get(name, ""),
        }, note)
    frame_protection = bool(headers.get("x-frame-options")) or "frame-ancestors" in headers.get("content-security-policy", "").lower()
    output["frame_embedding_control"] = evidence(
        "observed", "http_response_headers", "high", "response",
        {"present": frame_protection, "x_frame_options": headers.get("x-frame-options", ""),
         "csp_has_frame_ancestors": "frame-ancestors" in headers.get("content-security-policy", "").lower()},
        "Either CSP frame-ancestors or X-Frame-Options may provide framing control; policy semantics require manual review.",
    )
    return output


def assemble_report(url: str, page: FetchResult, robots: FetchResult, sitemap: FetchResult) -> dict[str, Any]:
    transport_status = "measured" if page.status is not None or page.error_type else "not_measured"
    return {
        "schema_version": SCHEMA_VERSION,
        "methodology": {
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "mode": "single-request laboratory observation",
            "does_not_measure": [
                "Core Web Vitals", "real-user performance", "conversion", "security exploitability",
                "search ranking", "AI citation or visibility",
            ],
        },
        "target": url,
        "transport": evidence(
            transport_status, "verified_http_fetch", "high" if page.transport_verified else "low", "request",
            {"requested_url": page.requested_url, "final_url": page.final_url, "status": page.status,
             "transport_verified": page.transport_verified, "error_type": page.error_type},
            page.error or "TLS is verified with the platform trust store; certificate failures are reported, never bypassed.",
        ),
        "single_request_timing": evidence(
            "measured" if page.elapsed_ms is not None else "not_measured", "single_http_request", "low", "request",
            {"elapsed_ms": page.elapsed_ms},
            "This is not a Core Web Vitals measurement and must not be used as field performance or user-experience evidence.",
        ),
        "response_headers": evidence("observed", "http_response_headers", "high", "response", page.headers),
        "security_header_observations": _header_observations(page.headers),
        "robots_fetch": evidence(
            "observed" if robots.status is not None else "not_measured", "verified_http_fetch",
            "high" if robots.transport_verified else "low", "site",
            {"status": robots.status, "final_url": robots.final_url, "bytes": len(robots.body.encode("utf-8")),
             "truncated": robots.truncated}, robots.error or "",
        ),
        "sitemap_fetch": evidence(
            "observed" if sitemap.status is not None else "not_measured", "verified_http_fetch",
            "high" if sitemap.transport_verified else "low", "site",
            {"status": sitemap.status, "final_url": sitemap.final_url, "bytes": len(sitemap.body.encode("utf-8")),
             "truncated": sitemap.truncated}, sitemap.error or "",
        ),
        "recommended_follow_up": [
            "Use CrUX or another field-data source for Core Web Vitals when available.",
            "Use a controlled browser run for rendering, interaction and laboratory performance diagnostics.",
            "Review security-header values and application context; presence/absence is not a security assessment.",
        ],
    }


def run(url: str, allow_private: bool = False, timeout: float = 15.0) -> dict[str, Any]:
    target = validate_public_url(url, allow_private=allow_private)
    page = fetch_text(target, timeout=timeout, allow_private=allow_private)
    robots = fetch_text(join_origin(target, "/robots.txt"), timeout=timeout, allow_private=allow_private)
    sitemap = fetch_text(join_origin(target, "/sitemap.xml"), timeout=timeout, allow_private=allow_private)
    return assemble_report(target, page, robots, sitemap)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect technical evidence without synthetic performance, security or GEO scores.")
    parser.add_argument("url")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--allow-private", action="store_true", help="Explicitly allow private/internal targets. Off by default to prevent SSRF.")
    args = parser.parse_args()
    try:
        report = run(args.url, args.allow_private, args.timeout)
    except ValueError as exc:
        json.dump({"schema_version": SCHEMA_VERSION, "status": "not_measured", "error": str(exc)}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
