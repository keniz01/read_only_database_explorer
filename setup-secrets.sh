#!/bin/bash

# Setup script for Docker secrets
# This script helps create the secrets directory with example files

echo "Setting up Docker secrets for Secure DB Access Gateway..."
echo ""

# Create secrets directory if it doesn't exist
mkdir -p secrets

echo "Creating example secret files in secrets/ directory..."
echo "Please edit these files with your actual credentials:"
echo ""

# Create example files
cat > secrets/secret_key.txt << 'EOF'
# Replace with your generated secret key (openssl rand -hex 32)
your-secret-key-here
EOF

cat > secrets/session_secret_key.txt << 'EOF'
# Replace with your generated session secret key
your-session-secret-key-here
EOF

cat > secrets/google_client_id.txt << 'EOF'
# Your Google OAuth client ID
your-google-client-id
EOF

cat > secrets/google_client_secret.txt << 'EOF'
# Your Google OAuth client secret
your-google-client-secret
EOF

cat > secrets/gemini_api_key.txt << 'EOF'
# Your Gemini API key
your-gemini-api-key
EOF

cat > secrets/openai_api_key.txt << 'EOF'
# Your OpenAI API key
your-openai-api-key
EOF

cat > secrets/openrouter_api_key.txt << 'EOF'
# Your OpenRouter API key
your-openrouter-api-key
EOF

cat > secrets/ai_model.txt << 'EOF'
# OpenRouter model identifier
configure-your-ai-model
EOF

cat > secrets/embedding_model.txt << 'EOF'
# Gemini embedding model identifier
configure-your-embedding-model
EOF

cat > secrets/github_token.txt << 'EOF'
# Your GitHub token for Azure OpenAI
github_pat_xxx
EOF

cat > secrets/auth0_client_id.txt << 'EOF'
# Your Auth0 client ID
your-auth0-client-id
EOF

cat > secrets/auth0_client_secret.txt << 'EOF'
# Your Auth0 client secret
your-auth0-client-secret
EOF

cat > secrets/auth0_domain.txt << 'EOF'
# Your Auth0 domain
your-domain.auth0.com
EOF

cat > secrets/frontend_url.txt << 'EOF'
# Frontend URL
http://localhost:5173
EOF

cat > secrets/react_app_url.txt << 'EOF'
# React app URL
http://localhost:5173
EOF

cat > secrets/database_url.txt << 'EOF'
# PostgreSQL connection string
postgresql://music_user:music_pass@postgres:5432/music_db
EOF

cat > secrets/tenant_databases.json << 'EOF'
[
  {
    "org_id": "replace-with-auth0-org-id",
    "database_id": "default",
    "connection_string": "******postgres:5432/music_db",
    "data_schema": "music",
    "metadata_schema": "meta"
  }
]
EOF

# Default-deny starter policy: one allow rule per table so governed queries
# work with a fresh scaffold. Restrict further via columns/row_scope per
# sql_query_api/README.md "Policy enforcement".
cat > secrets/policy_policies.json << 'EOF'
[
  {"id": "allow-album", "effect": "allow", "database_id": "default", "table": "album"},
  {"id": "allow-artist", "effect": "allow", "database_id": "default", "table": "artist"},
  {"id": "allow-genre", "effect": "allow", "database_id": "default", "table": "genre"},
  {"id": "allow-label", "effect": "allow", "database_id": "default", "table": "label"},
  {"id": "allow-record-label", "effect": "allow", "database_id": "default", "table": "record_label"},
  {"id": "allow-recording-artist", "effect": "allow", "database_id": "default", "table": "recording_artist"},
  {"id": "allow-track", "effect": "allow", "database_id": "default", "table": "track"}
]
EOF

# Generate a self-signed TLS certificate for the nginx edge.
# Replace with a certificate from a trusted CA before real production use.
openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout secrets/web_tls_key.pem \
  -out secrets/web_tls_cert.pem \
  -days 365 \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:web-app,DNS:auth0_api,DNS:sql_query_api,IP:127.0.0.1" 2>/dev/null
if [ ! -f secrets/web_tls_cert.pem ] || [ ! -s secrets/web_tls_cert.pem ]; then
  echo "⚠️  openssl certificate generation failed. Create secrets/web_tls_cert.pem and secrets/web_tls_key.pem manually."
fi

echo "✅ Secret files created!"
echo ""
echo "Next steps:"
echo "1. Edit each file in the secrets/ directory with your actual credentials"
echo "2. Run: docker-compose up --build"
echo ""
echo "For production, move secrets/ outside the repository and update docker-compose.yml paths."
echo "Replace the self-signed web_tls_cert.pem / web_tls_key.pem with a trusted CA certificate."