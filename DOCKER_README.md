# Docker Setup

This project supports running the entire application stack using Docker Compose, with PostgreSQL running locally.

## Prerequisites

- Docker and Docker Compose installed
- Docker Desktop running (on macOS)

## Quick Start

1. **Bootstrap local env + TLS certs** (first time only):
   ```bash
   ./scripts/bootstrap-dev.sh
   # Creates .env from .env.example (never overwrites) and generates a
   # self-signed TLS certificate into certs/ if one does not exist.
   ```
2. **Fill in real values in `.env`** — Auth0 credentials, `APP_SECRET_KEY`
   (generate with `openssl rand -hex 32`), AI keys, the tenant database
   mapping and policy JSON (single line each). See the comments in
   `.env.example`.

3. **Run the application stack**:
   ```bash
   docker compose up --build
   ```

This will start:
- **Nginx** (reverse proxy / TLS edge) on ports 8080 (HTTP→HTTPS redirect) and 8443 (HTTPS) – proxies Auth0 API requests
- Auth0 API on port 8001 (also reachable via nginx at https://localhost:8443/api)
- SQL Query API on port 8002
- Web App on port 5173

**Note**: PostgreSQL runs on your local machine, not in a container.

**TLS**: `scripts/bootstrap-dev.sh` generates a self-signed certificate
(`certs/web_tls_cert.pem` / `certs/web_tls_key.pem`). Accept the browser
warning during local development and replace with a trusted CA certificate for
production. Because HTTPS is enforced, the browser stores session cookies with
the `Secure` flag.

## Services

### Nginx (Reverse Proxy / TLS edge)
- **Image**: nginx:alpine
- **Ports**: 8080 (HTTP, redirects to HTTPS), 8443 (HTTPS)
- **Role**: Terminates TLS and proxies `/api` requests from the web app to the Auth0 API service
- **Config**: `./nginx/nginx.conf`
- **TLS certs**: bind-mounted from `certs/web_tls_cert.pem` and `certs/web_tls_key.pem`

### Auth0 API
- **Build**: context `.` / `auth0_api/Dockerfile`
- **Port**: 8001
- **Secrets**: Auth0, AI, and session-signing credentials injected as environment variables from `.env` (`env_file`)

### SQL Query API
- **Build**: context `.` / `sql_query_api/Dockerfile`
- **Port**: 8002
- **Secrets**: Tenant database mappings and access policies injected as environment variables (`TENANT_DATABASES_JSON`, `POLICY_POLICIES_JSON`) from `.env`

### Web App
- **Build**: ./web-app
- **Port**: 5173
- **Environment**: API base URL configured for container networking

## Secrets Management

There are no secret files in the repository. All credentials live in a single
env file injected by Compose:

- **Dev**: `.env` (created from `.env.example` by `scripts/bootstrap-dev.sh`)
- **Production**: `/etc/gateway/gateway.env` (provisioned manually, `chmod 600`)
- Compose injects it into `auth0_api` and `sql_query_api` via `env_file`
  (override the path with `GATEWAY_ENV_FILE`)
- Both services read values with the shared `read_secret` loader
  (`shared/shared_secrets`), which checks the env var first and then an
  optional `NAME_FILE` path for orchestrators that mount secrets as files
- In `ENVIRONMENT=production` the services fail fast if a required secret is
  missing, so a misconfigured deployment aborts at startup

### Editing a secret (dev)

```bash
# values are plaintext in .env — just edit and restart:
docker compose up -d
```

### Sending secrets to production

```bash
# Source of truth: your password manager / secret manager.
# Copy the env file to the host:
sudo install -m 600 -o deploy -g deploy gateway.env /etc/gateway/gateway.env
docker compose --env-file /etc/gateway/gateway.env up -d --build
```

Keep a copy of the env file in a password manager — the host file is a copy,
not the backup.

## Development

For development, you can edit `.env` and rebuild:

```bash
docker compose down
docker compose up --build
```

## Production

1. Provision `/etc/gateway/gateway.env` on the host from your secret manager /
   password manager, and set `GATEWAY_ENV_FILE` accordingly (default `.env`).
2. `ENVIRONMENT=production` enables startup fail-fast for required secrets.
3. Replace the self-signed TLS cert with a trusted CA certificate (or ACME).
4. Configure proper CORS origins and external database.
5. At scale, inject the `NAME` env vars from a real secret manager (AWS
   Secrets Manager, Vault, Azure Key Vault, Doppler, …) — the
   `NAME`/`NAME_FILE` loader already supports any injected source, so you can
   swap the manual env file without code changes.

## Troubleshooting

### Check container logs
```bash
docker compose logs [service_name]
```

### Restart services
```bash
docker compose restart [service_name]
```

### "Required secret ... is not set" on startup
Your `.env`/`gateway.env` is missing a value listed in `.env.example`. Fill it
in and `docker compose up -d`. This guard intentionally fails fast when
`ENVIRONMENT=production`.

### Clean rebuild
```bash
docker compose down -v
docker compose up --build
```

## Architecture

The Docker setup creates a complete development environment with:

- **Nginx reverse proxy / TLS edge** – serves the web app SPA and proxies `https://localhost:8443/api` for auth; nginx terminates TLS and forwards to web_app:5173 / auth0_api
- Isolated PostgreSQL database
- Backend APIs with proper networking
- Frontend served with hot reload
- Env-file secret management
- Health checks for database readiness

### Request flow (Auth API)

```
Browser (localhost:8443, TLS) → nginx (proxies SPA to web_app:5173, /api to auth0_api) → auth0_api (internal:8001) → sql_query_api (internal:8002)
```