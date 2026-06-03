# Contributing

## Version Control

- Branch off `main` for all feature work and bug fixes
- Use descriptive branch names in kebab-case: `username/feature-description`
- Example: `colin/user-authentication-fix`

### Integrating Changes

Use rebase instead of merge to integrate `main` changes:

```bash
git pull origin main --rebase

# If conflicts occur, resolve them and continue
git add .
git rebase --continue

git push --force-with-lease
```

## VSCode Setup

Create `.vscode/settings.json` in the project root:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  }
}
```

**Required extensions:**

- **Prettier** (`esbenp.prettier-vscode`)
- **ESLint** (`dbaeumer.vscode-eslint`)

**Recommended extensions:**

- **Tailwind CSS IntelliSense** (`bradlc.vscode-tailwindcss`)
- **TypeScript Error Translator** (`mattpocock.ts-error-translator`)

## Linting & Formatting

### Backend (Python)

```bash
# Lint
docker-compose exec backend ruff check .
docker-compose exec backend ruff check --fix .

# Format
docker-compose exec backend ruff format .

# Type checking
docker-compose exec backend mypy . --config-file mypy.ini
```

Config: `backend/python/pyproject.toml` (Ruff), `backend/python/mypy.ini` (mypy)

### Frontend (TypeScript/React)

```bash
docker-compose exec frontend pnpm lint
docker-compose exec frontend pnpm lint:fix
docker-compose exec frontend pnpm format
```

> If you run the frontend natively on Windows (see [Running the frontend on Windows](#running-the-frontend-on-windows)), the `frontend` container won't be running — run these directly from `frontend/` instead:
>
> ```bash
> pnpm lint
> pnpm lint:fix
> pnpm format
> ```

Config: `frontend/eslint.config.js`, `frontend/.prettierrc`, `frontend/tsconfig.json`

### Package Manager

This project uses **pnpm** — do not use npm or yarn, as it will break the lockfile and fail CI.

```bash
pnpm install          # install deps
pnpm add <pkg>        # add package
pnpm add -D <pkg>     # add dev dependency
pnpm remove <pkg>     # remove package
```

Always commit `pnpm-lock.yaml`.

## Running the frontend on Windows

If you're on Windows, you'll get a much faster dev loop by running the frontend
**natively** (outside Docker) using `pnpm dev`, while keeping the backend and database in Docker.
The Docker bind-mount path on Windows (host NTFS ↔ Linux container) makes Vite's
cold start very slow — we measured ~80–180 s for a single cold page load in the
container, vs **~9 s natively** on the same machine. We aren't entirely sure why
this is, but running locally is a good temporary fix.

### Setup (one time)

1. Install Node 24+ and pnpm 11+ on Windows (e.g. via [nvm-windows](https://github.com/coreybutler/nvm-windows) and `npm install -g pnpm`).
2. From `frontend/`: `pnpm install`.
3. From `frontend/`: `cp .env.example .env` (same `frontend/.env` Docker mounts via `env_file`). The default `VITE_API_BASE_URL=http://localhost:8080` points at the backend container's exposed port; override it if your backend runs elsewhere.

### Daily workflow

```bash
# Terminal 1 — backend + db only (stop or don't start the Docker frontend; it would conflict on port 3000)
docker-compose up backend db

# Terminal 2 — frontend on the host
cd frontend
pnpm dev
```

Open http://localhost:3000 as usual. The axios client defaults to
`http://localhost:8080` for the API, so it talks directly to the backend
container's exposed port (override with `VITE_API_BASE_URL` if needed).

## Testing

### Backend

```bash
docker-compose exec backend python -m pytest
docker-compose exec backend python -m pytest tests/unit/test_models.py
docker-compose exec backend python -m pytest --cov=app
```

### Developer Scripts

Scripts in `backend/python/scripts/` are for manual local use only — not run by CI.

| Script                                 | Purpose                                                                    |
| -------------------------------------- | -------------------------------------------------------------------------- |
| `scripts/k_means_test.py`              | Run K-Means clustering against real DB locations, saves scatter plot       |
| `scripts/update_firebase.py`           | Sync Firebase custom role claims to match your local database              |
| `scripts/fetch_route_polyline_test.py` | Test `fetch_route_polyline` with mock locations, prints polyline + distance |

```bash
docker-compose exec backend python scripts/k_means_test.py
docker-compose exec backend python scripts/update_firebase.py
docker-compose exec backend pytest scripts/fetch_route_polyline_test.py -v -s
```

## CI/CD

Workflows are in `.github/workflows/`.

| Workflow                  | Trigger                          | What it does                                  |
| ------------------------- | -------------------------------- | --------------------------------------------- |
| `lint.yml`                | Push/PR to `main`                | Ruff, mypy (backend); pnpm lint (frontend)    |
| `pytest.yml`              | Push/PR to `main` (backend paths) | Runs pytest against a PostgreSQL test container |
| `claude-code-review.yml`  | PR ready for review or `@claude review` comment | Automated code quality review  |

**Run CI checks locally before pushing:**

```bash
# Frontend
cd frontend && pnpm lint && pnpm build

# Backend
docker-compose exec backend ruff check .
docker-compose exec backend ruff format --check .
docker-compose exec backend mypy . --config-file mypy.ini
docker-compose exec backend pytest
```
