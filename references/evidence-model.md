# Evidence model

## Status

| Status | Use |
|---|---|
| `observed` | Direct page, response, browser or file evidence. |
| `measured` | Appropriate first-party system or controlled experiment. |
| `inferred` | Reasoning from cited evidence; assumptions must be visible. |
| `not_measured` | Required data or capability was unavailable. |

## Required fields

Every material finding carries source, confidence, scope, evidence, consequence, recommendation and verification step.

## Source hierarchy

1. first-party behavioral or search-console measurement;
2. controlled browser or query experiment;
3. verified HTTP and rendered HTML observation;
4. external public evidence;
5. heuristic inference.

A lower layer cannot impersonate a higher one. HTML structure does not become conversion data. A single assistant answer does not become share of voice. Header presence does not become security certification.

## Freshness

Record collection date and the period covered by first-party data. Treat crawler names, assistant behavior, platform reports and search interfaces as volatile.

## Current primary-source principles

- Google states that AI search features use normal Search technical requirements; no special AI file or unique schema is required. Structured data should match visible content.
- Google Search Console generative-AI performance reporting and Bing Webmaster Tools AI Performance are preferred first-party inputs when available.
- Bing explicitly warns that citation count does not represent ranking, placement or authority.
- OpenAI search, training and user-initiated fetch controls are separate and should not be collapsed into a single “AI crawler” policy.

Verify these statements against current official documentation before a material audit because platform behavior changes.
