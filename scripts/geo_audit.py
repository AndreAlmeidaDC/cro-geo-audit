#!/usr/bin/env python3
"""
GEO Audit Script — Generative Engine Optimization Analysis
Performs a comprehensive, autonomous GEO audit of any website.

Usage:
    python geo_audit.py https://example.com [--brand "Brand Name"] [--competitors "comp1,comp2"]

Output: JSON to stdout with all GEO metrics and scores.
"""

import sys
import json
import re
import ssl
import socket
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from html.parser import HTMLParser

# ─────────────────────────────────────────────────────────
# 1. AI CRAWLER ANALYSIS (robots.txt)
# ─────────────────────────────────────────────────────────

AI_CRAWLERS = {
    "GPTBot": {"engine": "ChatGPT / OpenAI", "critical": True},
    "ChatGPT-User": {"engine": "ChatGPT Browse", "critical": True},
    "Google-Extended": {"engine": "Gemini / Google AI", "critical": True},
    "Googlebot": {"engine": "Google Search + AI Overviews", "critical": True},
    "Bingbot": {"engine": "Bing / Copilot", "critical": True},
    "anthropic-ai": {"engine": "Claude / Anthropic", "critical": False},
    "ClaudeBot": {"engine": "Claude Web", "critical": False},
    "PerplexityBot": {"engine": "Perplexity AI", "critical": False},
    "Bytespider": {"engine": "TikTok / ByteDance AI", "critical": False},
    "CCBot": {"engine": "Common Crawl (training data)", "critical": False},
    "FacebookBot": {"engine": "Meta AI", "critical": False},
    "cohere-ai": {"engine": "Cohere", "critical": False},
}


def fetch_url(url, timeout=15):
    """Fetch URL content with proper error handling."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; GEOAuditBot/1.0)"
        })
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read().decode("utf-8", errors="replace"), resp.status
    except urllib.error.HTTPError as e:
        return "", e.code
    except Exception as e:
        return "", str(e)


def analyze_robots_txt(base_url):
    """Analyze robots.txt for AI crawler blocking status."""
    robots_url = base_url.rstrip("/") + "/robots.txt"
    content, status = fetch_url(robots_url)

    results = {
        "robots_url": robots_url,
        "status": status,
        "exists": status == 200,
        "raw_content": content[:3000] if content else "",
        "crawlers": {},
        "blocked_count": 0,
        "allowed_count": 0,
        "critical_blocked": 0,
        "total_checked": len(AI_CRAWLERS),
    }

    if not content:
        # No robots.txt = all allowed
        for name, info in AI_CRAWLERS.items():
            results["crawlers"][name] = {
                "engine": info["engine"],
                "critical": info["critical"],
                "status": "allowed",
                "reason": "No robots.txt found"
            }
            results["allowed_count"] += 1
        return results

    # Parse robots.txt
    lines = content.lower().split("\n")
    current_agents = []
    rules = {}  # agent -> list of (allow/disallow, path)

    for line in lines:
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        if line.startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip()
            current_agents = [agent]
            if agent not in rules:
                rules[agent] = []
        elif line.startswith("disallow:") and current_agents:
            path = line.split(":", 1)[1].strip()
            for agent in current_agents:
                if agent not in rules:
                    rules[agent] = []
                rules[agent].append(("disallow", path))
        elif line.startswith("allow:") and current_agents:
            path = line.split(":", 1)[1].strip()
            for agent in current_agents:
                if agent not in rules:
                    rules[agent] = []
                rules[agent].append(("allow", path))

    for name, info in AI_CRAWLERS.items():
        name_lower = name.lower()
        blocked = False
        partially_restricted = False
        reason = "No specific rule found (default: allowed)"

        # Check specific agent rules first
        if name_lower in rules:
            agent_rules = rules[name_lower]
            has_allow_root = any(a == "allow" and p == "/" for a, p in agent_rules)
            has_disallow_root = any(a == "disallow" and p == "/" for a, p in agent_rules)
            has_specific_disallows = any(a == "disallow" and p not in ("/", "") and p for a, p in agent_rules)

            if has_disallow_root and not has_allow_root:
                blocked = True
                reason = f"Disallow: / for User-agent: {name}"
            elif has_allow_root and has_specific_disallows:
                # Allow: / with specific Disallows (e.g., /dashboard) = allowed with restrictions
                restricted_paths = [p for a, p in agent_rules if a == "disallow" and p not in ("/", "")]
                partially_restricted = True
                reason = f"Allow: / with restricted paths: {', '.join(restricted_paths)}"
            elif has_allow_root:
                reason = f"Explicitly allowed via Allow: / for User-agent: {name}"

        # Check wildcard rules only if no specific rules found
        if not blocked and name_lower not in rules and "*" in rules:
            wildcard_rules = rules["*"]
            has_allow_root_w = any(a == "allow" and p == "/" for a, p in wildcard_rules)
            has_disallow_root_w = any(a == "disallow" and p == "/" for a, p in wildcard_rules)
            has_specific_disallows_w = any(a == "disallow" and p not in ("/", "") and p for a, p in wildcard_rules)

            if has_disallow_root_w and not has_allow_root_w:
                blocked = True
                reason = "Disallow: / for User-agent: *"
            elif has_allow_root_w and has_specific_disallows_w:
                restricted_paths = [p for a, p in wildcard_rules if a == "disallow" and p not in ("/", "")]
                partially_restricted = True
                reason = f"Allow: / via wildcard with restricted paths: {', '.join(restricted_paths)}"

        status_str = "blocked" if blocked else ("allowed_restricted" if partially_restricted else "allowed")
        results["crawlers"][name] = {
            "engine": info["engine"],
            "critical": info["critical"],
            "status": status_str,
            "reason": reason
        }

        if blocked:
            results["blocked_count"] += 1
            if info["critical"]:
                results["critical_blocked"] += 1
        else:
            results["allowed_count"] += 1
            if partially_restricted:
                results.setdefault("restricted_count", 0)
                results["restricted_count"] += 1

    return results


# ─────────────────────────────────────────────────────────
# 2. SCHEMA.ORG / STRUCTURED DATA ANALYSIS
# ─────────────────────────────────────────────────────────

class SchemaExtractor(HTMLParser):
    """Extract JSON-LD and meta tags from HTML."""
    def __init__(self):
        super().__init__()
        self.json_ld_blocks = []
        self.meta_tags = {}
        self.in_script = False
        self.script_type = ""
        self.script_content = ""
        self.title = ""
        self.in_title = False
        self.faq_sections = 0
        self.stat_patterns = 0
        self.citation_patterns = 0
        self.heading_counts = {"h1": 0, "h2": 0, "h3": 0, "h4": 0}
        self.word_count = 0
        self.current_text = ""
        self.list_count = 0
        self.table_count = 0
        self.internal_links = 0
        self.external_links = 0
        self.base_domain = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "script" and attrs_dict.get("type") == "application/ld+json":
            self.in_script = True
            self.script_content = ""
        elif tag == "meta":
            name = attrs_dict.get("name", attrs_dict.get("property", ""))
            content = attrs_dict.get("content", "")
            if name and content:
                self.meta_tags[name] = content
        elif tag == "title":
            self.in_title = True
        elif tag in self.heading_counts:
            self.heading_counts[tag] += 1
        elif tag in ("ul", "ol"):
            self.list_count += 1
        elif tag == "table":
            self.table_count += 1
        elif tag == "a":
            href = attrs_dict.get("href", "")
            if href.startswith("http") and self.base_domain not in href:
                self.external_links += 1
            elif href.startswith("/") or (href.startswith("http") and self.base_domain in href):
                self.internal_links += 1

    def handle_endtag(self, tag):
        if tag == "script" and self.in_script:
            self.in_script = False
            try:
                data = json.loads(self.script_content)
                self.json_ld_blocks.append(data)
            except json.JSONDecodeError:
                pass
        elif tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_script:
            self.script_content += data
        elif self.in_title:
            self.title += data.strip()
        else:
            self.current_text += data + " "
            # Count FAQ patterns
            lower = data.lower()
            if any(q in lower for q in ["perguntas frequentes", "faq", "frequently asked"]):
                self.faq_sections += 1
            # Count statistical patterns (numbers with %)
            self.stat_patterns += len(re.findall(r'\d+[.,]?\d*\s*%', data))
            # Count citation patterns
            if any(c in lower for c in ["segundo ", "de acordo com ", "fonte:", "source:", "according to"]):
                self.citation_patterns += 1


def analyze_structured_data(base_url, html_content):
    """Analyze Schema.org, JSON-LD, and content citability."""
    domain = urllib.parse.urlparse(base_url).netloc

    parser = SchemaExtractor()
    parser.base_domain = domain
    try:
        parser.feed(html_content)
    except Exception:
        pass

    # Analyze JSON-LD quality
    schema_types = []
    has_org = False
    has_product = False
    has_faq = False
    has_howto = False
    has_article = False
    has_breadcrumb = False
    has_website = False
    has_local_business = False

    for block in parser.json_ld_blocks:
        blocks_to_check = [block] if not isinstance(block, list) else block
        for item in blocks_to_check:
            if isinstance(item, dict):
                stype = item.get("@type", "")
                if isinstance(stype, list):
                    schema_types.extend(stype)
                else:
                    schema_types.append(stype)
                if stype in ("Organization", "Corporation"):
                    has_org = True
                elif stype in ("Product", "SoftwareApplication"):
                    has_product = True
                elif stype == "FAQPage":
                    has_faq = True
                elif stype == "HowTo":
                    has_howto = True
                elif stype in ("Article", "BlogPosting", "NewsArticle"):
                    has_article = True
                elif stype == "BreadcrumbList":
                    has_breadcrumb = True
                elif stype == "WebSite":
                    has_website = True
                elif stype == "LocalBusiness":
                    has_local_business = True

    # Word count
    words = parser.current_text.split()
    word_count = len(words)

    # Citability analysis
    citability = {
        "has_faq_content": parser.faq_sections > 0 or has_faq,
        "has_statistics_with_numbers": parser.stat_patterns > 2,
        "has_citations_or_sources": parser.citation_patterns > 0,
        "has_structured_lists": parser.list_count > 2,
        "has_data_tables": parser.table_count > 0,
        "has_clear_heading_hierarchy": parser.heading_counts["h1"] == 1 and parser.heading_counts["h2"] >= 2,
        "word_count": word_count,
        "content_depth": "deep" if word_count > 1500 else "moderate" if word_count > 500 else "thin",
        "stat_count": parser.stat_patterns,
        "citation_count": parser.citation_patterns,
        "list_count": parser.list_count,
        "table_count": parser.table_count,
    }

    return {
        "json_ld_count": len(parser.json_ld_blocks),
        "schema_types": list(set(schema_types)),
        "has_organization": has_org,
        "has_product": has_product,
        "has_faq_schema": has_faq,
        "has_howto_schema": has_howto,
        "has_article_schema": has_article,
        "has_breadcrumb": has_breadcrumb,
        "has_website_schema": has_website,
        "has_local_business": has_local_business,
        "meta_tags": {
            "title": parser.title,
            "description": parser.meta_tags.get("description", ""),
            "og_title": parser.meta_tags.get("og:title", ""),
            "og_description": parser.meta_tags.get("og:description", ""),
            "og_image": parser.meta_tags.get("og:image", ""),
            "og_type": parser.meta_tags.get("og:type", ""),
        },
        "citability": citability,
        "content_stats": {
            "headings": parser.heading_counts,
            "internal_links": parser.internal_links,
            "external_links": parser.external_links,
            "word_count": word_count,
        }
    }


# ─────────────────────────────────────────────────────────
# 3. DIRECTORY PRESENCE CHECK
# ─────────────────────────────────────────────────────────

DIRECTORIES = [
    {"name": "Google Business", "check_url": None, "type": "search"},
    {"name": "Product Hunt", "check_url": "https://www.producthunt.com/search?q={brand}", "type": "startup"},
    {"name": "G2", "check_url": "https://www.g2.com/search?query={brand}", "type": "b2b"},
    {"name": "Capterra", "check_url": "https://www.capterra.com/search/?query={brand}", "type": "b2b"},
    {"name": "Crunchbase", "check_url": "https://www.crunchbase.com/textsearch?q={brand}", "type": "startup"},
    {"name": "LinkedIn Company", "check_url": "https://www.linkedin.com/search/results/companies/?keywords={brand}", "type": "professional"},
    {"name": "GitHub", "check_url": "https://github.com/search?q={brand}&type=repositories", "type": "developer"},
    {"name": "Wikipedia", "check_url": "https://pt.wikipedia.org/wiki/{brand}", "type": "authority"},
    {"name": "Reclame Aqui", "check_url": "https://www.reclameaqui.com.br/busca/?q={brand}", "type": "reputation_br"},
    {"name": "Trustpilot", "check_url": "https://www.trustpilot.com/search?query={brand}", "type": "reputation"},
]


def check_google_presence(brand, domain):
    """Check brand presence in Google search results."""
    query = urllib.parse.quote(f'"{brand}" OR site:{domain}')
    url = f"https://www.google.com/search?q={query}&num=10"
    content, status = fetch_url(url)

    results_estimate = 0
    if content:
        # Try to find result count
        match = re.search(r'About ([\d,]+) results', content)
        if match:
            results_estimate = int(match.group(1).replace(",", ""))
        elif "did not match any documents" in content.lower():
            results_estimate = 0
        else:
            # Count result links as rough estimate
            results_estimate = content.lower().count('<div class="g">')

    return {
        "google_results_estimate": results_estimate,
        "has_google_presence": results_estimate > 0,
    }


def build_directory_checklist(brand):
    """Build a checklist of directories to verify (URLs for manual/browser check)."""
    checklist = []
    encoded_brand = urllib.parse.quote(brand)
    for d in DIRECTORIES:
        entry = {
            "name": d["name"],
            "type": d["type"],
            "check_url": d["check_url"].format(brand=encoded_brand) if d["check_url"] else None,
            "status": "needs_verification",
            "note": "Use browser to verify presence"
        }
        checklist.append(entry)
    return checklist


# ─────────────────────────────────────────────────────────
# 4. AI VISIBILITY TEST PROMPTS
# ─────────────────────────────────────────────────────────

def generate_test_prompts(brand, domain, industry="auditoria de contas de consumo"):
    """Generate prompts to test in ChatGPT, Gemini, and Perplexity."""
    prompts = [
        f"O que é {brand}?",
        f"Quais são as melhores ferramentas para auditar contas de água no Brasil?",
        f"Como saber se estou pagando a mais na conta de água?",
        f"Existe algum serviço que analisa faturas de água e identifica cobranças indevidas?",
        f"Quais empresas fazem análise de contas de consumo no Brasil?",
        f"Como contestar uma conta de água da SABESP?",
        f"Ferramentas de IA para análise de faturas de serviços públicos",
        f"Como funciona a auditoria de contas de água?",
        f"Melhores sites para verificar erros na conta de água",
        f"O que é {brand} e como funciona?",
        f"Comparação de serviços de auditoria de contas de consumo",
        f"Como economizar na conta de água em São Paulo?",
        f"Startups brasileiras de análise de contas de consumo",
        f"Tecnologia para identificar cobranças indevidas em faturas",
        f"Revisão de contas de água e esgoto automática",
    ]

    return {
        "total_prompts": len(prompts),
        "prompts": prompts,
        "engines_to_test": [
            {"name": "ChatGPT", "url": "https://chat.openai.com"},
            {"name": "Gemini", "url": "https://gemini.google.com"},
            {"name": "Perplexity", "url": "https://www.perplexity.ai"},
            {"name": "Copilot", "url": "https://copilot.microsoft.com"},
        ],
        "instructions": (
            "For each prompt, test in each AI engine and record: "
            "1) Does the brand appear? (yes/no) "
            "2) Is it mentioned or cited with link? "
            "3) What position in the response? (1st paragraph, middle, end, not present) "
            "4) Sentiment (positive, neutral, negative) "
            "5) Competitors mentioned alongside"
        )
    }


# ─────────────────────────────────────────────────────────
# 5. GEO SCORING ENGINE
# ─────────────────────────────────────────────────────────

def calculate_geo_score(robots_data, schema_data, google_data, additional_pages_data=None):
    """Calculate comprehensive GEO score based on all collected data."""

    scores = {}

    # --- A. AI Crawler Accessibility (25 points max) ---
    crawler_score = 25
    if robots_data["blocked_count"] > 0:
        # Deduct 3 points per critical crawler blocked, 1.5 per non-critical
        for name, info in robots_data["crawlers"].items():
            if info["status"] == "blocked":
                if info["critical"]:
                    crawler_score -= 5
                else:
                    crawler_score -= 2
    crawler_score = max(0, crawler_score)
    scores["ai_crawler_accessibility"] = {
        "score": round(crawler_score),
        "max": 25,
        "details": f"{robots_data['allowed_count']}/{robots_data['total_checked']} crawlers allowed, {robots_data['critical_blocked']} critical blocked"
    }

    # --- B. Structured Data Quality (20 points max) ---
    sd_score = 0
    if schema_data["json_ld_count"] > 0:
        sd_score += 4  # Has any JSON-LD
    if schema_data["has_organization"]:
        sd_score += 4  # Organization schema
    if schema_data["has_product"]:
        sd_score += 3  # Product/SoftwareApplication
    if schema_data["has_faq_schema"]:
        sd_score += 3  # FAQ schema (highly valued by AI)
    if schema_data["has_breadcrumb"]:
        sd_score += 2  # Breadcrumb
    if schema_data["has_website_schema"]:
        sd_score += 2  # WebSite
    if schema_data["has_article_schema"]:
        sd_score += 2  # Article/BlogPosting
    sd_score = min(20, sd_score)
    scores["structured_data_quality"] = {
        "score": sd_score,
        "max": 20,
        "details": f"{schema_data['json_ld_count']} JSON-LD blocks, types: {', '.join(schema_data['schema_types']) or 'none'}"
    }

    # --- C. Content Citability (20 points max) ---
    cit = schema_data["citability"]
    cit_score = 0
    if cit["has_faq_content"]:
        cit_score += 4
    if cit["has_statistics_with_numbers"]:
        cit_score += 3
    if cit["has_citations_or_sources"]:
        cit_score += 3
    if cit["has_structured_lists"]:
        cit_score += 3
    if cit["has_data_tables"]:
        cit_score += 2
    if cit["has_clear_heading_hierarchy"]:
        cit_score += 3
    if cit["content_depth"] == "deep":
        cit_score += 2
    elif cit["content_depth"] == "moderate":
        cit_score += 1
    cit_score = min(20, cit_score)
    scores["content_citability"] = {
        "score": cit_score,
        "max": 20,
        "details": f"Word count: {cit['word_count']}, Stats: {cit['stat_count']}, Citations: {cit['citation_count']}, Lists: {cit['list_count']}, Tables: {cit['table_count']}"
    }

    # --- D. Meta & OG Completeness (15 points max) ---
    meta = schema_data["meta_tags"]
    meta_score = 0
    if meta["title"]:
        meta_score += 3
    if meta["description"]:
        meta_score += 3
    if meta["og_title"]:
        meta_score += 2
    if meta["og_description"]:
        meta_score += 2
    if meta["og_image"]:
        meta_score += 3
    if meta["og_type"]:
        meta_score += 2
    meta_score = min(15, meta_score)
    scores["meta_completeness"] = {
        "score": meta_score,
        "max": 15,
        "details": f"Title: {'yes' if meta['title'] else 'no'}, Desc: {'yes' if meta['description'] else 'no'}, OG: {sum(1 for v in [meta['og_title'], meta['og_description'], meta['og_image'], meta['og_type']] if v)}/4"
    }

    # --- E. Content Architecture (10 points max) ---
    cs = schema_data["content_stats"]
    arch_score = 0
    if cs["headings"]["h1"] == 1:
        arch_score += 3
    if cs["headings"]["h2"] >= 3:
        arch_score += 2
    if cs["internal_links"] >= 5:
        arch_score += 2
    if cs["external_links"] >= 1:
        arch_score += 1
    if cs["word_count"] >= 300:
        arch_score += 2
    arch_score = min(10, arch_score)
    scores["content_architecture"] = {
        "score": arch_score,
        "max": 10,
        "details": f"H1: {cs['headings']['h1']}, H2: {cs['headings']['h2']}, Internal links: {cs['internal_links']}, External: {cs['external_links']}"
    }

    # --- F. External Authority Signals (10 points max) ---
    auth_score = 0
    if google_data.get("has_google_presence"):
        auth_score += 5
        est = google_data.get("google_results_estimate", 0)
        if est > 1000:
            auth_score += 5
        elif est > 100:
            auth_score += 3
        elif est > 10:
            auth_score += 1
    auth_score = min(10, auth_score)
    scores["external_authority"] = {
        "score": auth_score,
        "max": 10,
        "details": f"Google results estimate: {google_data.get('google_results_estimate', 'N/A')}"
    }

    # --- Calculate total ---
    total_score = sum(s["score"] for s in scores.values())
    total_max = sum(s["max"] for s in scores.values())
    percentage = round((total_score / total_max) * 100) if total_max > 0 else 0

    # --- Grade ---
    if percentage >= 80:
        grade = "A"
        verdict = "Excelente visibilidade em IA"
    elif percentage >= 60:
        grade = "B"
        verdict = "Boa visibilidade, com espaço para melhorias"
    elif percentage >= 40:
        grade = "C"
        verdict = "Visibilidade moderada, precisa de atenção"
    elif percentage >= 20:
        grade = "D"
        verdict = "Visibilidade fraca, ações urgentes necessárias"
    else:
        grade = "F"
        verdict = "Praticamente invisível para IAs"

    return {
        "total_score": total_score,
        "total_max": total_max,
        "percentage": percentage,
        "grade": grade,
        "verdict": verdict,
        "categories": scores,
    }


# ─────────────────────────────────────────────────────────
# 6. RECOMMENDATIONS ENGINE
# ─────────────────────────────────────────────────────────

def generate_recommendations(robots_data, schema_data, geo_score):
    """Generate prioritized recommendations based on audit findings."""
    recs = []

    # Critical: Blocked AI crawlers
    if robots_data["critical_blocked"] > 0:
        blocked_names = [n for n, v in robots_data["crawlers"].items() if v["status"] == "blocked" and v["critical"]]
        recs.append({
            "priority": "critical",
            "category": "AI Crawler Access",
            "title": "Liberar crawlers de IA críticos no robots.txt",
            "description": f"Os seguintes crawlers críticos estão bloqueados: {', '.join(blocked_names)}. Isso torna o site invisível para as principais IAs.",
            "impact": "alto",
            "effort": "baixo",
            "action": "Editar robots.txt e remover as regras de Disallow para esses User-agents."
        })

    if robots_data["blocked_count"] > robots_data["critical_blocked"]:
        blocked_names = [n for n, v in robots_data["crawlers"].items() if v["status"] == "blocked" and not v["critical"]]
        recs.append({
            "priority": "high",
            "category": "AI Crawler Access",
            "title": "Liberar crawlers de IA secundários",
            "description": f"Crawlers secundários bloqueados: {', '.join(blocked_names)}.",
            "impact": "médio",
            "effort": "baixo",
            "action": "Remover regras de bloqueio no robots.txt."
        })

    # Schema.org
    if not schema_data["has_organization"]:
        recs.append({
            "priority": "high",
            "category": "Structured Data",
            "title": "Adicionar Schema Organization",
            "description": "Sem Schema Organization, as IAs não conseguem identificar claramente quem é a empresa.",
            "impact": "alto",
            "effort": "baixo",
            "action": "Adicionar JSON-LD com @type Organization incluindo name, url, logo, description, contactPoint."
        })

    if not schema_data["has_faq_schema"]:
        recs.append({
            "priority": "high",
            "category": "Structured Data",
            "title": "Adicionar Schema FAQPage",
            "description": "FAQ estruturado é um dos formatos mais citados por IAs generativas.",
            "impact": "alto",
            "effort": "médio",
            "action": "Criar uma seção de FAQ no site e marcar com JSON-LD @type FAQPage."
        })

    if not schema_data["has_product"]:
        recs.append({
            "priority": "medium",
            "category": "Structured Data",
            "title": "Adicionar Schema Product/SoftwareApplication",
            "description": "Ajuda IAs a entenderem o que o produto faz, preço e avaliações.",
            "impact": "médio",
            "effort": "médio",
            "action": "Adicionar JSON-LD com @type SoftwareApplication ou Product na página de produtos."
        })

    if not schema_data["has_breadcrumb"]:
        recs.append({
            "priority": "low",
            "category": "Structured Data",
            "title": "Adicionar Schema BreadcrumbList",
            "description": "Melhora a navegação semântica para crawlers.",
            "impact": "baixo",
            "effort": "baixo",
            "action": "Adicionar JSON-LD BreadcrumbList em todas as páginas."
        })

    # Content citability
    cit = schema_data["citability"]
    if not cit["has_faq_content"]:
        recs.append({
            "priority": "high",
            "category": "Content Citability",
            "title": "Criar conteúdo em formato FAQ",
            "description": "IAs generativas adoram citar conteúdo em formato pergunta-resposta.",
            "impact": "alto",
            "effort": "médio",
            "action": "Adicionar seção FAQ na homepage e criar artigos no blog em formato Q&A."
        })

    if not cit["has_statistics_with_numbers"]:
        recs.append({
            "priority": "medium",
            "category": "Content Citability",
            "title": "Incluir estatísticas e dados numéricos",
            "description": "Conteúdo com dados específicos (%, R$, números) é mais citado por IAs.",
            "impact": "médio",
            "effort": "médio",
            "action": "Adicionar estatísticas reais: '87% das contas analisadas tinham erros', 'economia média de R$ 340/ano'."
        })

    if cit["content_depth"] == "thin":
        recs.append({
            "priority": "high",
            "category": "Content Citability",
            "title": "Aumentar profundidade do conteúdo",
            "description": f"O conteúdo principal tem apenas {cit['word_count']} palavras. IAs preferem conteúdo denso e detalhado.",
            "impact": "alto",
            "effort": "alto",
            "action": "Expandir o conteúdo da homepage e criar páginas de conteúdo aprofundado (guias, tutoriais)."
        })

    # Meta tags
    meta = schema_data["meta_tags"]
    if not meta["og_image"]:
        recs.append({
            "priority": "medium",
            "category": "Meta Tags",
            "title": "Adicionar og:image",
            "description": "Sem og:image, compartilhamentos em redes sociais e citações ficam sem visual.",
            "impact": "médio",
            "effort": "baixo",
            "action": "Adicionar meta tag og:image com URL de uma imagem representativa (1200x630px)."
        })

    # External authority
    recs.append({
        "priority": "medium",
        "category": "External Authority",
        "title": "Cadastrar em diretórios B2B e de startups",
        "description": "Presença em diretórios como Product Hunt, G2, Capterra aumenta a autoridade percebida pelas IAs.",
        "impact": "alto",
        "effort": "médio",
        "action": "Criar perfis em Product Hunt, G2, Capterra, Crunchbase, GetApp, e Reclame Aqui."
    })

    recs.append({
        "priority": "medium",
        "category": "Content Strategy",
        "title": "Publicar conteúdo técnico citável",
        "description": "Artigos técnicos com dados originais são as fontes preferidas das IAs generativas.",
        "impact": "alto",
        "effort": "alto",
        "action": "Criar artigos como 'Guia Completo de Tarifas de Água em SP', 'Como Identificar Cobranças Indevidas da SABESP' com dados reais."
    })

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recs.sort(key=lambda x: priority_order.get(x["priority"], 99))

    return recs


# ─────────────────────────────────────────────────────────
# 7. MULTI-PAGE ANALYSIS
# ─────────────────────────────────────────────────────────

def discover_pages(base_url, html_content):
    """Discover internal pages from the homepage for multi-page analysis.
    
    Handles:
    - Traditional href links (relative and absolute)
    - Hash-based SPA routing (#/page)
    - Sitemap.xml discovery
    - JavaScript-embedded URLs
    - No-code platform patterns (Base44, Webflow, Wix, etc.)
    """
    parsed_base = urllib.parse.urlparse(base_url)
    domain = parsed_base.netloc
    scheme = parsed_base.scheme
    base_origin = f"{scheme}://{domain}"

    internal_pages = set()

    # 1. Standard href links
    links = re.findall(r'href=["\']([^"\']+)["\']', html_content)
    for link in links:
        link = link.strip()
        if link.startswith("/") and not link.startswith("//"):
            full_url = base_origin + link.split("?")[0].split("#")[0]
            if full_url != base_origin + "/":
                internal_pages.add(full_url)
        elif link.startswith("http") and domain in link:
            clean = link.split("?")[0].split("#")[0]
            if clean != base_origin + "/" and clean != base_origin:
                internal_pages.add(clean)
        elif link.startswith("#/") and len(link) > 2:
            # Hash-based SPA routes
            internal_pages.add(base_origin + "/" + link)

    # 2. JavaScript-embedded paths (common in SPAs and no-code platforms)
    js_paths = re.findall(r'["\']/(\w[\w/-]{2,})["\']', html_content)
    for path in js_paths:
        if not any(ext in path for ext in [".js", ".css", ".png", ".jpg", ".svg", ".ico", ".woff"]):
            candidate = base_origin + "/" + path
            internal_pages.add(candidate)

    # 3. Try sitemap.xml
    sitemap_urls = _discover_from_sitemap(base_origin)
    internal_pages.update(sitemap_urls)

    # 4. Common page patterns for no-code platforms
    common_pages = [
        "/about", "/sobre", "/pricing", "/precos", "/preco",
        "/contact", "/contato", "/faq", "/blog", "/terms", "/termos",
        "/privacy", "/privacidade", "/login", "/signup", "/register",
        "/como-funciona", "/how-it-works", "/features", "/recursos",
    ]
    for page in common_pages:
        candidate = base_origin + page
        internal_pages.add(candidate)

    # Filter out non-content pages
    skip_patterns = [
        "/api/", "/static/", "/assets/", "/_next/", "/_nuxt/",
        ".js", ".css", ".png", ".jpg", ".svg", ".ico", ".woff",
        "/node_modules/", "/__", "/wp-admin", "/wp-includes",
        "/dashboard", "/admin", "/auth/", "/callback",
    ]
    filtered = [p for p in internal_pages if not any(s in p.lower() for s in skip_patterns)]

    # Remove base URL itself
    filtered = [p for p in filtered if p.rstrip("/") != base_origin.rstrip("/")]

    return sorted(set(filtered))[:20]  # Max 20 pages


def _discover_from_sitemap(base_origin):
    """Try to discover pages from sitemap.xml."""
    pages = set()
    sitemap_urls_to_try = [
        base_origin + "/sitemap.xml",
        base_origin + "/sitemap_index.xml",
        base_origin + "/sitemap-0.xml",
    ]

    for sitemap_url in sitemap_urls_to_try:
        content, status = fetch_url(sitemap_url, timeout=10)
        if status == 200 and content:
            # Extract URLs from sitemap XML
            urls = re.findall(r'<loc>([^<]+)</loc>', content)
            domain = urllib.parse.urlparse(base_origin).netloc
            for url in urls:
                if domain in url:
                    # Check if it's a sub-sitemap
                    if url.endswith(".xml"):
                        sub_content, sub_status = fetch_url(url, timeout=10)
                        if sub_status == 200 and sub_content:
                            sub_urls = re.findall(r'<loc>([^<]+)</loc>', sub_content)
                            for sub_url in sub_urls:
                                if domain in sub_url and not sub_url.endswith(".xml"):
                                    pages.add(sub_url)
                    else:
                        pages.add(url)
            if pages:
                break  # Found a working sitemap

    return pages


# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python geo_audit.py <url> [--brand 'Brand Name'] [--competitors 'comp1,comp2']", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    if not url.startswith("http"):
        url = "https://" + url

    # Parse optional args
    brand = ""
    competitors = []
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--brand" and i + 1 < len(args):
            brand = args[i + 1]
            i += 2
        elif args[i] == "--competitors" and i + 1 < len(args):
            competitors = [c.strip() for c in args[i + 1].split(",")]
            i += 2
        else:
            i += 1

    # Extract domain and brand from URL if not provided
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc
    if not brand:
        brand = domain.replace("www.", "").split(".")[0].title()

    # ── Run all analyses ──
    report = {
        "url": url,
        "domain": domain,
        "brand": brand,
        "competitors": competitors,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "audit_version": "2.0",
    }

    # 1. Robots.txt analysis
    report["robots_analysis"] = analyze_robots_txt(url)

    # 2. Fetch homepage HTML
    html_content, http_status = fetch_url(url)
    report["http_status"] = http_status

    # 3. Structured data & citability analysis (homepage)
    report["homepage_analysis"] = analyze_structured_data(url, html_content)

    # 4. Discover and analyze additional pages
    print(f"Discovering pages from {url}...", file=sys.stderr)
    pages = discover_pages(url, html_content)
    report["discovered_pages"] = pages
    report["pages_analysis"] = {}
    report["pages_status"] = {}  # Track status of each discovered page

    print(f"Found {len(pages)} candidate pages. Analyzing top 10...", file=sys.stderr)
    for page_url in pages[:10]:  # Analyze top 10 pages
        try:
            page_html, page_status = fetch_url(page_url, timeout=10)
            report["pages_status"][page_url] = page_status
            if page_status == 200 and page_html and len(page_html) > 200:
                # Verify it's actual content, not just a redirect shell
                report["pages_analysis"][page_url] = analyze_structured_data(page_url, page_html)
                print(f"  ✓ Analyzed: {page_url} ({len(page_html)} bytes)", file=sys.stderr)
            else:
                print(f"  ✗ Skipped: {page_url} (status={page_status}, size={len(page_html) if page_html else 0})", file=sys.stderr)
        except Exception as e:
            report["pages_status"][page_url] = str(e)
            print(f"  ✗ Error: {page_url} ({e})", file=sys.stderr)
            continue

    print(f"Successfully analyzed {len(report['pages_analysis'])} additional pages.", file=sys.stderr)

    # 5. Google presence check
    report["google_presence"] = check_google_presence(brand, domain)

    # 6. Directory checklist
    report["directory_checklist"] = build_directory_checklist(brand)

    # 7. AI visibility test prompts
    report["ai_visibility_prompts"] = generate_test_prompts(brand, domain)

    # 8. Calculate GEO score
    report["geo_score"] = calculate_geo_score(
        report["robots_analysis"],
        report["homepage_analysis"],
        report["google_presence"]
    )

    # 9. Generate recommendations
    report["recommendations"] = generate_recommendations(
        report["robots_analysis"],
        report["homepage_analysis"],
        report["geo_score"]
    )

    # 10. Summary
    report["summary"] = {
        "overall_score": report["geo_score"]["percentage"],
        "grade": report["geo_score"]["grade"],
        "verdict": report["geo_score"]["verdict"],
        "critical_issues": len([r for r in report["recommendations"] if r["priority"] == "critical"]),
        "high_issues": len([r for r in report["recommendations"] if r["priority"] == "high"]),
        "medium_issues": len([r for r in report["recommendations"] if r["priority"] == "medium"]),
        "low_issues": len([r for r in report["recommendations"] if r["priority"] == "low"]),
        "total_recommendations": len(report["recommendations"]),
        "pages_discovered": len(pages),
        "pages_analyzed": len(report["pages_analysis"]) + 1,  # +1 for homepage
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
