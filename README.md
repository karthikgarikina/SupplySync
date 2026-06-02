# SupplySync Backend

Production-grade inventory and order management backend built with Django, Django REST Framework, PostgreSQL, Redis, Celery, and Simple JWT.

## Local Setup

1. Create and activate a Python 3.11 or 3.12 virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and adjust values if needed.
4. Start infrastructure:

```bash
docker compose up -d postgres redis
```

5. Run migrations:

```bash
python manage.py migrate
```

6. Start the API:

```bash
python manage.py runserver
```

The API is served at `http://127.0.0.1:8000/`. OpenAPI schema is available at `/api/schema/`, Swagger UI at `/api/schema/swagger-ui/`, and ReDoc at `/api/schema/redoc/`.

## Workers

Run the background workers with Docker Compose:

```bash
docker compose up celery_worker celery_beat
```

## Tests

```bash
pytest
```

