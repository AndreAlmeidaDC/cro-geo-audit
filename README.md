# cro-geo-audit

Evidence-based website audit toolkit for CRO, UX, SEO and search/AI discovery readiness.

Version `2026.09.02` removes the old universal GEO score and replaces it with source-labeled evidence, first-party measurement slots and reproducible experiments.

## Why the model changed

The previous implementation assigned points for crawlers, JSON-LD, FAQs, lists, tables, word count and estimated Google result volume, then called the total “AI visibility”. Those observations can be useful, but they do not measure ranking, citation probability or share of voice. The new version refuses that false precision.

## Main safeguards

- verified TLS; certificate errors are reported and never bypassed;
- public-target allowlist by default, with SSRF protection on redirects;
- bounded response size and timeouts;
- no Google result scraping;
- no hardcoded industry prompts or universal directory checklist;
- crawler purposes kept separate;
- no form submission, checkout or external mutation without authorization;
- no dependency installation; collectors use the Python standard library.

## Commands

```bash
python3 scripts/technical_audit.py https://example.com > technical.json
python3 scripts/seo_meta_check.py https://example.com https://example.com/pricing > pages.json
python3 scripts/geo_audit.py https://example.com \
  --brand "Example" \
  --category "workflow orchestration software" \
  --competitors "Competitor A,Competitor B" > discovery.json
```

Internal targets are blocked unless explicitly approved:

```bash
python3 scripts/technical_audit.py http://internal.example --allow-private
```

## Evidence statuses

| Status | Meaning |
|---|---|
| `observed` | Directly found in a page, response, robots file or rendered interface. |
| `measured` | Produced by an appropriate measurement system or controlled experiment. |
| `inferred` | Reasoned from evidence, with assumptions stated. |
| `not_measured` | The environment or supplied data did not support the conclusion. |

## Validation

```bash
python3 scripts/validate_skill.py
python3 scripts/test_evidence_audit.py
python3 -m py_compile scripts/*.py
```

## Limits

A static audit does not measure conversion, field performance, indexation, assistant visibility or security exploitability. Those require analytics, field data, search-console inputs, controlled experiments, browser testing or a dedicated security review.
