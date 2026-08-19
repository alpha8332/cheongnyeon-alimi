# syntax=docker/dockerfile:1.7
FROM python:3.14.5-slim-bookworm@sha256:a9bee15510a364124aa24692899d269835683b883de42f7ebec8c293cf679ccb

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /nonexistent --shell /usr/sbin/nologin app \
    && python -m venv /opt/venv

WORKDIR /app

COPY backend/requirements.lock /tmp/requirements.lock
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --require-hashes --no-deps --requirement /tmp/requirements.lock \
    && rm /tmp/requirements.lock

COPY backend/app /app/backend/app
COPY backend/alembic /app/backend/alembic
COPY backend/alembic.ini /app/backend/alembic.ini
COPY collectors /app/collectors
COPY data/reference /app/data/reference
COPY data/schema /app/data/schema
COPY data/seeds /app/data/seeds
COPY deployment/postgres/prepare_acceptance_schema.py /opt/acceptance/prepare_acceptance_schema.py
COPY deployment/postgres/verify_restored_database.py /opt/acceptance/verify_restored_database.py

RUN mkdir -p /app/backend/logs /app/backend/runtime \
    && chown -R app:app /app/backend/logs /app/backend/runtime

WORKDIR /app/backend
USER 10001:10001
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
