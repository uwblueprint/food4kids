# Backend

Built with Python, FastAPI, and SQLModel. Runs on port 8080 inside Docker.

## Project Structure

```
backend/python/
├── app/
│   ├── dependencies/           # Dependency injection (auth, DB sessions, services)
│   ├── migrations/             # Alembic database migrations
│   ├── models/                 # SQLModel database models
│   ├── routers/                # FastAPI route handlers
│   ├── schemas/                # Pydantic schemas for API request/response
│   ├── services/
│   │   ├── implementations/    # Concrete service implementations
│   │   ├── jobs/               # Scheduled cron jobs (see jobs/README.md)
│   │   └── protocols/          # Abstract protocols (clustering, routing algorithms)
│   ├── templates/              # Email/HTML templates
│   └── utilities/              # Shared utility functions
├── scripts/                    # Developer scripts (run manually, not by CI)
├── tests/                      # Unit and functional tests
├── server.py                   # Application entry point
├── pyproject.toml              # Ruff config + project metadata
├── mypy.ini                    # mypy type checking config
├── alembic.ini                 # Alembic migration config
└── requirements.txt            # Python dependencies
```

## Architecture

**Request flow:** Router → Service (implementation) → Model → Database

- **Routers** handle HTTP concerns only (parsing requests, returning responses)
- **Services** contain business logic; each service has a protocol (interface) in `protocols/` and a concrete implementation in `implementations/`
- **Models** are SQLModel classes shared between the ORM and (where appropriate) API schemas
- **Dependencies** wire together auth, DB sessions, and services via FastAPI's `Depends()`

## Adding a New Feature

1. Define the model in `app/models/`
2. Create a migration: `docker-compose exec backend alembic revision --autogenerate -m "add_thing"`
3. Add a schema in `app/schemas/` if the API shape differs from the model
4. Add a service protocol in `app/services/protocols/` and implementation in `app/services/implementations/`
5. Wire the service in `app/dependencies/`
6. Add a router in `app/routers/` and register it in `server.py`

## Scheduled Jobs

Cron jobs live in `app/services/jobs/`. See [jobs/README.md](python/app/services/jobs/README.md) for how to create and register a new job.

## Developer Scripts

Scripts in `scripts/` are for manual local testing — not run by CI.

| Script                          | Purpose                                                              |
| ------------------------------- | -------------------------------------------------------------------- |
| `k_means_test.py`               | Run K-Means clustering against real DB locations, saves scatter plot |
| `update_firebase.py`            | Sync Firebase custom role claims to match your local DB              |
| `fetch_route_polyline_test.py`  | Test `fetch_route_polyline` with mock locations                      |
| `sweep_algorithm_test.py`       | Test the sweep clustering algorithm                                  |

```bash
docker-compose exec backend python scripts/k_means_test.py
docker-compose exec backend python scripts/update_firebase.py
docker-compose exec backend pytest scripts/fetch_route_polyline_test.py -v -s
docker-compose exec backend pytest scripts/sweep_algorithm_test.py -v -s
```

## Linting & Type Checking

```bash
docker-compose exec backend ruff check .           # lint
docker-compose exec backend ruff check --fix .     # auto-fix
docker-compose exec backend ruff format .          # format
docker-compose exec backend mypy . --config-file mypy.ini  # type check
```

## Testing

```bash
docker-compose exec backend python -m pytest
docker-compose exec backend python -m pytest tests/unit/test_models.py
docker-compose exec backend python -m pytest --cov=app
```
