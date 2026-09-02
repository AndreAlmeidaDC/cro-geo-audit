# Architecture

The toolkit has four bounded, standard-library modules:

- `audit_common.py`: URL normalization, DNS/public-address policy, redirect revalidation, verified TLS and bounded fetches;
- `technical_audit.py`: transport, request timing, headers, robots and sitemap observations;
- `seo_meta_check.py`: page-level semantic and metadata observations;
- `geo_audit.py`: crawler-policy purposes, content surface, first-party measurement slots and controlled-query kit.

Raw JSON remains the evidence layer. Browser notes, first-party exports and query experiments are separate sources joined only in the final report. No collector calculates an overall score.
