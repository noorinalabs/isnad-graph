# Production Deployment Security Review

**Date:** 2026-03-25
**Reviewer:** Yara Hadid, Senior Security Engineer
**Branch:** `deployments/phase10/wave-2`
**Status:** Pre-production audit

---

## Scope

The following files were reviewed for security posture ahead of production deployment:

| File | Purpose |
|------|---------|
| `terraform/main.tf` | Hetzner Cloud server, firewall, SSH key |
| `terraform/variables.tf` | Variable definitions and sensitivity |
| `terraform/versions.tf` | Provider version pinning |
| `terraform/outputs.tf` | Terraform output values |
| `docker-compose.prod.yml` | Production container orchestration |
| `Dockerfile` | Backend API container image |
| `frontend/Dockerfile` | Frontend container image |
| `Caddyfile` | Reverse proxy, TLS, security headers |
| `scripts/backup.sh` | Automated database backup to B2 |
| `scripts/restore.sh` | Database restore from B2 |
| `.envrc` | direnv environment mapping |
| `.env.example` | Example environment file |
| `.github/workflows/ci.yml` | CI pipeline configuration |

---

## Findings

### CRITICAL

#### C1: Neo4j ports exposed to the public internet

**File:** `docker-compose.prod.yml:14-15`
**Description:** Neo4j binds both the browser (7474) and Bolt (7687) ports to `0.0.0.0`, making the database directly reachable from the internet. The Hetzner firewall only allows ports 22, 80, and 443, so the host-level firewall mitigates this today. However, if the Hetzner firewall is ever misconfigured, removed, or bypassed (e.g., by switching cloud providers or adding a load balancer), Neo4j is immediately exposed with only a username/password standing between an attacker and the full graph database.

**Risk:** Direct database access from the internet; credential brute-force; data exfiltration.

**Recommendation:** Bind Neo4j to localhost or remove the `ports` directive entirely. Neo4j is on the `backend` internal network, so the API container already reaches it via Docker DNS at `neo4j:7687`. If admin access is needed, use SSH tunneling.

```yaml
# Replace:
ports:
  - "7474:7474"
  - "7687:7687"
# With:
ports:
  - "127.0.0.1:7474:7474"
  - "127.0.0.1:7687:7687"
```

**Blocks production:** YES — this is defense-in-depth; relying solely on the cloud firewall is insufficient.

---

#### C2: Backend Dockerfile runs as root

**File:** `Dockerfile`
**Description:** The API container has no `USER` directive, so the application runs as `root` inside the container. If an attacker achieves remote code execution through a vulnerability in FastAPI, a dependency, or the application code, they have root privileges inside the container, which significantly increases the blast radius (volume writes, capability exploitation, potential container escape on unpatched kernels).

**Risk:** Privilege escalation from application-level RCE to root-in-container; container escape.

**Recommendation:** Add a non-root user:

```dockerfile
RUN addgroup --system app && adduser --system --ingroup app app
USER app
```

**Blocks production:** YES

---

### HIGH

#### H1: No Redis authentication configured

**File:** `docker-compose.prod.yml:85`
**Description:** Redis is started with `--maxmemory` and `--maxmemory-policy` but no `--requirepass` flag. Any process on the backend network can connect to Redis without authentication. If an attacker compromises the API container, they get unrestricted Redis access for cache poisoning, data exfiltration, or using Redis as a pivot.

**Risk:** Unauthenticated access to cache layer; cache poisoning; potential data leakage from cached API responses.

**Recommendation:** Add `--requirepass ${REDIS_PASSWORD}` to the Redis command and add `REDIS_PASSWORD` as a required environment variable. Update `REDIS_URL` in the API service to include the password.

**Blocks production:** YES — any authenticated service on the network should require credentials.

---

#### H2: No read-only root filesystem on containers

**File:** `docker-compose.prod.yml` (all services)
**Description:** None of the containers use `read_only: true` for their root filesystem. Writable root filesystems allow attackers to drop binaries, modify application code, or install tools after gaining access.

**Risk:** Post-exploitation persistence; malware installation; configuration tampering.

**Recommendation:** Add `read_only: true` to all services where feasible (api, frontend, caddy, redis). Use `tmpfs` mounts for directories that need writes (e.g., `/tmp`). Neo4j and PostgreSQL need writable data directories but can still use read-only root with explicit volume mounts.

**Blocks production:** No — defense-in-depth improvement, but not a hard blocker.

---

#### H3: Backup staging in /tmp with predictable paths

**File:** `scripts/backup.sh:33`
**Description:** Backups are staged in `/tmp/isnad-backups` by default. The `/tmp` directory is world-readable on most Linux distributions, and the path is predictable. Database dumps staged here could be read by any user or process on the system before they are cleaned up.

**Risk:** Local information disclosure; database dumps readable by unprivileged processes.

**Recommendation:** Use `mktemp -d` for unique staging directories, or use a non-world-readable directory (e.g., `/var/backups/isnad/`) with restrictive permissions (`chmod 700`). Additionally, set `umask 077` at the top of the script so all created files default to owner-only permissions.

**Blocks production:** No — but should be fixed before the first backup runs.

---

#### H4: SSH open to all source IPs

**File:** `terraform/main.tf:14-18`
**Description:** The SSH firewall rule allows inbound connections from `0.0.0.0/0` and `::/0` (the entire internet). While key-based authentication is used (good), exposing SSH to all IPs invites brute-force attacks and increases the attack surface.

**Risk:** SSH brute-force; exposure to 0-day SSH vulnerabilities; reconnaissance by scanners.

**Recommendation:** Restrict SSH `source_ips` to known operator IP ranges or a VPN/bastion CIDR. If static IPs are not practical, consider:
- Fail2ban on the server
- Port knocking or Tailscale/WireGuard for SSH access
- At minimum, document the risk and add rate limiting

**Blocks production:** No — key-only SSH is a strong baseline, but IP restriction is recommended.

---

### MEDIUM

#### M1: Docker images use mutable tags

**File:** `docker-compose.prod.yml`, `Dockerfile`, `frontend/Dockerfile`
**Description:** Several images use mutable tags that can change without notice:
- `neo4j:5-community` — could pull a different 5.x version on next build
- `redis:7-alpine` — same issue
- `caddy:2-alpine` — same issue
- `python:3.14-slim` — same issue
- `node:22-alpine` — same issue
- `nginx:alpine` — could change major version

**Risk:** Non-reproducible builds; unexpected breaking changes; potential supply chain compromise if a tag is overwritten.

**Recommendation:** Pin images to specific digests or at minimum to full version tags (e.g., `neo4j:5.26.2-community`, `redis:7.4.2-alpine`). For application Dockerfiles, pin the exact Python and Node versions.

**Blocks production:** No — but strongly recommended before production.

---

#### M2: No Content-Security-Policy header

**File:** `Caddyfile`
**Description:** The Caddyfile sets several good security headers (HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, strips Server header) but does not include a `Content-Security-Policy` header. CSP is the primary defense against XSS attacks.

**Risk:** Reduced XSS mitigation; injected scripts can load from any origin.

**Recommendation:** Add a CSP header. A reasonable starting point:

```
Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'"
```

Tune based on actual frontend requirements (e.g., if CDN assets are needed).

**Blocks production:** No — but should be added before public launch.

---

#### M3: No Permissions-Policy header

**File:** `Caddyfile`
**Description:** No `Permissions-Policy` (formerly `Feature-Policy`) header is set. This allows the page (or any embedded iframes, if X-Frame-Options is bypassed) to access browser features like geolocation, camera, and microphone.

**Risk:** Feature abuse by injected content.

**Recommendation:** Add:

```
Permissions-Policy "geolocation=(), camera=(), microphone=(), payment=()"
```

**Blocks production:** No

---

#### M4: Terraform state not configured for remote backend

**File:** `terraform/versions.tf`
**Description:** No `backend` block is configured, so Terraform state defaults to local file storage. The state file contains sensitive information (server IPs, resource IDs, and potentially the Hetzner API token in some configurations). Local state also means no state locking, risking concurrent modifications.

**Risk:** State file exposure (contains infrastructure details); no state locking; state loss if local machine is lost.

**Recommendation:** Configure a remote backend (e.g., S3-compatible with Backblaze B2, or Terraform Cloud). Encrypt at rest. At minimum, ensure `.terraform/` and `*.tfstate*` are in `.gitignore`.

**Blocks production:** No — but a significant operational risk.

---

#### M5: CI actions not pinned to SHA

**File:** `.github/workflows/ci.yml`
**Description:** GitHub Actions are pinned to version tags (`@v4`, `@v2`) rather than immutable SHA digests. Version tags are mutable — a compromised upstream action maintainer can overwrite `v4` to inject malicious code.

**Risk:** Supply chain attack via compromised GitHub Action; secret exfiltration from CI environment.

**Recommendation:** Pin all actions to full commit SHAs:

```yaml
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
- uses: astral-sh/setup-uv@c7f87aa956e4c323abf06d5dec078e358f6b4d04  # v4.x.x
```

Keep the version comment for readability. Use Dependabot or Renovate to auto-update SHA pins.

**Blocks production:** No — but strongly recommended for supply chain security.

---

### LOW

#### L1: Frontend Nginx container runs as root

**File:** `frontend/Dockerfile`
**Description:** The Nginx container (second stage) has no `USER` directive. Similar to C2 but lower risk because this container only serves static files and has a smaller attack surface.

**Risk:** Privilege escalation if Nginx has a vulnerability.

**Recommendation:** Use `nginx:alpine` with a non-root configuration, or switch to `nginxinc/nginx-unprivileged:alpine`.

**Blocks production:** No

---

#### L2: No resource limits on `docker run` in backup/restore scripts

**File:** `scripts/backup.sh:174`, `scripts/restore.sh:208`
**Description:** The `docker run` commands for Neo4j dump/restore have no `--memory` or `--cpus` limits. A large dump could consume excessive resources on the production server.

**Risk:** Resource exhaustion during backup/restore operations.

**Recommendation:** Add `--memory=4g --cpus=2` to the `docker run` commands.

**Blocks production:** No

---

#### L3: Restore script has SQL injection potential in terminate_pg_connections

**File:** `scripts/restore.sh:149`
**Description:** The `POSTGRES_DB` variable is interpolated directly into a SQL query (`WHERE datname = '${POSTGRES_DB}'`). If `POSTGRES_DB` contains single quotes, this is SQL injection. In practice, this variable comes from the operator's environment, so the risk is theoretical.

**Risk:** SQL injection if a malformed database name is provided.

**Recommendation:** Use parameterized queries or at minimum validate that `POSTGRES_DB` matches `^[a-zA-Z_][a-zA-Z0-9_]*$`.

**Blocks production:** No — theoretical risk only.

---

### INFO (Positive Findings)

#### I1: Firewall is correctly scoped

The Hetzner firewall only opens ports 22, 80, and 443. All other inbound traffic is blocked by default. This is correct.

#### I2: Network segmentation is implemented

Docker Compose uses two networks: `backend` (internal, no external access) and `frontend` (bridge). Neo4j, PostgreSQL, and Redis are only on the backend network. The API bridges both networks. Caddy and the frontend are on the frontend network only. This is a good design.

#### I3: PostgreSQL and Redis bound to localhost

PostgreSQL (`127.0.0.1:5432`) and Redis (`127.0.0.1:6379`) host-side ports are bound to localhost only. Even if the cloud firewall is misconfigured, these services are not reachable from the internet at the host level.

#### I4: Sensitive Terraform variables marked correctly

The `hcloud_token` variable is marked `sensitive = true`, which prevents it from appearing in Terraform plan output and logs.

#### I5: Backup credentials passed via environment variables, not CLI flags

The backup script uses `RCLONE_CONFIG_ISNAD_*` environment variables instead of passing B2 credentials as CLI arguments. This prevents credential leakage via `ps aux` or `/proc/*/cmdline`.

#### I6: Backup checksums and retention

Backups use SHA256 checksums for integrity verification, and the retention policy (7 daily + 4 weekly) with pruning is well-implemented.

#### I7: Restore script has safety confirmation

The restore script requires typing "YES" to confirm, and supports `--force` for automation. The confirmation prompt clearly shows what will be overwritten.

#### I8: TLS and HSTS are properly configured

Caddy provides automatic TLS via Let's Encrypt with HSTS at `max-age=63072000` (2 years) with `includeSubDomains` and `preload`. The `Server` header is stripped. Good baseline.

#### I9: Security audit is a required CI check

The CI pipeline includes `pip-audit` for vulnerability scanning and `gitleaks` for secret detection. The comments indicate this is a required status check on main. Excellent.

#### I10: Docker services have health checks, resource limits, and log rotation

All services have health checks, memory/CPU limits, and JSON log rotation configured. This prevents resource exhaustion and enables proper orchestration.

#### I11: SSH key-based authentication

Terraform deploys SSH keys only; no password authentication is configured. The Hetzner provider defaults to disabling password auth when SSH keys are provided.

---

## Summary

| Severity | Count | Blocks Production |
|----------|-------|-------------------|
| CRITICAL | 2 | Yes (C1, C2) |
| HIGH | 4 | Yes (H1); No (H2, H3, H4) |
| MEDIUM | 5 | No |
| LOW | 3 | No |
| INFO | 11 | N/A (positive) |

**Overall Assessment:** The infrastructure has a solid foundation — good network segmentation, proper TLS, security-focused CI, and well-designed backup/restore scripts. However, there are three must-fix items before production: Neo4j port binding (C1), root containers (C2), and Redis authentication (H1). The remaining findings are defense-in-depth improvements that should be addressed in subsequent waves.

---

## Action Items

### Must-fix before production (GitHub Issues created)

1. **C1** — Bind Neo4j ports to 127.0.0.1 in docker-compose.prod.yml → [#324](https://github.com/parametrization/isnad-graph/issues/324)
2. **C2** — Add non-root USER to backend Dockerfile → [#325](https://github.com/parametrization/isnad-graph/issues/325)
3. **H1** — Enable Redis authentication with `--requirepass` → [#326](https://github.com/parametrization/isnad-graph/issues/326)

### Should-fix (GitHub Issues created for tracking)

4. **H2** — Add read-only root filesystem to containers → [#327](https://github.com/parametrization/isnad-graph/issues/327)
5. **H3** — Secure backup staging directory permissions → [#328](https://github.com/parametrization/isnad-graph/issues/328)
6. **H4** — Restrict SSH source IPs in Terraform firewall → [#329](https://github.com/parametrization/isnad-graph/issues/329)
7. **M1** — Pin Docker images to specific version tags or SHA digests
8. **M2** — Add Content-Security-Policy header to Caddyfile
9. **M4** — Configure remote Terraform state backend
10. **M5** — Pin GitHub Actions to SHA digests
