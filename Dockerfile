FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PORT=8080

WORKDIR /app

COPY requirements-runtime.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements-runtime.txt

COPY src ./src

EXPOSE 8080

CMD ["sh", "-c", "python -m uvicorn api.app:app --host 0.0.0.0 --port \"${PORT:-8080}\""]
