# Stage 1: Build virtual environment
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && \
    uv venv /opt/venv && \
    VIRTUAL_ENV=/opt/venv uv pip install --no-cache -r <(uv pip compile pyproject.toml)

# Stage 2: Minimal runtime
FROM python:3.12-slim AS runner

WORKDIR /app

# Create non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -d /app appuser

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code with non-root ownership
COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 8002

CMD ["python", "main.py"]