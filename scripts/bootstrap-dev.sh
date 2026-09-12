#!/bin/bash
set -euo pipefail

# Local development bootstrap for env-based secrets (approach A).
#
# Secrets are never stored in this repository. They live in a single
# gitignored env file (.env locally, /etc/gateway/gateway.env on a host) that
# is COPY-created from .env.example and filled in manually.
#
# This script:
#   1. Creates .env from .env.example if it does not exist (never overwrites).
#   2. Generates a self-signed TLS certificate for the nginx edge into certs/
#      if it does not exist. Production: replace with a trusted CA cert / ACME.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${GATEWAY_ENV_FILE:-.env}"
if [ ! -f "$ENV_FILE" ]; then
  cp .env.example "$ENV_FILE"
  echo "Created $ENV_FILE from .env.example"
  echo "Edit it and fill in real values:"
  echo "  open $ENV_FILE"
else
  echo "Kept  $ENV_FILE (does not overwrite existing values)"
fi

if [ ! -f certs/web_tls_cert.pem ] || [ ! -f certs/web_tls_key.pem ]; then
  mkdir -p certs
  openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout certs/web_tls_key.pem \
    -out certs/web_tls_cert.pem \
    -days 365 \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:web-app,DNS:auth0_api,DNS:sql_query_api,IP:127.0.0.1" 2>/dev/null
  chmod 600 certs/web_tls_key.pem
  echo "Generated self-signed TLS certificate (localhost) into certs/"
else
  echo "Kept  certs/ (existing TLS certificate)"
fi

echo ""
echo "Next steps:"
echo "1. Fill in real values in $ENV_FILE (see the comments in .env.example)."
echo "2. Run: docker compose up --build"
echo ""
echo "Production: copy $ENV_FILE to the host as /etc/gateway/gateway.env"
echo "  (chmod 600), keep the source of truth in a password manager, and run:"
echo "  docker compose --env-file /etc/gateway/gateway.env up -d"