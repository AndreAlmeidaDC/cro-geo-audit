#!/usr/bin/env python3
"""Collect page-level SEO surface evidence without a synthetic SEO score."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any

from audit_common import FetchResult, evidence, fetch_text, validate_public_url
from geo_audit import analyze_html

SCHEMA_VERSION = "3.0"


def _findings(surface: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    title = surface["title"]["value"]
    description = surface["meta_description"]["value"]
    canonical = surface["canonical"]["value"]
    headings = surface["headings"]["value"]["counts"]
    json_ld = surface["json_ld"]["value"]
    images_without_alt = surface["structured_elements"]["value"]["images_without_alt_attribute"]

    if not title:
        items.append({"severity": "high", "status": "observed", "finding": "Missing HTML title",
                      "recommendation": "Add a page-specific title that identifies the entity and intent."})
    if not description:
        items.append({"severity": "medium", "status": "observed", "finding": "Missing meta description",
                      "recommendation": "Add an accurate page-specific description; snippet selection remains engine-controlled."})
    if not canonical:
        items.append({"severity": "medium", "status": "observed", "finding": "Canonical link not observed",
                      "recommendation": "Confirm whether a self-referencing or cross-page canonical is appropriate for this URL."})
    if headings.get("h1", 0) != 1:
        items.append({"severity": "medium", "status": "observed", "finding": f"Observed H1 count: {headings.get('h1', 0)}",
                      "recommendation": "Review the page's primary heading and semantic outline in rendered output."})
    if json_ld["invalid_blocks"]:
        items.append({"severity": "high", "status": "observed", "finding": f"Invalid JSON-LD blocks: {json_ld['invalid_blocks']}",
                      "recommendation": "Repair JSON-LD and verify that marked-up claims match visible content."})
    if images_without_alt:
        items.append({"severity": "medium", "status": "observed", "finding": f"Images without an alt attribute: {images_without_alt}",
                      "recommendation": "Add useful alternatives for informative images and empty alt text for decorative images."})
    return items


def analyze_fetches(fetches: list[FetchResult]) -> dict[str, Any]:
    pages: list[dict[str, Any]] = []
    for item in fetches:
        if item.body:
            surface = analyze_html(item.body, item.final_url or item.requested_url)
            findings = _findings(surface)
        else:
            surface = {"status": evidence("not_measured", "rendered_html", "low", "page", None,
                                          "No page body was available for analysis.")}
            findings = [{"severity": "high", "status": "not_measured", "finding": "Page HTML unavailable",
                         "recommendation": "Resolve transport or rendering access, then repeat the audit."}]
        pages.append({
            "url": item.requested_url,
            "fetch": evidence(
                "observed" if item.status is not None else "not_measured", "verified_http_fetch",
                "high" if item.transport_verified else "low", "page",
                {"status": item.status, "final_url": item.final_url, "transport_verified": item.transport_verified,
                 "truncated": item.truncated}, item.error or "",
            ),
            "surface": surface,
            "findings": findings,
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "methodology": {
            "claim": "page-level observable metadata and semantic surface",
            "does_not_measure": ["ranking", "indexation", "click-through rate", "AI citation probability"],
        },
        "pages": pages,
    }


def run(urls: list[str], allow_private: bool = False, timeout: float = 15.0) -> dict[str, Any]:
    fetches = [fetch_text(validate_public_url(url, allow_private=allow_private), timeout=timeout,
                          allow_private=allow_private) for url in urls]
    return analyze_fetches(fetches)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect page metadata and semantic HTML without synthetic scores.")
    parser.add_argument("urls", nargs="+")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--allow-private", action="store_true", help="Explicitly allow private/internal targets. Off by default to prevent SSRF.")
    args = parser.parse_args()
    try:
        report = run(args.urls, args.allow_private, args.timeout)
    except ValueError as exc:
        json.dump({"schema_version": SCHEMA_VERSION, "status": "not_measured", "error": str(exc)}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
