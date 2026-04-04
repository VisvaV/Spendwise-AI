FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run DB Migrations dynamically and start FastAPI
CMD ["bash", "-c", "alembic upgrade head && python -m app.db.mongo_init && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
