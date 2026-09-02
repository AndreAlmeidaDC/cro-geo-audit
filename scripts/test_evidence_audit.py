#!/usr/bin/env python3
from __future__ import annotations

import json
import socket
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(HERE))

import audit_common
import geo_audit
import technical_audit
import seo_meta_check


class EvidenceAuditTests(unittest.TestCase):
    def test_private_address_is_blocked_by_default(self) -> None:
        fake_info = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 0))]
        with mock.patch('socket.getaddrinfo', return_value=fake_info):
            with self.assertRaisesRegex(ValueError, 'non-global address blocked'):
                audit_common.validate_public_url('http://internal.example')

    def test_private_address_requires_explicit_override(self) -> None:
        fake_info = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('10.0.0.8', 0))]
        with mock.patch('socket.getaddrinfo', return_value=fake_info):
            self.assertEqual(
                audit_common.validate_public_url('http://internal.example', allow_private=True),
                'http://internal.example',
            )

    def test_collectors_never_disable_tls_verification(self) -> None:
        for path in [HERE / 'audit_common.py', HERE / 'geo_audit.py', HERE / 'technical_audit.py']:
            text = path.read_text(encoding='utf-8')
            self.assertNotIn('CERT_NONE', text, path.name)
            self.assertNotIn('check_hostname = False', text, path.name)

    def test_robots_analysis_separates_search_training_and_user_fetch(self) -> None:
        robots = '''
User-agent: OAI-SearchBot
Allow: /

User-agent: GPTBot
Disallow: /

User-agent: ChatGPT-User
Disallow: /private/
'''
        result = geo_audit.analyze_robots_text(robots, 'https://example.com/public/page')
        self.assertEqual(result['crawlers']['OAI-SearchBot']['access'], 'allowed')
        self.assertEqual(result['crawlers']['OAI-SearchBot']['purpose'], 'search_discovery')
        self.assertEqual(result['crawlers']['GPTBot']['access'], 'blocked')
        self.assertEqual(result['crawlers']['GPTBot']['purpose'], 'model_training')
        self.assertEqual(result['crawlers']['ChatGPT-User']['access'], 'allowed')
        self.assertEqual(result['crawlers']['ChatGPT-User']['purpose'], 'user_initiated_fetch')
        self.assertNotIn('critical', json.dumps(result).lower())

    def test_html_analysis_returns_evidence_not_visibility_score(self) -> None:
        html = '''<!doctype html><html><head><title>Acme Platform</title>
<meta name="description" content="Acme coordinates verified workflows.">
<link rel="canonical" href="https://example.com/">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Acme"}</script>
</head><body><main><h1>Acme Platform</h1><h2>How it works</h2><p>Verified workflows with cited evidence.</p></main></body></html>'''
        result = geo_audit.analyze_html(html, 'https://example.com/')
        serialized = json.dumps(result).lower()
        self.assertIn('observed', serialized)
        self.assertNotIn('geo_score', serialized)
        self.assertNotIn('grade', serialized)
        self.assertNotIn('excellent visibility', serialized)

    def test_query_kit_is_generic_and_uses_supplied_context(self) -> None:
        kit = geo_audit.build_query_test_kit(
            brand='Nirvana-OS',
            category='orchestration operating system for AI work',
            competitors=['Example A', 'Example B'],
            locale='pt-BR',
        )
        serialized = json.dumps(kit, ensure_ascii=False).lower()
        self.assertIn('nirvana-os', serialized)
        self.assertIn('orchestration operating system for ai work', serialized)
        self.assertIn('example a', serialized)
        self.assertNotIn('conta de água', serialized)
        self.assertNotIn('sabes', serialized)
        self.assertEqual(kit['methodology']['status'], 'not_measured')

    def test_technical_report_does_not_invent_scores_or_core_web_vitals(self) -> None:
        page = audit_common.FetchResult(
            requested_url='https://example.com', final_url='https://example.com/', status=200,
            headers={'content-security-policy': "default-src 'self'"}, body='<html></html>',
            elapsed_ms=123, transport_verified=True,
        )
        robots = audit_common.FetchResult(
            requested_url='https://example.com/robots.txt', final_url='https://example.com/robots.txt', status=200,
            headers={}, body='User-agent: *\nAllow: /', elapsed_ms=33, transport_verified=True,
        )
        sitemap = audit_common.FetchResult(
            requested_url='https://example.com/sitemap.xml', final_url='https://example.com/sitemap.xml', status=404,
            headers={}, body='', elapsed_ms=25, transport_verified=True, error_type='http_error', error='404',
        )
        report = technical_audit.assemble_report('https://example.com', page, robots, sitemap)
        serialized = json.dumps(report).lower()
        self.assertNotIn('scores', report)
        self.assertNotIn('score', serialized)
        self.assertNotIn('core_web_vitals', serialized)
        self.assertEqual(report['transport']['status'], 'measured')
        self.assertEqual(report['single_request_timing']['confidence'], 'low')
        self.assertIn('not a core web vitals measurement', report['single_request_timing']['note'].lower())

    def test_seo_report_keeps_observations_separate_from_claims(self) -> None:
        fetch = audit_common.FetchResult(
            requested_url='https://example.com', final_url='https://example.com/', status=200,
            headers={}, body='<html><head><title>Example</title></head><body><h1>Example</h1></body></html>',
            elapsed_ms=90, transport_verified=True,
        )
        report = seo_meta_check.analyze_fetches([fetch])
        serialized = json.dumps(report).lower()
        self.assertNotIn('seo_score', serialized)
        self.assertEqual(report['pages'][0]['fetch']['status'], 'observed')
        self.assertEqual(report['pages'][0]['surface']['title']['value'], 'Example')

    def test_first_party_measurement_sources_are_explicitly_not_measured(self) -> None:
        sources = geo_audit.measurement_source_status()
        self.assertEqual(sources['google_search_console']['status'], 'not_measured')
        self.assertEqual(sources['bing_ai_performance']['status'], 'not_measured')
        self.assertEqual(sources['analytics']['status'], 'not_measured')
        self.assertEqual(sources['assistant_experiments']['status'], 'not_measured')
        self.assertIn('preferred', sources['google_search_console']['note'].lower())


if __name__ == '__main__':
    unittest.main()
