# Environment adapters

This reference defines how the cro-geo-audit skill adapts to the capabilities of the host platform. Phase 0 of SKILL.md performs the detection; this file defines the decision rules.

## Capability matrix

| Capability | How to detect | Used by | If missing |
|---|---|---|---|
| Python 3 | run `python3 --version` | Phases 1, 2, 3 | Reduced Phase 1 via HTTP fetch; Phase 2 manual HTML inspection; Phase 3 cannot run, score GEO qualitatively and say so |
| requests + beautifulsoup4 | `python3 -c "import requests, bs4"` or install from requirements.txt | Phase 2 | Script emits structured JSON error; fall back to HTTP fetch inspection of each page |
| Interactive browser | platform exposes a browsing/clicking tool | Phases 4 (Mode A), 5 (Mode A) | Phase 4 drops to Mode B or C; Phase 5 drops to Mode B |
| Plain HTTP fetch | platform exposes a URL fetch tool | Phases 4 (Mode B), 5 (Mode B), reduced Phase 1 | If even fetch is unavailable, only script-based phases run; everything else is marked not assessable |
| Web search | platform exposes a search tool | Phase 4 (Mode B) | Phase 4 drops to Mode C (manual test kit) |
| MD to PDF converter | native skill/tool, pandoc, manus-md-to-pdf, weasyprint | Phase 6 export | Deliver Markdown plus styled standalone HTML |
| Interactive artifact / app | platform renders React or HTML artifacts | Phase 7 | Deliver single-file standalone HTML dashboard |

## Mode selection rules

1. Always pick the highest mode available. Never ask the user to choose between modes when detection is unambiguous.
2. Never abort the audit because a capability is missing. Degrade and declare.
3. Every degradation must appear in two places: the capability note produced in Phase 0 and the "Audit methodology" section of the final report.
4. When a JavaScript-rendered SPA returns an empty HTML shell in Mode B of Phase 5, state that static analysis covers only the server-rendered surface and recommend a browser-mode follow-up.
5. When direct AI assistant testing is replaced by search-presence proxies (Phase 4 Mode B), never present proxy results as if they were direct test results.

## Known platform profiles

These profiles are illustrative, not exhaustive. Detection always wins over assumptions.

| Platform | Typical profile |
|---|---|
| Claude (claude.ai with code execution) | Python yes, pip with `--break-system-packages`, no interactive browser by default, HTTP fetch yes, web search yes, native PDF tooling available, React artifacts yes |
| Manus | Python yes, browser yes, `manus-md-to-pdf` yes, webdev projects yes |
| API-only agent or CI | Python usually yes, no browser, fetch depends on harness, no artifacts; expect Modes B/C and HTML fallbacks |

## PDF export chain

Try in order, stop at the first success:

1. Platform-native Markdown to PDF skill or tool
2. `pandoc report.md -o report.pdf`
3. `manus-md-to-pdf report.md report.pdf` (Manus only)
4. `python3 -m weasyprint report.html report.pdf` (requires installing weasyprint and rendering Markdown to HTML first)
5. Fallback: styled standalone HTML plus instructions to print to PDF from any browser

Failures in this chain are never fatal. The Markdown report is the canonical deliverable; PDF and HTML are presentation layers.
