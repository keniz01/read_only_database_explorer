"""
SQL Query API - Entry point for the SQL Query Executor service.

This module serves as the main entry point for running the FastAPI application.
All configuration, middleware, and route setup is delegated to dedicated modules.
"""

import os

import uvicorn

from app_factory import create_app

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    is_dev = os.getenv("ENVIRONMENT", "production").lower() in {
        "dev",
        "development",
        "local",
    } or os.getenv("DEBUG", "").lower() in {"true", "1"}
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # noqa: S104 - bind all interfaces for containerized deployments
        port=8002,
        reload=is_dev,
        log_level="info",
    )
