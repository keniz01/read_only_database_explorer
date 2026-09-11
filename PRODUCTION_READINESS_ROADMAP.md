# Production Readiness Roadmap

This roadmap defines the explicit work required to move Secure DB Access Gateway from a functional prototype/staging build to a production-ready system.

## Current status summary

The repository has a strong architecture and a good test foundation, but it is not yet production-ready.

Current blockers identified during assessment:
- SQL Query API test suite is failing heavily (`43 failed, 78 passed`)
- Root cause is in the SQL safety validation path: `sqlglot` API compatibility issue (`exp.Function` no longer exists in the resolved version)
- The deployment stack is dev-oriented, with HTTP-only ingress, no TLS termination, no production-grade secrets management pattern, and no hardened release pipeline
- Operational controls (health checks, alerts, incident runbooks, backup/restore, load handling policies) are not yet defined enough for production operations

Production readiness will be considered achieved only after all tasks below are complete and verified by CI/CD, security review, and operational sign-off.

---

## Phase 0: Stabilize the baseline and unblock production

### 0.1 Fix the SQL safety validation breakage
- [ ] Pin and validate the compatible `sqlglot` version in `sql_query_api` dependencies
- [ ] Replace deprecated AST checks that rely on removed `sqlglot` APIs
- [ ] Verify `DefaultSqlSafetyChecker` blocks DML/DDL and rejects unsafe functions/tables
- [ ] Add regression tests for adversarial SQL bypass attempts
- [ ] Acceptance: all SQL Query API tests pass in CI

### 0.2 Restore the full backend quality gate
- [ ] Fix failing tenant isolation and authorization tests
- [ ] Fix arbitrary-schema query tests and GraphQL integration failures
- [ ] Fix audit sanitization and query result resource limit checks
- [ ] Run full backend unit/integration suites for auth and SQL API
- [ ] Acceptance: 100% pass for all Python service tests before release

### 0.3 Add production-grade test coverage
- [ ] Add tests for multi-tenant DB routing and database-by-tenant enforcement
- [ ] Add tests for timeout, query budget enforcement, and max-result limits
- [ ] Add failure-mode tests for connection errors and upstream API outages
- [ ] Add security regression tests for OAuth header spoofing and query injection bypasses
- [ ] Acceptance: security and resilience tests are part of required CI

---

## Phase 1: Security hardening

### 1.1 Enforce stricter read-only database controls
- [ ] Verify every database connection enforces `SET TRANSACTION READ ONLY` for PostgreSQL
- [ ] Validate SQLite connections open in read-only mode (`?mode=ro`)
- [ ] Confirm there is no path to mutation via direct SQL, GraphQL, or CLI execution
- [ ] Audit all DB access layers for bypasses or helper APIs that can execute non-SELECT statements
- [ ] Acceptance: code review + security review confirms no write path exists

### 1.2 Harden auth and session handling
- [ ] Validate Auth0 JWT verification is strictly server-side and header-supplied roles are ignored
- [ ] Confirm tenant claims are required and cannot be spoofed
- [ ] Harden cookie/session settings (`HttpOnly`, `Secure`, `SameSite`, expiry, rotation)
- [ ] Add lockout or rate limiting for authentication failures at the gateway and API layers
- [ ] Acceptance: auth attack tests pass and security review sign-off is recorded

### 1.3 Dependency and secret hygiene
- [ ] Run `pip-audit`/`npm audit` and remediate critical findings
- [ ] Ensure no secrets are committed to the repository or generated files
- [ ] Move secret handling to environment/secret-manager best practice for every environment
- [ ] Add secret rotation procedure and emergency response guidance
- [ ] Acceptance: no high-risk dependency issues remain and secret scanning passes

---

## Phase 2: Production infrastructure and deployment hardening

### 2.1 Replace dev deployment assumptions with production deployment
- [ ] Add a production override for Docker Compose or move to managed deployment manifests
- [ ] Configure TLS/HTTPS termination at the edge (reverse proxy or load balancer)
- [ ] Restrict public exposure to only required ports and endpoints
- [ ] Add explicit network segmentation and service isolation
- [ ] Acceptance: deployment can be brought up in a production-like environment without unsafe defaults

### 2.2 Add health checks and startup guarantees
- [ ] Add liveness/readiness endpoints to all services
- [ ] Add Docker health checks and dependency startup ordering checks
- [ ] Define fail-fast behavior for missing config or unreachable dependencies
- [ ] Add graceful degradation for DB or Auth0 outage states
- [ ] Acceptance: platform can self-diagnose unhealthy components and fail predictably

### 2.3 Add operational security controls
- [ ] Restrict CORS to approved production origins only
- [ ] Require TLS for all cross-service communications in production
- [ ] Add WAF/reverse-proxy hardening rules and request limits
- [ ] Review and document NGINX exposure policy for admin and API endpoints
- [ ] Acceptance: no insecure public endpoints remain in production config

---

## Phase 3: Data layer and resilience

### 3.1 Production database strategy
- [ ] Define the production database topology and failover plan
- [ ] Add explicit backup and restore procedures for tenant databases
- [ ] Define retention, snapshot policy, and disaster recovery objective (RTO/RPO)
- [ ] Validate read-only access patterns against database-level permissions and least privilege
- [ ] Acceptance: DB administrators have a tested restore plan and least-privilege configuration

### 3.2 Query safety and performance budgets
- [ ] Enforce maximum query execution time, row limits, and byte limits in the gateway
- [ ] Validate query budget behavior under concurrent traffic
- [ ] Add resource limits for schema introspection, result serialization, and audit payload sizes
- [ ] Add circuit-breaking or queue backpressure under database overload
- [ ] Acceptance: production stress tests confirm predictable behavior under load

### 3.3 Database and API observability at the data layer
- [ ] Add DB query metrics, connection pool metrics, and latency dashboards
- [ ] Log tenant, org, query hash, and execution metadata in a privacy-safe format
- [ ] Ensure audit logs are sanitized and retention policies are enforced
- [ ] Acceptance: data access can be traced and audited without exposing raw SQL or sensitive row data

---

## Phase 4: Monitoring, alerts, and operational maturity

### 4.1 Observability stack
- [ ] Validate Grafana/Loki/Tempo/OTel stack in a real deployment
- [ ] Add dashboards for service availability, DB latency, auth failures, GraphQL failure rates, and error budgets
- [ ] Add alert thresholds for critical endpoints and infrastructure services
- [ ] Ensure correlation IDs and structured logs are emitted consistently across services
- [ ] Acceptance: operators can diagnose failures without manual log searching

### 4.2 Incident response and runbooks
- [ ] Write runbooks for Auth0 outage, DB outage, API error spike, and reverse-proxy failure
- [ ] Define escalation paths and on-call ownership
- [ ] Document log collection, support troubleshooting steps, and service dependencies
- [ ] Acceptance: team can execute recovery procedures without developer tribal knowledge

### 4.3 Capacity and resilience testing
- [ ] Conduct load testing with realistic concurrent queries
- [ ] Test failover, restart, and partial-service outage recovery
- [ ] Validate rate limiting and request throttling behavior under attack traffic
- [ ] Accept a defined concurrency and resource envelope for production deployment
- [ ] Acceptance: service remains stable under expected production load

---

## Phase 5: Release management and compliance gate

### 5.1 CI/CD pipeline hardening
- [ ] Require all backend tests, frontend build, lint, and security scans in PR checks
- [ ] Add deployment gate checks for production branch/tag
- [ ] Add artifact provenance and signed release verification if required
- [ ] Validate rollback steps and version pinning for all infrastructure and application dependencies
- [ ] Acceptance: production deployment is versioned, traceable, and reversible

### 5.2 Security review and compliance sign-off
- [ ] Complete a formal security review covering auth, DB access, secrets, and ingress
- [ ] Remediate all high/critical findings before production sign-off
- [ ] Document threat model and residual risks
- [ ] Define access control and approval process for tenant onboarding and database permissions
- [ ] Acceptance: security sign-off is recorded and reviewed by stakeholders

### 5.3 Production launch checklist
- [ ] Production secrets populated and verified
- [ ] Production tenant mapping configured and validated
- [ ] TLS and network policy verified
- [ ] Monitoring/alerting tested and operational
- [ ] Backups validated
- [ ] Rollback procedure tested
- [ ] Launch communication and support escalation plan approved
- [ ] Acceptance: all launch checklist items are complete and signed off

---

## Milestones

### Milestone A: Stable and secure core (required before staging)
- SQL safety checker fixed
- all backend tests passing
- security review completed
- tenant isolation validated

### Milestone B: Deployment-ready (required before production)
- HTTPS/TLS configured
- secrets hardened
- health checks and observability active
- production deployment manifests and rollback verified

### Milestone C: Production launch gate (final sign-off)
- all critical/high issues resolved
- backups and DR validated
- monitoring and alerts live
- launch checklist signed by engineering + security + operations

---

## Suggested execution order

1. Fix SQL safety validation path and restore the Python test suite
2. Complete security hardening and dependency audit
3. Add production-grade deployment configuration and TLS
4. Validate operational monitoring, backup, and rollback
5. Run production launch gate and sign-off

---

## Definition of done for production readiness

The system is production-ready only when all of the following are true:
- All required automated tests pass in CI
- No critical or high-severity security findings remain open
- Database access is strictly read-only and tenant-isolated
- Production environment is encrypted, monitored, and backed up
- Rollback and incident response procedures are documented and tested
- Stakeholders have signed off on go-live

This roadmap should be treated as the minimum required work; any environment-specific compliance or architecture requirements should be added before the final release decision.
