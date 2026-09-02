#!/usr/bin/env python3
"""Shared safe HTTP helpers for CRO/GEO evidence collection."""
from __future__ import annotations

import ipaddress
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass

MAX_RESPONSE_BYTES = 5_000_000
USER_AGENT = "CROGeoEvidenceBot/3.0 (+https://github.com/AndreAlmeidaDC/cro-geo-audit)"


@dataclass
class FetchResult:
    requested_url: str
    final_url: str | None
    status: int | None
    headers: dict[str, str]
    body: str
    elapsed_ms: int | None
    transport_verified: bool
    error_type: str | None = None
    error: str | None = None
    truncated: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("URL is empty")
    if "://" not in value:
        value = "https://" + value
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http and https URLs are supported")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in URLs are not allowed")
    return urllib.parse.urlunsplit(parsed)


def _resolved_ips(hostname: str) -> set[ipaddress._BaseAddress]:
    values: set[ipaddress._BaseAddress] = set()
    for item in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM):
        values.add(ipaddress.ip_address(item[4][0]))
    return values


def validate_public_url(value: str, allow_private: bool = False) -> str:
    url = normalize_url(value)
    host = urllib.parse.urlsplit(url).hostname
    assert host is not None
    try:
        addresses = _resolved_ips(host)
    except socket.gaierror as exc:
        raise ValueError(f"DNS resolution failed for {host}: {exc}") from exc
    if not addresses:
        raise ValueError(f"No address resolved for {host}")
    if not allow_private:
        blocked = [str(ip) for ip in addresses if not ip.is_global]
        if blocked:
            raise ValueError(f"Private, loopback, link-local, reserved or non-global address blocked: {', '.join(blocked)}")
    return url


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allow_private: bool = False, max_redirects: int = 8):
        super().__init__()
        self.allow_private = allow_private
        self.max_redirects = max_redirects
        self.count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.count += 1
        if self.count > self.max_redirects:
            raise urllib.error.HTTPError(req.full_url, code, "Too many redirects", headers, fp)
        target = urllib.parse.urljoin(req.full_url, newurl)
        validate_public_url(target, allow_private=self.allow_private)
        return super().redirect_request(req, fp, code, msg, headers, target)


def fetch_text(value: str, *, timeout: float = 15, allow_private: bool = False,
               max_bytes: int = MAX_RESPONSE_BYTES, method: str = "GET") -> FetchResult:
    requested = validate_public_url(value, allow_private=allow_private)
    redirect = SafeRedirectHandler(allow_private=allow_private)
    context = ssl.create_default_context()
    opener = urllib.request.build_opener(redirect, urllib.request.HTTPSHandler(context=context))
    request = urllib.request.Request(requested, method=method, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml,text/plain;q=0.9,*/*;q=0.5",
    })
    started = time.perf_counter()
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
            truncated = len(raw) > max_bytes
            raw = raw[:max_bytes]
            content_type = response.headers.get_content_charset() or "utf-8"
            body = raw.decode(content_type, errors="replace") if method != "HEAD" else ""
            return FetchResult(
                requested_url=requested,
                final_url=response.geturl(),
                status=getattr(response, "status", None),
                headers={k.lower(): v for k, v in response.headers.items()},
                body=body,
                elapsed_ms=round((time.perf_counter() - started) * 1000),
                transport_verified=True,
                truncated=truncated,
            )
    except ssl.SSLCertVerificationError as exc:
        return FetchResult(requested, None, None, {}, "", None, False,
                           "tls_verification_failed", str(exc))
    except urllib.error.HTTPError as exc:
        raw = exc.read(max_bytes + 1) if method != "HEAD" else b""
        return FetchResult(
            requested, exc.geturl(), exc.code,
            {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {},
            raw[:max_bytes].decode("utf-8", errors="replace"),
            round((time.perf_counter() - started) * 1000), True,
            "http_error", str(exc), len(raw) > max_bytes,
        )
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        reason = getattr(exc, "reason", exc)
        is_tls = isinstance(reason, ssl.SSLCertVerificationError)
        return FetchResult(requested, None, None, {}, "", None, not is_tls,
                           "tls_verification_failed" if is_tls else "network_error", str(reason))


def origin(value: str) -> str:
    parsed = urllib.parse.urlsplit(normalize_url(value))
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{parsed.hostname}{port}"


def join_origin(value: str, path: str) -> str:
    return urllib.parse.urljoin(origin(value).rstrip("/") + "/", path.lstrip("/"))


def evidence(status: str, source: str, confidence: str, scope: str, value, note: str = "") -> dict:
    return {
        "status": status,
        "source": source,
        "confidence": confidence,
        "scope": scope,
        "value": value,
        "note": note,
    }
