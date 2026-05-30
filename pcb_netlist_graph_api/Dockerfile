FROM python:3.11-slim AS builder

WORKDIR /build
RUN pip install uv
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

FROM python:3.11-slim AS runtime

WORKDIR /app
COPY --from=builder /build/.venv /app/.venv
COPY catalog/ ./catalog/
COPY pcb_api/ ./pcb_api/
COPY manage.py ./
COPY fixtures/ ./fixtures/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=3 \
    CMD python manage.py check || exit 1

EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
