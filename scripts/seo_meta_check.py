#!/usr/bin/env python3
"""
SEO Meta Tag Checker for CRO/GEO Analysis.
Extracts and evaluates meta tags, Open Graph, Schema.org JSON-LD from a list of URLs.
Usage: python seo_meta_check.py <url1> [url2] [url3] ...
Output: JSON report to stdout.
"""

import sys
import json
import requests
from bs4 import BeautifulSoup

def analyze_page(url: str) -> dict:
    """Extract and evaluate SEO meta data from a single page."""
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; CROAuditBot/1.0)"
        })
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        return {"url": url, "error": str(e)}

    result = {"url": url, "status_code": resp.status_code}

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    result["title"] = {
        "value": title,
        "length": len(title),
        "ok": 30 <= len(title) <= 65,
        "issue": "" if 30 <= len(title) <= 65 else (
            "Muito curto (< 30 chars)" if len(title) < 30 else "Muito longo (> 65 chars)"
        ),
    }

    # Meta description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc = desc_tag.get("content", "") if desc_tag else ""
    result["meta_description"] = {
        "value": desc,
        "length": len(desc),
        "ok": 120 <= len(desc) <= 160,
        "issue": "" if 120 <= len(desc) <= 160 else (
            "Ausente ou muito curta" if len(desc) < 120 else "Muito longa (> 160 chars)"
        ),
    }

    # Canonical
    canonical = soup.find("link", rel="canonical")
    result["canonical"] = {
        "value": canonical.get("href", "") if canonical else "",
        "present": canonical is not None,
    }

    # Viewport
    viewport = soup.find("meta", attrs={"name": "viewport"})
    result["viewport"] = {"present": viewport is not None}

    # Open Graph
    og_tags = {}
    for tag in soup.find_all("meta", attrs={"property": lambda x: x and x.startswith("og:")}):
        og_tags[tag.get("property")] = tag.get("content", "")
    required_og = ["og:title", "og:description", "og:image", "og:url", "og:type"]
    result["open_graph"] = {
        "tags": og_tags,
        "present_count": len(og_tags),
        "missing": [t for t in required_og if t not in og_tags],
        "ok": all(t in og_tags for t in required_og),
    }

    # Twitter Card
    tw_tags = {}
    for tag in soup.find_all("meta", attrs={"name": lambda x: x and x.startswith("twitter:")}):
        tw_tags[tag.get("name")] = tag.get("content", "")
    result["twitter_card"] = {
        "tags": tw_tags,
        "present": len(tw_tags) > 0,
    }

    # Headings hierarchy
    headings = {}
    for level in range(1, 7):
        tags = soup.find_all(f"h{level}")
        if tags:
            headings[f"h{level}"] = [t.get_text(strip=True)[:80] for t in tags[:5]]
    result["headings"] = {
        "structure": headings,
        "has_h1": "h1" in headings,
        "h1_count": len(headings.get("h1", [])),
        "ok": "h1" in headings and len(headings.get("h1", [])) == 1,
    }

    # Schema.org JSON-LD
    schemas = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                schemas.extend(data)
            else:
                schemas.append(data)
        except (json.JSONDecodeError, TypeError):
            pass
    result["schema_jsonld"] = {
        "count": len(schemas),
        "types": [s.get("@type", "Unknown") for s in schemas],
        "present": len(schemas) > 0,
    }

    # Images without alt
    images = soup.find_all("img")
    no_alt = [img.get("src", "")[:60] for img in images if not img.get("alt")]
    result["images"] = {
        "total": len(images),
        "missing_alt": len(no_alt),
        "examples_missing_alt": no_alt[:5],
    }

    # Internal links
    links = soup.find_all("a", href=True)
    result["links"] = {
        "total": len(links),
        "internal": sum(1 for l in links if l["href"].startswith("/") or url.split("/")[2] in l["href"]),
        "external": sum(1 for l in links if l["href"].startswith("http") and url.split("/")[2] not in l["href"]),
    }

    # Calculate SEO score
    score = 0
    if result["title"]["ok"]: score += 15
    elif result["title"]["value"]: score += 8
    if result["meta_description"]["ok"]: score += 15
    elif result["meta_description"]["value"]: score += 8
    if result["canonical"]["present"]: score += 10
    if result["viewport"]["present"]: score += 5
    if result["open_graph"]["ok"]: score += 15
    elif result["open_graph"]["present_count"] > 0: score += 8
    if result["headings"]["ok"]: score += 15
    elif result["headings"]["has_h1"]: score += 8
    if result["schema_jsonld"]["present"]: score += 15
    if result["images"]["missing_alt"] == 0: score += 10
    elif result["images"]["missing_alt"] < 3: score += 5

    result["seo_score"] = score
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python seo_meta_check.py <url1> [url2] [url3] ...")
        sys.exit(1)

    urls = sys.argv[1:]
    results = [analyze_page(url) for url in urls]

    avg_score = sum(r.get("seo_score", 0) for r in results) / len(results) if results else 0

    report = {
        "pages_analyzed": len(results),
        "average_seo_score": round(avg_score),
        "results": results,
    }

    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
