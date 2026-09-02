# Contributing

1. Create a branch.
2. Add or update a regression test before changing collection, safety or inference behavior.
3. Run `python3 scripts/validate_skill.py` and `python3 scripts/test_evidence_audit.py`.
4. Update `metadata.json`, `SKILL.md` and `CHANGELOG.md` together.
5. Open a PR describing evidence impact, false-positive/false-negative risk and remaining blind spots.

## Non-negotiable rules

- Never disable TLS verification.
- Never fetch private or non-global targets by default.
- Never turn static proxies into conversion, ranking or citation claims.
- Never hardcode a vertical, brand, directory list or platform claim as universal.
- Never submit forms or mutate external services during a default audit.
- Prefer current primary sources for volatile crawler and platform behavior.
