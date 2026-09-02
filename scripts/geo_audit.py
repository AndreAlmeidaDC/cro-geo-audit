#!/usr/bin/env python3
"""Evidence-based search and AI-discovery readiness audit.

This collector reports observable technical and content signals. It does not calculate
or imply a universal GEO score, assistant ranking, citation probability, or visibility
verdict. First-party product data and controlled query experiments remain separate
measurement sources.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.robotparser
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Iterable

from audit_common import evidence, fetch_text, join_origin, validate_public_url

SCHEMA_VERSION = "3.0"
CRAWLER_REGISTRY_VERIFIED_AT = "2026-09-02"
CRAWLERS: dict[str, dict[str, str]] = {
    "OAI-SearchBot": {
        "provider": "OpenAI",
        "purpose": "search_discovery",
        "note": "Search/discovery crawler; distinct from model-training and user-initiated fetch controls.",
    },
    "GPTBot": {
        "provider": "OpenAI",
        "purpose": "model_training",
        "note": "Model-training crawler; blocking it is not equivalent to opting out of OpenAI search inclusion.",
    },
    "ChatGPT-User": {
        "provider": "OpenAI",
        "purpose": "user_initiated_fetch",
        "note": "User-initiated retrieval surface; behavior and controls should be reviewed separately.",
    },
    "Googlebot": {
        "provider": "Google",
        "purpose": "search_indexing",
        "note": "Search indexing crawler. AI search eligibility relies on normal Google Search technical requirements.",
    },
    "Google-Extended": {
        "provider": "Google",
        "purpose": "ai_model_control",
        "note": "A separate control token; it should not be conflated with Googlebot search indexing.",
    },
    "Bingbot": {
        "provider": "Microsoft",
        "purpose": "search_indexing",
        "note": "Bing indexing crawler and an upstream signal for Microsoft search experiences.",
    },
    "PerplexityBot": {
        "provider": "Perplexity",
        "purpose": "search_discovery",
        "note": "Provider crawler reference; revalidate naming and policy before operational changes.",
    },
    "ClaudeBot": {
        "provider": "Anthropic",
        "purpose": "provider_crawl",
        "note": "Provider crawler reference; revalidate naming and policy before operational changes.",
    },
    "CCBot": {
        "provider": "Common Crawl",
        "purpose": "public_corpus_crawl",
        "note": "Public corpus crawler; access is a publishing-policy decision, not a universal GEO requirement.",
    },
}


class SurfaceParser(HTMLParser):
    def __init__(self, page_url: str):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.page_host = urllib.parse.urlsplit(page_url).hostname or ""
        self.title_parts: list[str] = []
        self.in_title = False
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.headings: list[dict[str, str]] = []
        self.heading_tag: str | None = None
        self.heading_parts: list[str] = []
        self.json_ld_raw: list[str] = []
        self.in_json_ld = False
        self.json_ld_parts: list[str] = []
        self.visible_parts: list[str] = []
        self.skip_depth = 0
        self.list_count = 0
        self.table_count = 0
        self.internal_links = 0
        self.external_links = 0
        self.images_total = 0
        self.images_without_alt = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        lower = tag.lower()
        if lower in {"script", "style", "noscript", "template"}:
            if lower == "script" and values.get("type", "").lower() == "application/ld+json":
                self.in_json_ld = True
                self.json_ld_parts = []
            else:
                self.skip_depth += 1
        elif lower == "title":
            self.in_title = True
        elif lower == "meta":
            key = values.get("name") or values.get("property") or values.get("http-equiv")
            content = values.get("content", "").strip()
            if key and content:
                self.meta[key.lower()] = content
        elif lower == "link" and "canonical" in values.get("rel", "").lower().split():
            self.canonical = urllib.parse.urljoin(self.page_url, values.get("href", ""))
        elif lower in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_tag = lower
            self.heading_parts = []
        elif lower in {"ul", "ol"}:
            self.list_count += 1
        elif lower == "table":
            self.table_count += 1
        elif lower == "a":
            href = values.get("href", "").strip()
            if href and not href.startswith(("#", "mailto:", "tel:", "javascript:")):
                absolute = urllib.parse.urljoin(self.page_url, href)
                host = urllib.parse.urlsplit(absolute).hostname or ""
                if host == self.page_host:
                    self.internal_links += 1
                elif host:
                    self.external_links += 1
        elif lower == "img":
            self.images_total += 1
            if "alt" not in values:
                self.images_without_alt += 1

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "script" and self.in_json_ld:
            self.in_json_ld = False
            self.json_ld_raw.append("".join(self.json_ld_parts).strip())
            self.json_ld_parts = []
        elif lower in {"script", "style", "noscript", "template"} and self.skip_depth:
            self.skip_depth -= 1
        elif lower == "title":
            self.in_title = False
        elif self.heading_tag == lower:
            self.headings.append({"level": lower, "text": " ".join("".join(self.heading_parts).split())})
            self.heading_tag = None
            self.heading_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_json_ld:
            self.json_ld_parts.append(data)
            return
        if self.in_title:
            self.title_parts.append(data)
        if self.heading_tag:
            self.heading_parts.append(data)
        if not self.skip_depth and not self.in_title:
            cleaned = " ".join(data.split())
            if cleaned:
                self.visible_parts.append(cleaned)


def _schema_types(value: Any) -> Iterable[str]:
    if isinstance(value, list):
        for item in value:
            yield from _schema_types(item)
    elif isinstance(value, dict):
        raw_type = value.get("@type")
        if isinstance(raw_type, str):
            yield raw_type
        elif isinstance(raw_type, list):
            for item in raw_type:
                if isinstance(item, str):
                    yield item
        if "@graph" in value:
            yield from _schema_types(value["@graph"])


def analyze_html(html: str, page_url: str) -> dict[str, Any]:
    parser = SurfaceParser(page_url)
    try:
        parser.feed(html)
    except Exception as exc:
        parse_error = str(exc)
    else:
        parse_error = ""

    decoded_json_ld: list[Any] = []
    invalid_json_ld = 0
    for block in parser.json_ld_raw:
        if not block:
            continue
        try:
            decoded_json_ld.append(json.loads(block))
        except json.JSONDecodeError:
            invalid_json_ld += 1
    types = sorted(set(item for block in decoded_json_ld for item in _schema_types(block)))
    text = " ".join(parser.visible_parts)
    words = text.split()
    levels = Counter(item["level"] for item in parser.headings)
    title = " ".join("".join(parser.title_parts).split())

    return {
        "page_url": page_url,
        "parse": evidence("observed", "rendered_html", "high", "page", not bool(parse_error), parse_error),
        "title": evidence("observed", "html_title", "high", "page", title),
        "meta_description": evidence("observed", "meta_tag", "high", "page", parser.meta.get("description", "")),
        "canonical": evidence("observed", "canonical_link", "high", "page", parser.canonical),
        "open_graph": evidence("observed", "meta_tags", "high", "page", {
            key: parser.meta.get(key, "") for key in ("og:title", "og:description", "og:image", "og:type")
        }),
        "headings": evidence("observed", "rendered_html", "high", "page", {
            "counts": dict(sorted(levels.items())),
            "items": parser.headings[:50],
        }),
        "visible_text": evidence("observed", "rendered_html", "medium", "page", {
            "word_count": len(words),
            "sample": text[:500],
        }, "Word count is a surface observation, not a ranking or citation predictor."),
        "structured_elements": evidence("observed", "rendered_html", "high", "page", {
            "lists": parser.list_count,
            "tables": parser.table_count,
            "internal_links": parser.internal_links,
            "external_links": parser.external_links,
            "images_total": parser.images_total,
            "images_without_alt_attribute": parser.images_without_alt,
        }),
        "json_ld": evidence("observed", "json_ld", "high", "page", {
            "blocks": len(parser.json_ld_raw),
            "valid_blocks": len(decoded_json_ld),
            "invalid_blocks": invalid_json_ld,
            "types": types,
        }, "Presence is observed. Correctness, eligibility and consistency with visible content require type-specific validation."),
    }


def analyze_robots_text(text: str, target_url: str) -> dict[str, Any]:
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(join_origin(target_url, "/robots.txt"))
    parser.parse(text.splitlines())
    crawlers: dict[str, Any] = {}
    for name, info in CRAWLERS.items():
        allowed = parser.can_fetch(name, target_url)
        crawlers[name] = {
            **info,
            "access": "allowed" if allowed else "blocked",
            "tested_url": target_url,
            "status": "observed",
            "source": "robots_txt",
            "confidence": "high",
        }
    return {
        "registry_verified_at": CRAWLER_REGISTRY_VERIFIED_AT,
        "registry_note": "Crawler names and policies are provider-controlled and must be revalidated before changing publishing policy.",
        "crawlers": crawlers,
    }


def measurement_source_status() -> dict[str, dict[str, str]]:
    return {
        "google_search_console": evidence(
            "not_measured", "first_party_console", "high", "property",
            None, "Preferred for Google Search and generative-AI performance when the property owner provides access or an export."
        ),
        "bing_ai_performance": evidence(
            "not_measured", "first_party_console", "high", "property",
            None, "Preferred for Bing citation and grounding-query observations when the property owner provides access or an export."
        ),
        "analytics": evidence(
            "not_measured", "first_party_analytics", "high", "site",
            None, "Required for conversion, funnel and referral conclusions; static HTML cannot measure user behavior."
        ),
        "assistant_experiments": evidence(
            "not_measured", "controlled_query_experiment", "medium", "query_set",
            None, "Run separately with model, mode, locale, date, clean-session protocol, repetitions, citations and variance recorded."
        ),
    }


def build_query_test_kit(brand: str, category: str, competitors: list[str], locale: str) -> dict[str, Any]:
    brand = brand.strip()
    category = category.strip()
    prompts = [
        f"What is {brand}?",
        f"What are credible options for {category}?",
        f"Which tools or providers are commonly cited for {category}?",
        f"How does {brand} work, and what evidence supports the description?",
        f"What are the limitations or trade-offs of {brand}?",
    ]
    for competitor in competitors[:5]:
        competitor = competitor.strip()
        if competitor:
            prompts.append(f"Compare {brand} with {competitor} for {category}. Cite sources.")
    return {
        "methodology": evidence(
            "not_measured", "generated_test_protocol", "medium", "query_set", None,
            "This is a test kit, not observed assistant visibility. Use clean sessions, record model/mode/date/locale, repeat prompts, capture cited URLs and report variance."
        ),
        "locale": locale,
        "brand": brand,
        "category": category,
        "competitors": [item for item in competitors if item.strip()],
        "prompts": prompts,
        "fields_to_record": [
            "assistant", "model_or_mode", "date", "locale", "clean_session", "repeat_number",
            "brand_mentioned", "cited_urls", "position_description", "claim_accuracy",
            "competitors_mentioned", "notes",
        ],
    }


def _recommendations(page: dict[str, Any], robots: dict[str, Any], page_fetch: dict[str, Any]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    if not page_fetch.get("transport_verified", False):
        recommendations.append({
            "priority": "critical", "category": "transport", "status": "observed",
            "evidence": page_fetch.get("error_type") or "unverified transport",
            "recommendation": "Fix certificate validation or transport before trusting content collected from this origin.",
            "expected_measurement": "Repeat the verified fetch and record a successful TLS handshake.",
        })
    if not page["title"]["value"]:
        recommendations.append({
            "priority": "high", "category": "page_identity", "status": "observed",
            "evidence": "Missing HTML title",
            "recommendation": "Add a page-specific title that identifies the entity and user intent.",
            "expected_measurement": "Re-fetch the page and verify the title in rendered HTML and Search Console indexing data.",
        })
    if not page["meta_description"]["value"]:
        recommendations.append({
            "priority": "medium", "category": "page_identity", "status": "observed",
            "evidence": "Missing meta description",
            "recommendation": "Add an accurate page-specific description. Treat snippet selection as search-engine controlled.",
            "expected_measurement": "Verify the tag and monitor actual snippets separately.",
        })
    if page["json_ld"]["value"]["invalid_blocks"]:
        recommendations.append({
            "priority": "high", "category": "structured_data", "status": "observed",
            "evidence": f"{page['json_ld']['value']['invalid_blocks']} invalid JSON-LD block(s)",
            "recommendation": "Repair invalid JSON-LD and validate that marked-up claims match visible content.",
            "expected_measurement": "Run type-specific structured-data validation after the fix.",
        })
    blocked_search = [name for name, item in robots.get("crawlers", {}).items()
                      if item.get("access") == "blocked" and item.get("purpose") in {"search_discovery", "search_indexing"}]
    if blocked_search:
        recommendations.append({
            "priority": "high", "category": "crawler_policy", "status": "observed",
            "evidence": {"blocked_search_or_discovery_crawlers": blocked_search},
            "recommendation": "Review whether the robots policy matches the publisher's intended search/discovery policy. Do not change it automatically.",
            "expected_measurement": "After owner approval, re-test robots rules and monitor first-party search/citation reports.",
        })
    return recommendations


def run_audit(url: str, brand: str, category: str, competitors: list[str], locale: str,
              allow_private: bool = False, timeout: float = 15.0) -> dict[str, Any]:
    target = validate_public_url(url, allow_private=allow_private)
    page_fetch = fetch_text(target, timeout=timeout, allow_private=allow_private)
    robots_fetch = fetch_text(join_origin(target, "/robots.txt"), timeout=timeout, allow_private=allow_private)
    sitemap_fetch = fetch_text(join_origin(target, "/sitemap.xml"), timeout=timeout, allow_private=allow_private)

    if page_fetch.body:
        page = analyze_html(page_fetch.body, page_fetch.final_url or target)
    else:
        page = {"status": evidence("not_measured", "rendered_html", "low", "page", None,
                                   "Page body was unavailable; HTML signals were not analyzed.")}
    if robots_fetch.status == 200 and robots_fetch.body:
        robots = analyze_robots_text(robots_fetch.body, page_fetch.final_url or target)
        robots["fetch"] = robots_fetch.to_dict()
    else:
        robots = {
            "fetch": robots_fetch.to_dict(),
            "registry_verified_at": CRAWLER_REGISTRY_VERIFIED_AT,
            "crawlers": {name: {**info, "access": "unknown", "status": "not_measured", "confidence": "low"}
                         for name, info in CRAWLERS.items()},
            "note": "robots.txt could not be retrieved successfully. Access is unknown; do not infer allowed or blocked.",
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "methodology": {
            "fetched_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "claim": "readiness and observable evidence audit",
            "does_not_measure": [
                "assistant ranking", "citation probability", "share of voice", "conversion rate",
                "Google or Bing field performance without first-party exports", "Core Web Vitals",
            ],
            "evidence_statuses": ["observed", "measured", "inferred", "not_measured"],
        },
        "target": target,
        "transport": page_fetch.to_dict(),
        "robots": robots,
        "sitemap": evidence(
            "observed" if sitemap_fetch.status is not None else "not_measured",
            "http_fetch", "high" if sitemap_fetch.transport_verified else "low", "site",
            {"status": sitemap_fetch.status, "final_url": sitemap_fetch.final_url, "truncated": sitemap_fetch.truncated},
            sitemap_fetch.error or "",
        ),
        "page_surface": page,
        "measurement_sources": measurement_source_status(),
        "query_test_kit": build_query_test_kit(brand, category, competitors, locale),
        "recommendations": _recommendations(page, robots, page_fetch.to_dict()) if "title" in page else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect evidence for search and AI-discovery readiness without inventing a GEO score.")
    parser.add_argument("url")
    parser.add_argument("--brand", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--competitors", default="")
    parser.add_argument("--locale", default="pt-BR")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--allow-private", action="store_true", help="Explicitly allow private/internal targets. Disabled by default to prevent SSRF.")
    args = parser.parse_args()
    try:
        report = run_audit(
            args.url, args.brand, args.category,
            [item.strip() for item in args.competitors.split(",") if item.strip()],
            args.locale, args.allow_private, args.timeout,
        )
    except ValueError as exc:
        json.dump({"schema_version": SCHEMA_VERSION, "error": str(exc), "status": "not_measured"}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
