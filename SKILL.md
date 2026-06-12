---
name: cro-geo-audit
description: Performs a comprehensive Conversion Rate Optimization (CRO) and Generative Engine Optimization (GEO) audit of any website. Platform-agnostic, it adapts to the capabilities of the host environment (browser, plain HTTP, PDF tooling) and degrades gracefully when a capability is missing. Produces a scored report with findings, prioritized recommendations, and an optional interactive dashboard. Use when a user wants to understand why their site is not converting, audit UX/SEO/performance/security/AI visibility, or get a prioritized fix list.
---

# CRO + GEO Audit

## Origin version check

At the start of a meaningful use, when internet access and Git or HTTP tooling are available, check whether this skill has a newer upstream version before performing the main task. The canonical source is:

```text
https://github.com/AndreAlmeidaDC/cro-geo-audit
```

Read the upstream `README.md` and `CHANGELOG.md` when available. Compare the local copy against the upstream default branch using the lightest safe method, such as `git fetch`, `git ls-remote`, direct raw file retrieval or repository metadata. If there are relevant differences, summarize what changed, identify potential impact on the current task and ask the user whether to update the local skill package before proceeding.

Never perform silent self-update. Never overwrite local edits without explicit user approval. If network access is unavailable, the repository cannot be reached or the task is too small to justify the check, continue with the local version and record the limitation when relevant. For the detailed protocol, read `references/version-check.md`.

Performs a comprehensive Conversion Rate Optimization (CRO) and Generative Engine Optimization (GEO) audit of any website. The core analyses run from the skill's own scripts with no dependency on external tools like NAIA, Otterly, or HubSpot. Browser-dependent phases have explicit fallback modes, so the audit completes in any environment and always declares which mode was used.

## When to Use

Use this skill when the user wants to:
- Understand why their website is not converting visitors into customers
- Audit a website for UX, SEO, performance, security, and AI visibility issues
- Get a prioritized list of fixes to improve conversion rates
- Generate an interactive CRO dashboard with visual scores and findings
- Evaluate their site's visibility in AI-powered search engines (ChatGPT, Gemini, Perplexity, Copilot)

## Path conventions

This skill never assumes a fixed install location. Two paths are used throughout this document:

- `SKILL_DIR`: the directory where this skill is installed (the directory containing this SKILL.md). Resolve it at the start and reuse it.
- `WORK_DIR`: the platform's writable working directory for outputs (for example `/home/claude` on Claude, `/home/ubuntu` on Manus, the project root elsewhere).

All script invocations below use these placeholders. Replace them with the real paths of the current environment.

## Workflow Overview

The audit follows 8 sequential phases:

0. **Environment Capabilities Check** - Detect what the host platform offers and pick the operating mode of each later phase
1. **Automated Technical Audit** - Run `technical_audit.py` to collect performance, headers, robots.txt, sitemap, SSL data
2. **SEO Meta Analysis** - Run `seo_meta_check.py` to extract and evaluate meta tags, Open Graph, Schema.org from all pages
3. **Autonomous GEO Audit** - Run `geo_audit.py` to analyze AI crawler access, structured data quality, content citability, directory presence, and calculate GEO score
4. **AI Visibility Verification** - Test the brand in AI assistants (browser mode) or run the documented fallback modes
5. **Navigation Audit** - Evaluate CRO, UX, copy, CTAs, and funnel (browser mode or static HTTP mode)
6. **Report Generation** - Compile all findings into a structured Markdown report, score each category, and export (PDF when available)
7. **Dashboard Generation** (optional) - Create an interactive dashboard using the best format the platform supports

---

## Phase 0: Environment Capabilities Check

Before any analysis, detect the capabilities of the current environment and record the result. This determines the operating mode of Phases 4, 5, 6 and 7.

Check, in order:

1. **Python 3**: can the environment execute Python scripts? (`python3 --version` or equivalent)
2. **Python dependencies**: can `requests` and `beautifulsoup4` be imported? If not, can they be installed from `SKILL_DIR/requirements.txt`? (on some platforms `pip install` needs `--break-system-packages`)
3. **Interactive browser**: is there a tool that can open pages, click, fill forms and take screenshots?
4. **Plain HTTP fetch**: is there a tool that can retrieve URLs and return content? (almost always yes)
5. **Web search**: is there a search tool available?
6. **Markdown to PDF conversion**: is any of these available, in order of preference: a platform-native PDF skill or tool, `pandoc`, `manus-md-to-pdf` (Manus only), Python `weasyprint` or `markdown-pdf`?
7. **Interactive artifact or app output**: can the platform render a single-file HTML page or a React component?

Record the detected capabilities in a short capability note (a few lines) that will be included in the final report under "Audit methodology". Every phase below states what to do when a capability is missing. The audit must never abort because of a missing capability; it must degrade to the documented fallback and say so.

For the full capability matrix and decision rules, read [references/environment-adapters.md](references/environment-adapters.md).

---

## Phase 1: Automated Technical Audit

Run the technical audit script against the target URL:

```bash
python3 "SKILL_DIR/scripts/technical_audit.py" https://example.com > "WORK_DIR/technical_audit_results.json"
```

This script is standard-library only and runs on any Python 3. It automatically checks:
- Response times (DNS, TCP, SSL, TTFB, total)
- HTTP response headers
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- robots.txt content and AI bot blocking status
- sitemap.xml existence and URL count
- SSL certificate validity

Save the JSON output for use in Phase 6.

If Python is not available in the environment, perform a reduced version of this phase with the HTTP fetch tool: retrieve the homepage, `robots.txt` and `sitemap.xml`, record response headers when the tool exposes them, and mark the timing metrics as not assessable in the capability note.

---

## Phase 2: SEO Meta Analysis

This script requires `requests` and `beautifulsoup4`. Install them first if needed:

```bash
pip install -r "SKILL_DIR/requirements.txt"
# on externally managed environments:
# pip install -r "SKILL_DIR/requirements.txt" --break-system-packages
```

Run the SEO meta check script against all important pages:

```bash
python3 "SKILL_DIR/scripts/seo_meta_check.py" \
  https://example.com \
  https://example.com/produtos \
  https://example.com/blog \
  https://example.com/cadastro \
  > "WORK_DIR/seo_meta_results.json"
```

This script extracts and evaluates per page:
- Title tag (length, quality)
- Meta description (length, quality)
- Canonical URL
- Open Graph tags (completeness)
- Twitter Card tags
- Heading hierarchy (H1 count, structure)
- Schema.org JSON-LD (types, completeness)
- Images without alt text
- Internal/external link counts
- Per-page SEO score

If the dependencies cannot be installed, the script exits with a structured JSON error explaining what is missing. In that case, cover the most important checks (title, meta description, canonical, Open Graph, H1 count, JSON-LD presence) by fetching each page with the HTTP tool and inspecting the HTML directly, and mark the per-page numeric SEO score as not computed.

Save the JSON output for use in Phase 6.

---

## Phase 3: Autonomous GEO Audit

This is the core GEO analysis phase. Run the `geo_audit.py` script which performs the ENTIRE GEO analysis autonomously (standard-library only):

```bash
python3 "SKILL_DIR/scripts/geo_audit.py" \
  https://example.com \
  --brand "Brand Name" \
  --competitors "competitor1,competitor2" \
  > "WORK_DIR/geo_audit_results.json"
```

The script performs **6 autonomous analyses**:

### 3.1 AI Crawler Accessibility Analysis
- Fetches and parses `robots.txt`
- Checks 12 AI crawlers (GPTBot, ChatGPT-User, Google-Extended, Googlebot, Bingbot, anthropic-ai, ClaudeBot, PerplexityBot, Bytespider, CCBot, FacebookBot, cohere-ai)
- Classifies each as `allowed`, `allowed_restricted`, or `blocked` with the specific rule that causes the classification
- **`allowed`**: No blocking rules, or explicit `Allow: /` with no restrictions
- **`allowed_restricted`**: `Allow: /` is present but specific paths are blocked (e.g., `/dashboard`). This is correct behavior and does NOT count as blocked
- **`blocked`**: `Disallow: /` without a corresponding `Allow: /`
- Correctly handles the precedence: specific agent rules override wildcard (`*`) rules
- Identifies critical vs non-critical crawlers
- **Scoring**: 25 points max. Deducts 5 points per critical crawler blocked, 2 per non-critical. `allowed_restricted` crawlers are NOT penalized

### 3.2 Structured Data Quality Analysis
- Fetches the homepage HTML
- Extracts all JSON-LD blocks
- Identifies Schema types (Organization, Product, FAQPage, HowTo, Article, BreadcrumbList, WebSite, LocalBusiness)
- Evaluates completeness of meta tags and Open Graph
- **Scoring**: 20 points max based on presence of key Schema types

### 3.3 Content Citability Analysis
- Analyzes content depth (word count, heading hierarchy)
- Detects FAQ patterns in content
- Counts statistical data (numbers with %)
- Counts citation patterns ("segundo", "de acordo com", "fonte:")
- Counts structured elements (lists, tables)
- Evaluates heading hierarchy quality
- **Scoring**: 20 points max based on citability factors

### 3.4 Multi-Page Discovery & Analysis
- Discovers internal pages using 4 methods:
  1. Standard `href` links from homepage HTML
  2. JavaScript-embedded paths (common in SPAs and no-code platforms like Base44, Webflow, Wix)
  3. `sitemap.xml` discovery (tries sitemap.xml, sitemap_index.xml, sitemap-0.xml)
  4. Common page pattern probing (/about, /faq, /pricing, /como-funciona, /blog, etc.)
- Handles hash-based SPA routing (`#/page`)
- Filters out non-content pages (API endpoints, static assets, admin areas)
- Discovers up to 20 candidate pages, analyzes the top 10 for Schema, citability, and content quality
- Provides per-page breakdown with HTTP status tracking
- Logs progress to stderr for debugging

### 3.5 Google Presence Check
- Searches Google for the brand name and domain
- Estimates the number of indexed results
- **Scoring**: 10 points max based on Google presence

### 3.6 Directory Presence Checklist
- Generates a checklist of 10 directories to verify (Product Hunt, G2, Capterra, Crunchbase, LinkedIn, GitHub, Wikipedia, Reclame Aqui, Trustpilot, Google Business)
- Provides check URLs for each directory

### 3.7 AI Visibility Test Prompts
- Generates 15 test prompts in Portuguese to test in ChatGPT, Gemini, Perplexity, and Copilot
- Prompts cover brand recognition, category searches, and competitor comparisons

### 3.8 GEO Score Calculation
- Calculates a total GEO score out of 100 across 6 sub-categories:
  - AI Crawler Accessibility (25 pts)
  - Structured Data Quality (20 pts)
  - Content Citability (20 pts)
  - Meta & OG Completeness (15 pts)
  - Content Architecture (10 pts)
  - External Authority (10 pts)
- Assigns a grade (A-F) and verdict

### 3.9 Prioritized Recommendations
- Generates specific, actionable recommendations based on findings
- Each recommendation includes: priority (critical/high/medium/low), category, title, description, impact, effort, and action
- Sorted by priority

Save the JSON output for use in Phases 4 and 6.

---

## Phase 4: AI Visibility Verification

Use the test prompts generated by `geo_audit.py` (in `ai_visibility_prompts`). Pick the highest mode available in this environment and state the mode used in the report.

### Mode A: interactive browser available

Manually test the brand's visibility:

1. Open ChatGPT (chat.openai.com) and test 3-5 key prompts
2. Open Gemini (gemini.google.com) and test the same prompts
3. Open Perplexity (perplexity.ai) and test the same prompts
4. Open Copilot (copilot.microsoft.com) and test the same prompts

For each test, record:
- Does the brand appear? (yes/no)
- Is it cited with a link?
- Position in the response (1st paragraph, middle, end, not present)
- Sentiment (positive, neutral, negative)
- Competitors mentioned alongside

Also verify directory presence using the `directory_checklist` URLs from the geo_audit.py output.

### Mode B: no browser, but web search and HTTP fetch available

Direct testing inside AI assistants is not possible, so measure the public signals those assistants rely on:

1. Run web searches for the brand name, the brand plus category terms, and the brand versus each competitor
2. Record whether the brand appears in results, in which position, and whether authoritative third-party sources mention it
3. Verify each URL in `directory_checklist` with the HTTP fetch tool and record present/absent
4. Mark the direct assistant tests as "not performed in this environment" and explain that the search-presence proxy was used instead

### Mode C: no browser and no search

Generate a manual test kit for the user instead of skipping the phase:

1. Create `WORK_DIR/ai_visibility_manual_test.md` containing the 15 prompts, organized per assistant, with a fill-in table (brand appears? cited with link? position? sentiment? competitors mentioned?)
2. Tell the user to run the prompts themselves and return the filled file for incorporation into the report
3. In the report, mark the AI visibility section as "pending manual verification" and base the GEO external-authority commentary only on the script's autonomous signals

In all modes, save results in a Markdown file for use in Phase 6.

---

## Phase 5: Navigation Audit

**Read the full checklist:** See [references/cro-checklist.md](references/cro-checklist.md) for the complete CRO evaluation criteria covering:
- Homepage / Landing Page
- Proposta de Valor e Copy
- CTAs e Botões
- Formulários e Cadastro
- Funil de Conversão
- Prova Social e Confiança
- Preços e Pagamento
- Blog e Conteúdo
- Mobile e Responsividade
- Acessibilidade

### Mode A: interactive browser available

Browse every page of the site. Key actions:

1. Visit the homepage and evaluate the hero section (< 5 seconds to understand value)
2. Click every CTA and verify destinations (no 404s)
3. Test the signup/login flow end-to-end
4. Test any interactive tools (simulators, calculators)
5. Check the blog for broken images and internal CTAs
6. Verify the pricing page for clarity and anchoring
7. Test partner/affiliate pages if they exist
8. Take screenshots of critical issues when the browser supports it

### Mode B: no browser, HTTP fetch only

Perform a static evaluation of the rendered HTML:

1. Fetch the homepage and the main pages discovered in Phase 3 (products, pricing, signup, blog)
2. Evaluate what is visible in the HTML: hero copy and value proposition text, CTA labels and their `href` destinations, form fields and required attributes, social proof elements, pricing structure
3. Verify CTA destinations by fetching each linked URL and recording the HTTP status (catches 404s without clicking)
4. Apply the CRO checklist, marking visual items (layout, contrast, responsiveness, animation) and behavioral flows (end-to-end signup, interactive tools) as "not assessable in this environment"
5. If the site is a JavaScript-rendered SPA and the fetched HTML is an empty shell, state that static analysis covers only the server-rendered surface and recommend a browser-mode follow-up

In both modes, save detailed notes in a Markdown file for each page evaluated.

---

## Phase 6: Report Generation

Compile all findings into a structured report.

**Use the report template:** See [templates/report-template.md](templates/report-template.md) for the exact structure.

**Score each category using the rubric:** See [references/scoring-rubric.md](references/scoring-rubric.md) for detailed scoring criteria for CRO, UX, SEO, Performance, Security, and GEO.

**Steps:**
1. Calculate scores for each category using the rubric
2. For the GEO score, use the score calculated by `geo_audit.py` (normalize to 0-100 scale using `percentage` field)
3. Calculate the weighted overall score: `(CRO×0.25) + (UX×0.20) + (SEO×0.20) + (Perf×0.15) + (Seg×0.10) + (GEO×0.10)`
4. Fill in the report template with all findings, organized by section
5. Include an "Audit methodology" note with the capability summary from Phase 0 and the modes used in Phases 4 and 5, so the reader knows exactly how each finding was obtained
6. Include the GEO section with: crawler blocking table, Schema analysis, citability metrics, directory checklist, AI visibility test results, and all recommendations from `geo_audit.py`
7. Create the prioritized recommendations list (Critical → High → Medium → Low)
8. Export the report using the first available option:
   1. A platform-native Markdown to PDF skill or tool, when the platform provides one
   2. `pandoc` (`pandoc report.md -o report.pdf`)
   3. `manus-md-to-pdf` (Manus environments only)
   4. Python `weasyprint` or equivalent, if installable
   5. Universal fallback: generate a styled standalone HTML version of the report and deliver Markdown plus HTML, telling the user the HTML prints cleanly to PDF from any browser

The PDF is a convenience, not a gate. Never fail or stall the audit because no PDF converter exists; fall back to Markdown plus HTML and say so.

---

## Phase 7: Dashboard Generation (Optional)

If the user wants an interactive dashboard, build it in the best format the platform supports, in this order of preference:

1. The platform's native interactive artifact or app format (for example a React artifact on Claude, a webdev project on Manus)
2. Universal fallback: a single-file standalone HTML dashboard with inline CSS and JavaScript, openable in any browser

**Use the data template:** See [templates/dashboard-data-template.ts](templates/dashboard-data-template.ts) for the data structure.

**Dashboard sections to include:**
1. **Header** - Site name, date, overall score gauge
2. **Score Gauges** - One animated gauge per category (CRO, UX, SEO, Perf, Seg, GEO)
3. **Conversion Funnel** - Visual funnel with drop-off percentages at each step
4. **Findings Grid** - Filterable list of all problems by severity and category, with expandable details
5. **Performance Metrics** - TTFB, total load, page size with visual indicators
6. **Security Headers** - Table with present/absent status and severity
7. **GEO Section** - AI crawler blocking grid (allowed/blocked per bot), GEO sub-score bars, content citability metrics, directory presence checklist, AI visibility test results, competitor comparison
8. **Top Actions** - 3-5 highest-impact recommendations with effort/impact assessment

**Design recommendation:** Dark theme ("War Room" aesthetic) with severity-based color coding (red = critical, orange = high, yellow = medium, green = positive). Use Recharts for gauges when building a React artifact, or lightweight inline SVG and CSS when building the standalone HTML fallback.

---

## Output Files

At the end of the audit, the following files should be produced in `WORK_DIR`:

| File | Description |
|------|-------------|
| `technical_audit_results.json` | Raw output from technical_audit.py |
| `seo_meta_results.json` | Raw output from seo_meta_check.py |
| `geo_audit_results.json` | Raw output from geo_audit.py (complete GEO analysis) |
| `ai_visibility_notes.md` | AI visibility results (mode A or B) or manual test kit (mode C) |
| `cro_analysis_notes.md` | Navigation audit notes (mode A or B) |
| `relatorio_cro_[site].md` | Final report in Markdown (always produced) |
| `relatorio_cro_[site].pdf` | Final report in PDF (when a converter is available) |
| `relatorio_cro_[site].html` | Styled HTML version (when PDF is unavailable) |
| Interactive dashboard (optional) | Native artifact or standalone HTML |

---

## Tips

- Always run ALL THREE scripts (technical_audit.py, seo_meta_check.py, geo_audit.py) BEFORE starting the navigation audit; the data informs what to look for
- The `geo_audit.py` script is 100% autonomous and does not require any external tool, API key, or third-party report
- If the user happens to provide an external GEO report (e.g., NAIA), use it as supplementary data to cross-validate the autonomous analysis, but never depend on it
- Take screenshots of critical issues during navigation when a browser with screenshot capability is available
- The scoring rubric is a guide, not a rigid formula; use judgment for edge cases
- For sites with many pages, prioritize: Homepage → Products/Pricing → Signup → Blog → Other
- Deliver the final report as PDF when a converter exists, since users prefer sharing PDFs with their teams; otherwise deliver Markdown plus the styled HTML fallback
- For the AI visibility browser tests, focus on the 5 most relevant prompts rather than all 15 to save time
- Whatever the environment, the report must state which modes were used in Phases 4 and 5; transparency about method is part of the audit's credibility
