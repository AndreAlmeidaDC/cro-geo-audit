# Environment adapters

| Capability | Use | Missing behavior |
|---|---|---|
| Python 3.10+ | Run standard-library collectors and tests. | Use verified host HTTP tools and mark omitted fields `not_measured`. |
| Interactive browser | Rendered UX, mobile, navigation, screenshots and non-submitting form checks. | Do not infer visual or behavioral findings from an HTML shell. |
| Web search | External mentions and current platform documentation. | Leave external evidence unmeasured. |
| Search Console export/connection | Google search and generative-AI performance. | Do not substitute static proxies. |
| Bing AI Performance export/connection | Cited pages and grounding-query observations. | Do not substitute estimated citations. |
| Analytics/product events | Conversion, funnel and referrals. | Label CRO findings heuristic. |
| Field performance data | Core Web Vitals and real-user performance. | Keep single-request and lab observations separate. |
| PDF/HTML renderer | Presentation layer. | Markdown remains canonical. |

## Rules

- Choose the strongest available evidence source.
- Declare every degradation in methodology and affected findings.
- Do not install dependencies merely to manufacture a score; the bundled collectors require none.
- Direct assistant experiments are separate, recorded and reproducible; authenticated automation requires authorization.
- Browser availability does not authorize form submission, account creation or checkout.
