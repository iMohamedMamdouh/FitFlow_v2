# syntax=docker/dockerfile:1

# ----------------------------------------------------------------- base
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------ builder
FROM base AS builder

COPY pyproject.toml ./
COPY app ./app
RUN pip install --prefix=/install ".[dev]"

# ----------------------------------------------------------- development
FROM base AS development

COPY --from=builder /install /usr/local
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ------------------------------------------------------------ production
FROM base AS production

# مستخدم غير root — لا يشغّل التطبيق بصلاحيات كاملة
RUN groupadd --system app && useradd --system --gid app --home /app app

COPY --from=builder /install /usr/local
COPY --chown=app:app app ./app
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini pyproject.toml ./

USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/health/live || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
