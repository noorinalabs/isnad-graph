# Security Headers & CORS Audit Report

**Date:** 2026-03-29
**Auditor:** Yara Hadid, Senior Security Engineer
**Issue:** #492
**Scope:** All HTTP responses from the isnad-graph FastAPI application
**Reference:** OWASP Secure Headers Project, MDN Web Security Guidelines

---

## 1. Executive Summary

This audit reviewed the security headers and CORS configuration on the isnad-graph API.
Seven findings were identified (3 High, 3 Medium, 1 Low). All have been remediated in this PR.

---

## 2. CORS Configuration

### 2.1 Findings

| Setting | Before | After | Severity |
|---------|--------|-------|----------|
| `allow_origins` | `settings.cors_origins` (default `["http://localhost:3000"]`) | Unchanged | OK -- no wildcard |
| `allow_credentials` | `True` | Unchanged | OK -- required for cookie-based refresh tokens |
| `allow_methods` | `["GET", "POST"]` | `["GET", "POST", "PATCH", "OPTIONS"]` | **Medium** -- missing PATCH for admin routes |
| `allow_headers` | `["*"]` | `["Authorization", "Content-Type", "Accept", "X-Request-ID"]` | **Medium** -- wildcard weakens CORS |

### 2.2 Verification Checklist

- [x] No wildcard `*` in `allow_origins` (uses explicit list from `Settings.cors_origins`)
- [x] Preflight OPTIONS from allowed origin returns correct `Access-Control-Allow-Origin`
- [x] Preflight from disallowed origin receives no ACAO header
- [x] `Access-Control-Allow-Credentials: true` is present
- [x] PATCH method is allowed in preflight response (required by admin config endpoint)
- [x] Authorization header is explicitly allowed
- [x] No wildcard in `allow_headers`

---

## 3. Security Response Headers

### 3.1 Audit Matrix

| Header | Before | After | Severity | Rationale |
|--------|--------|-------|----------|-----------|
| `X-Content-Type-Options` | `nosniff` | `nosniff` | OK | Prevents MIME-type sniffing |
| `X-Frame-Options` | `DENY` | `DENY` | OK | Prevents clickjacking |
| `X-XSS-Protection` | `1; mode=block` | `0` | **High** | Legacy XSS Auditor introduces cross-site leak vectors (OWASP recommends `0`; CSP provides real protection) |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains` | `max-age=63072000; includeSubDomains; preload` | **Medium** | Added `preload` directive for HSTS preload list eligibility |
| `Content-Security-Policy` | `default-src 'self'` | `default-src 'self'; frame-ancestors 'none'` | **Medium** | `frame-ancestors 'none'` provides defense-in-depth with X-Frame-Options |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | `strict-origin-when-cross-origin` | OK | Appropriate for API |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | `camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()` | **Low** | Extended to cover Payment, USB, and FLoC |
| `Cross-Origin-Opener-Policy` | **Missing** | `same-origin` | **High** | Spectre mitigation -- prevents cross-origin window references |
| `Cross-Origin-Resource-Policy` | **Missing** | `same-origin` | **High** | Spectre mitigation -- prevents cross-origin resource loading |

### 3.2 Headers Not Added (Intentional)

| Header | Reason |
|--------|--------|
| `Cross-Origin-Embedder-Policy` | Would break cross-origin API consumption from the React SPA |
| `Expect-CT` | Deprecated; Certificate Transparency is enforced by browsers by default |

---

## 4. Configuration

All security headers are configurable via the `SECURITY_` environment variable prefix
(see `SecurityHeaderSettings` in `src/config.py`). This allows per-environment tuning
(e.g., relaxing CSP in development).

New configurable fields added:
- `SECURITY_X_XSS_PROTECTION` (default `0`)
- `SECURITY_HSTS_PRELOAD` (default `True`)
- `SECURITY_CROSS_ORIGIN_OPENER_POLICY` (default `same-origin`)
- `SECURITY_CROSS_ORIGIN_RESOURCE_POLICY` (default `same-origin`)

---

## 5. Test Coverage

| Test Class | Count | Description |
|------------|-------|-------------|
| `TestSecurityHeaders` | 11 | All OWASP headers including COOP, CORP, extended Permissions-Policy |
| `TestCORSConfiguration` | 6 | Origin allowlisting, credentials, PATCH method, explicit headers |
| `TestRateLimiting` | 1 | 429 response on exceeded limit |
| `TestRequestSizeLimits` | 1 | 413 response on oversized body |

All tests pass.

---

## 6. Risk Summary

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 0 | -- |
| High | 3 | Remediated |
| Medium | 3 | Remediated |
| Low | 1 | Remediated |
