Most Critical

dump.rdb is committed to Git (Redis persistence file may contain cached or sensitive data).
Database connection strings are hardcoded in backend/alembic.ini and backend/app/core/config.py.
Backend Dockerfile runs uvicorn --reload, which is a development configuration.
API and ARQ worker run in the same FastAPI process (backend/app/main.py), preventing independent scaling.
No production deployment or CI/CD pipeline.
No secrets management (currently relying on .env).

Highly crical as well
Docker container runs as root.
No healthcheck in the backend image.
No multi-stage Docker build.
No pinned production process manager (Gunicorn/Uvicorn workers).
Databases exposed publicly in Docker Compose.

Medium
No structured logging.
No CloudWatch metrics.
No readiness endpoint validating dependencies.
No backup documentation.
No Infrastructure as Code.

Low
Improve README for production deployment.
Add .dockerignore.
Pin image digests.