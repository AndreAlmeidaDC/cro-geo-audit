#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026.09.02"
REQUIRED = [
    "SKILL.md", "README.md", "CHANGELOG.md", "metadata.json", "LICENSE",
    "references/evidence-model.md", "references/cro-checklist.md", "references/geo-checklist.md",
    "references/prioritization-rubric.md", "references/scoring-rubric.md",
    "references/environment-adapters.md", "references/version-check.md",
    "templates/report-template.md", "templates/dashboard-data-template.ts",
    "scripts/audit_common.py", "scripts/technical_audit.py", "scripts/seo_meta_check.py",
    "scripts/geo_audit.py", "scripts/test_evidence_audit.py", "scripts/validate_skill.py",
    ".github/workflows/validate-skill.yml",
]
COLLECTORS = [
    ROOT / "scripts/audit_common.py",
    ROOT / "scripts/technical_audit.py",
    ROOT / "scripts/seo_meta_check.py",
    ROOT / "scripts/geo_audit.py",
]
PROHIBITED = {
    "CERT_NONE": "TLS verification bypass",
    "check_hostname = False": "hostname verification bypass",
    "google.com/search": "search result scraping",
    "conta de água": "hardcoded vertical prompt",
    "geo_score": "synthetic GEO score",
    "visibility_verdict": "unsupported visibility verdict",
    "requests.": "third-party requests dependency",
    "subprocess.": "subprocess collector dependency",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


missing = [name for name in REQUIRED if not (ROOT / name).exists()]
if missing:
    fail("Missing required files: " + ", ".join(missing))
if (ROOT / "requirements.txt").exists():
    fail("requirements.txt must be removed; collectors are standard-library only")

metadata = json.loads((ROOT / "metadata.json").read_text(encoding="utf-8"))
if metadata.get("name") != "cro-geo-audit":
    fail("metadata name mismatch")
if metadata.get("version") != VERSION:
    fail("metadata version mismatch")
if VERSION not in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"):
    fail("changelog version mismatch")
if metadata.get("declared_capabilities", {}).get("network_egress", {}).get("expected") is not True:
    fail("network egress must be declared")
if metadata.get("declared_capabilities", {}).get("subprocess", {}).get("expected") is not False:
    fail("subprocess must be false")
if metadata.get("declared_capabilities", {}).get("dependency_install", {}).get("expected") is not False:
    fail("dependency install must be false")
if metadata.get("security_model", {}).get("tls_verification") != "required":
    fail("TLS verification must be required")
if metadata.get("security_model", {}).get("private_network_targets") != "deny-by-default":
    fail("private targets must be deny-by-default")
if metadata.get("evidence_statuses") != ["observed", "measured", "inferred", "not_measured"]:
    fail("evidence status contract mismatch")

for path in COLLECTORS:
    text = path.read_text(encoding="utf-8")
    for phrase, reason in PROHIBITED.items():
        if phrase in text:
            fail(f"{path.name}: {reason}: {phrase}")

common = (ROOT / "scripts/audit_common.py").read_text(encoding="utf-8")
for required in ["ssl.create_default_context", "validate_public_url", "SafeRedirectHandler", "max_bytes"]:
    if required not in common:
        fail(f"audit_common.py missing safety control: {required}")

skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
if not skill.startswith("---\n"):
    fail("SKILL.md frontmatter missing")
for term in ["observed", "measured", "inferred", "not_measured", "--allow-private", "TLS"]:
    if term not in skill:
        fail(f"SKILL.md missing term: {term}")
if re.search(r"(?i)overall (?:score|grade)|universal GEO score", skill) is None:
    fail("SKILL.md must explicitly prohibit a universal score")

subprocess.run([sys.executable, "-m", "py_compile", *[str(path) for path in ROOT.glob("scripts/*.py")]], check=True)
print(f"Validation passed. version={VERSION}")
