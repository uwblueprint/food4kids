# Food4Kids

A delivery management platform for Food4Kids, supporting admin and driver workflows.

## Tech Stack

| Layer          | Technology                                      |
| -------------- | ----------------------------------------------- |
| Frontend       | React 19, TypeScript, Vite, Tailwind CSS v4, React Router v7 |
| Backend        | Python, FastAPI, SQLModel                       |
| Database       | PostgreSQL + Alembic migrations                 |
| Auth           | Firebase Auth                                   |
| Infrastructure | Docker & Docker Compose                         |
| Package manager | pnpm                                           |

## Repo Structure

```
food4kids/
├── backend/python/
│   ├── app/
│   │   ├── dependencies/       # Dependency injection (auth, etc.)
│   │   ├── migrations/         # Alembic database migrations
│   │   ├── models/             # SQLModel database models
│   │   ├── routers/            # FastAPI route handlers
│   │   ├── schemas/            # Pydantic schemas for API
│   │   ├── services/           # Business logic layer
│   │   ├── templates/          # Email/HTML templates
│   │   └── utilities/          # Shared utility functions
│   ├── scripts/                # Developer scripts (run manually, not by CI)
│   ├── tests/                  # Unit and functional tests
│   └── server.py               # Application entry point
├── frontend/                   # React + TypeScript frontend (see frontend/README.md)
├── db-init/                    # Database initialization scripts
├── docker-compose.yml
└── README.md
```

## Setup

### Prerequisites

- [Docker Desktop](https://docs.docker.com/get-started/get-docker/) installed and running

```bash
git clone git@github.com:uwblueprint/food4kids.git
cd food4kids
```

### Environment

You need two env files: `.env` (backend) and `frontend/.env` (frontend). Never commit these files.

The backend `.env` is stored in Google Secret Manager and pulled via a script. The frontend `.env` must be obtained from the PL (a `frontend/.env.example` template is provided).

#### Pull backend `.env` via Google Secret Manager

**Prerequisites:** [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed.

**1. Get the service account credentials**

Download the `food4kids-env-service-account.json` file from the Food4Kids Developers shared Google Drive in UW Blueprint. Save it to the **repo root** (it is gitignored automatically).

**2. Authenticate with the service account**

```bash
gcloud auth activate-service-account --key-file=food4kids-env-service-account.json
```

**3. Run the pull script**

Mac/Linux:
```bash
chmod +x pull-env.sh   # only needed once
./pull-env.sh
```

Windows (Git Bash or WSL):
```bash
bash pull-env.sh
```

Windows (PowerShell, if you don't have Git Bash/WSL):
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "food4kids-env-service-account.json"
gcloud secrets versions access latest --secret="f4k-backend-env" --project="food4kids-473501" | Out-File -Encoding utf8 .env
```

This writes `.env` to the repo root. You still need `frontend/.env` from the PL.

### Run

```bash
docker-compose up --build
```

| Service  | URL                                          |
| -------- | -------------------------------------------- |
| Frontend | http://localhost:3000                        |
| Backend  | http://localhost:8080                        |
| API docs | http://localhost:8080/docs (dev only)        |

## Database

```bash
# Check migration status
docker-compose exec backend alembic current

# Generate migration after model changes
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Connect to DB
docker-compose exec db psql -U postgres -d f4k

# Seed with test data
docker-compose exec backend python -m app.seed_database
```

## API Testing

Use the interactive Swagger UI at http://localhost:8080/docs, or see the [Postman Setup Guide](https://www.notion.so/uwblueprintexecs/Postman-Setup-28410f3fb1dc80f8b1e8c414c4a21802).

## Docker Commands

```bash
docker-compose up --build       # Start with fresh build
docker-compose up -d --build    # Start in background
docker-compose down             # Stop
docker-compose down --volumes   # Stop and remove volumes
docker system prune -a --volumes  # Clean up unused resources
```

## Further Reading

- [Frontend README](frontend/README.md) — project structure, design system, TypeScript conventions
- [Backend README](backend/README.md) — architecture, adding features, scheduled jobs, developer scripts
- [CONTRIBUTING.md](CONTRIBUTING.md) — version control, linting, testing, CI/CD, VSCode setup

## FAQ & Debugging

<details>
<summary>Database connection errors</summary>

- Ensure Docker Desktop is running
- Check container health: `docker-compose ps`
- Verify `.env` values
- Try: `docker-compose down --volumes && docker-compose up --build`

</details>

<details>
<summary>"ENOSPC: no space left on device" when building containers</summary>

```bash
docker system prune -a --volumes
docker-compose up --build
```

</details>

<details>
<summary>Migration errors</summary>

- Check status: `docker-compose exec backend alembic current`
- Ensure the database is running
- Verify model changes in `app/models/`

</details>

<details>
<summary>Firebase authentication issues</summary>

- Verify Firebase config in your env files
- Ensure Firebase Admin SDK credentials are properly formatted

</details>
