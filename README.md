# Food4Kids

A delivery management platform for Food4Kids, supporting admin and driver workflows.

## Tech Stack

| Layer           | Technology                                                   |
| --------------- | ------------------------------------------------------------ |
| Frontend        | React 19, TypeScript, Vite, Tailwind CSS v4, React Router v7 |
| Backend         | Python, FastAPI, SQLModel                                    |
| Database        | PostgreSQL + Alembic migrations                              |
| Auth            | Firebase Auth                                                |
| Infrastructure  | Docker & Docker Compose                                      |
| Package manager | pnpm                                                         |

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
│   │   ├── templates/          # Email HTML (generated — see "Email Templates")
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

The backend `.env` is stored in Google Secret Manager and pulled via a script. For the frontend, copy the `frontend/.env.example` template to `frontend/.env`. It currently holds a single variable, `VITE_API_BASE_URL` (the backend API URL, defaulting to `http://localhost:8080`).

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
gcloud secrets versions access latest --secret="f4k-development-backend-env" --project="food4kids-473501" | Out-File -Encoding utf8 .env
```

This writes `.env` to the repo root. You still need `frontend/.env` from the PL.

> **If containers are already running,** re-pulling `.env` is not enough. Use `docker compose up -d --force-recreate` instead.

### Git hooks

The repo ships a pre-commit hook that keeps the frontend OpenAPI client in sync with the backend automatically — when a commit touches the API contract it regenerates `frontend/openapi.json` and `frontend/src/api/generated/` (no running backend needed) and stages the result.

**It enables itself** the first time you run `pnpm install` in `frontend/` (via a `prepare` script that points `core.hooksPath` at `scripts/git-hooks`). If you only ever run the stack through Docker and want it anyway, enable it manually once (worktrees of the same clone share it):

```bash
git config core.hooksPath scripts/git-hooks
```

To regenerate the client it needs the backend's Python deps. It finds them, in order: a host `backend/python/venv`, then a **running `f4k_backend` container** (Docker-only devs need the backend up — `docker compose up backend`), then a system `python3` that can import the deps. If none are available it **warns and skips** rather than blocking the commit — on pull requests, CI regenerates the client (`openapi.json` **and** the generated TS) and **commits the fix back to your branch automatically** (via the `f4k-openapi-sync` GitHub App), so drift can't merge even if the hook never ran. You can also force-skip the hook with `SKIP_OPENAPI_REGEN=1 git commit …`.

See [frontend/README.md](frontend/README.md#api-client-generated-from-openapi) for details.

### Run

```bash
docker-compose up --build
```

| Service  | URL                                   |
| -------- | ------------------------------------- |
| Frontend | http://localhost:3000                 |
| Backend  | http://localhost:8080                 |
| API docs | http://localhost:8080/docs (dev only) |

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

# Seed with test data (needs app/data/locations.csv from our Google Drive)
docker-compose exec backend python -m app.seed_database

# ...and restore every seed account's password, if one has drifted.
# Signs out everyone currently logged in, so it is opt-in.
docker-compose exec backend python -m app.seed_database --reset-passwords
```

Seeding leaves existing Firebase accounts' passwords alone. Writing a password
moves the account's `tokensValidAfterTime`, which revokes every token already
issued — so an unconditional rewrite signed out every open session, local and
otherwise, on each run.

## Creating an admin account

There is no in-app way to make someone an admin — an existing admin cannot
invite another one. A Blueprint developer with database access runs a CLI, which
prints a link; the F4K staff member opens that link and sets their own password.
The CLI never sees or prints a password.

```bash
# Locally
docker-compose exec backend python -m app.create_admin \
  --email jane@food4kids.ca --name "Jane Doe" --phone "519-576-3443"
```

It prints something like:

```
Created admin account for jane@food4kids.ca.
Send them this link to set their password:

    https://app.food4kids.example/create-password/6f1c…-…-…

The link is single-use and expires in 48 hours.
```

Send that link to the person. It opens the same **Create a password** page that
invited drivers use; submitting it calls `POST /auth/register`, which creates
their Firebase account, stamps the `role: admin` custom claim on it, and fills
in `users.auth_id`.

**Both halves matter.** Authorization reads the Firebase custom claim, never
`users.role` — see `require_authorization_by_role` in
`backend/python/app/dependencies/auth.py`. Until the link is used, the row in
`users` says `admin` but the person can do nothing, because there is no Firebase
account yet. So an admin isn't real until they've followed the link.

Notes for whoever runs this:

- **It is not `seed_database`.** `python -m app.seed_database` starts by
  `DELETE`-ing every table. `create_admin` inserts three rows (`users`,
  `admin_info`, `user_invites`) in one transaction and touches nothing else.
- **Set `FRONTEND_BASE_URL`** in the backend environment before running it
  against a deployed database, or the link it prints will point at
  `http://localhost:3000`. The URL is printed in full, so check it before
  sending.
- **The email must be unused.** `users.email` is unique across drivers and
  admins alike; the CLI refuses up front rather than writing a partial account.
- **48 hours.** If the link lapses, delete the unfinished user row and run the
  CLI again.
- **Running against production**: exec into the deployed backend the same way,
  with `APP_ENV=production` and `DATABASE_URL` set — the CLI reuses the app's
  own connection setup, so if the backend can reach the database, so can it.

## API Testing

Use the interactive Swagger UI at http://localhost:8080/docs, or see the [Postman Setup Guide](https://www.notion.so/uwblueprintexecs/Postman-Setup-28410f3fb1dc80f8b1e8c414c4a21802).

The frontend consumes the API through a TypeScript client generated from FastAPI's OpenAPI schema. After making backend route or schema changes, regenerate with `pnpm generate:api` from `frontend/`. See [frontend/README.md](frontend/README.md#api-client-generated-from-openapi) for details.

## Email Templates

The emails are written as React Email components in `frontend/emails/*.tsx` — **that is the only place to edit them.** The HTML under `frontend/emails/html/` and `backend/python/app/templates/` is generated output; hand-editing either copy gets overwritten by the next export.

Placeholders are rendered as literal `{{ Name }}` text by the sources, so Jinja2 substitutes them at send time. The name of every placeholder is declared in `backend/python/app/constants/email_config.py` as that email's `required_context`, and `backend/python/tests/test_email_template_placeholders.py` fails if the two ever disagree.

After changing a template, regenerate both copies with one command from the repo root:

```bash
./scripts/sync-email-templates.sh
```

Commit both directories together; CI fails if they drift. To preview while editing, run `pnpm run email:dev` from `frontend/`.

## Docker Commands

```bash
docker-compose up --build       # Start with fresh build
docker-compose up -d --build    # Start in background
docker-compose down             # Stop
docker-compose down --volumes   # Stop and remove volumes
docker system prune -a --volumes  # Clean up unused resources
docker compose down && docker volume rm food4kids_frontend_node_modules; docker compose build --no-cache frontend && docker compose up -d #regenerate pnpm
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
<summary>db container exits: "database files are incompatible with server"</summary>

```
FATAL:  database files are incompatible with server
DETAIL: The data directory was initialized by PostgreSQL version 12,
        which is not compatible with this version 17.x
```

Your `postgres_data` volume predates the Postgres 12 → 17 upgrade (#177). Postgres will not
start on a data directory from an older major version, and the backend fails with it because
it waits on `db` being healthy.

The volume has to be recreated. **This destroys your local dev database**, which is fine if
it is just seed data — back it up first if not.

```bash
docker compose down
docker volume rm food4kids_postgres_data
docker compose up -d
docker compose exec backend alembic upgrade head
# then re-seed (see Database above)
```

</details>

<details>
<summary>`GET /billing/costs` returns 503</summary>

Re-pull secrets (they were updated August 19, 2026).

</details>

<details>
<summary>Frontend loads a blank page / "Failed to resolve import"</summary>

Vite logs something like `Failed to resolve import "zustand" from "src/api/authStore.ts"`
and the page renders empty. The `frontend_node_modules` volume is stale — it persists across
rebuilds, so dependencies added since you last installed are missing.

```bash
docker compose exec -e CI=true frontend pnpm install
docker compose restart frontend
```

`CI=true` matters: without it pnpm prompts "The modules directory will be removed and
reinstalled from scratch. Proceed?" and hangs, because `exec` has no interactive stdin.

</details>

<details>
<summary>Firebase authentication issues</summary>

- Verify Firebase config in your env files
- Ensure Firebase Admin SDK credentials are properly formatted
</details>
