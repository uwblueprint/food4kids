# Food4Kids

## Table of Contents

- [Tech Stack](#tech-stack)
- [Repo Structure](#repo-structure)
- [Development Setup](#development-setup)
- [Application Execution](#application-execution)
- [API Testing with Postman](#api-testing-with-postman)
- [Database Interactions](#database-interactions)
- [Version Control Guide](#version-control-guide)
  - [Branching](#branching)
  - [Docker Commands](#docker-commands)
- [Formatting and Linting](#formatting-and-linting)
- [Testing](#testing)
- [FAQ & Debugging](#faq--debugging)
- [Polyline Model Testing Guide](#polyline-model-testing-guide) 🚀 **NEW**

---

## Tech Stack

**Frontend:** React, TypeScript
**Backend:** Python, FastAPI, SQLModel
**Database:** PostgreSQL
**Authentication:** Firebase Auth
**Containerization:** Docker & Docker Compose

---

## Repo Structure

```
food4kids/
├── backend/
│   └── python/
│       ├── app/
│       │   ├── dependencies/       # Dependency injection (auth, etc.)
│       │   ├── migrations/         # Alembic database migrations
│       │   ├── models/             # SQLModel database models
│       │   ├── routers/            # FastAPI route handlers
│       │   ├── schemas/            # Pydantic schemas for API
│       │   ├── services/           # Business logic layer
│       │   │   ├── implementations/ # Concrete service implementations
│       │   │   └── interfaces/     # Service interfaces
│       │   ├── templates/          # Email/HTML templates
│       │   └── utilities/          # Shared utility functions
│       ├── tests/                  # Unit and functional tests
│       ├── alembic.ini            # Alembic configuration
│       ├── requirements.txt       # Python dependencies
│       └── server.py              # Application entry point
├── frontend/                      # Frontend (TBD)
├── db-init/                       # Database initialization scripts
├── docker-compose.yml             # Multi-container Docker setup
└── README.md
```

---

## Development Setup

### Prerequisites

- Install [Docker Desktop](https://docs.docker.com/get-started/get-docker/) and ensure it's running
- Clone this repository:

```bash
git clone git@github.com:uwblueprint/food4kids.git
cd food4kids
```

### Environment Configuration

You will need to create environment files: `.env` and `frontend/.env`. Talk to the PL to obtain these.

### Installation

Build and start all services using Docker Compose:

```bash
docker-compose up --build
```

This will start:

- **Frontend**: React development server on port 3000
- **Backend**: FastAPI server on port 8080
- **Database**: PostgreSQL on port 5432

---

## Application Execution

```bash
# Start all services
docker-compose up --build

# Start in detached mode (background)
docker-compose up -d --build
```

**Access Points:**

- Frontend: http://localhost:3000
- Backend API: http://localhost:8080
- API Documentation: http://localhost:8080/docs (development only)
- ReDoc Documentation: http://localhost:8080/redoc (development only)

---
## API Testing with Postman

Postman is a powerful tool for testing API endpoints during development. For detailed setup instructions and best practices, see our [Postman Setup Guide](https://www.notion.so/uwblueprintexecs/Postman-Setup-28410f3fb1dc80f8b1e8c414c4a21802?source=copy_link).

**Quick Start:**

1. Ensure the backend container is running (`docker-compose up`)
2. Import the Postman collection (if available) or manually configure requests
3. Set the base URL to `http://localhost:8080`
4. Configure authentication headers as needed (see the Notion guide for details)

**Alternative:** You can also test endpoints using the interactive Swagger UI at http://localhost:8080/docs

## Database Interactions

### Migration Commands

The project uses Alembic for database migrations. All commands run from the project root:

```bash
# Check current migration status
docker-compose exec backend alembic current

# Generate new migration (auto-detect model changes)
docker-compose exec backend alembic revision --autogenerate -m "description_of_changes"

# Apply pending migrations
docker-compose exec backend alembic upgrade head

# Check if database schema matches models
docker-compose exec backend alembic check

# View migration history
docker-compose exec backend alembic history
```

### Direct Database Access

```bash
# Connect to development database
docker-compose exec db psql -U postgres -d f4k

# Connect to test database
docker-compose exec db psql -U postgres -d f4k_test

# Once inside the DB, try these common PostgreSQL commands:
\dt          # List all tables
\d table_name # Describe table structure
\q           # Quit
SELECT * FROM users; # Run SQL queries
```

### Database Seeding

```bash
# Populate database with randomized test data
docker-compose exec backend python app/seed_database.py
```

---

## Version Control Guide

### Branching

- Branch off `main` for all feature work and bug fixes
- Use descriptive branch names in kebab-case: `username/feature-description`
- Example: `colin/user-authentication-fix`

### Integrating Changes

Use rebase instead of merge to integrate `main` changes:

```bash
# Update feature branch with main changes
git pull origin main --rebase

# If conflicts occur, resolve them and continue
git add .
git rebase --continue

# Force push to remote feature branch
git push --force-with-lease
```

### Docker Commands

```bash
# Build images
docker-compose build

# Start containers (builds if needed)
docker-compose up

# Start with fresh build
docker-compose up --build

# Stop containers
docker-compose down

# Stop containers and remove volumes
docker-compose down --volumes

# View running containers
docker ps

# Clean up unused Docker resources
docker system prune -a --volumes
```

---

## Formatting and Linting

### Backend (Python)

The project uses **Ruff** for Python linting and formatting, and **mypy** for static type checking:

#### Ruff (Linting & Formatting)

```bash
# Check for linting issues
docker-compose exec backend ruff check .

# Auto-fix linting issues
docker-compose exec backend ruff check --fix .

# Format code
docker-compose exec backend ruff format .

# Check formatting without making changes
docker-compose exec backend ruff format --check .
```

#### mypy (Static Type Checking)

```bash
# Run type checking
docker-compose exec backend mypy .
```

#### Combined Quality Checks

```bash
# Run all quality checks (linting, formatting, type checking)
docker-compose exec backend ruff check . && docker-compose exec backend ruff format --check . && docker-compose exec backend mypy .
```

**Configuration Files:**

- Ruff: `backend/python/pyproject.toml` (under `[tool.ruff]`)
- mypy: `backend/python/mypy.ini`

### Frontend (TypeScript/React)

```bash
# Check linting issues
docker-compose exec frontend npm run lint

# Auto-fix linting issues
docker-compose exec frontend npm run fix

# Combined format and lint (when available)
docker-compose exec frontend npm run format
```

---

## Testing

### Backend Tests

```bash
# Run all backend tests
docker-compose exec backend python -m pytest

# Run specific test file
docker-compose exec backend python -m pytest tests/unit/test_models.py

# Run with coverage
docker-compose exec backend python -m pytest --cov=app
```

### Frontend Tests

```bash
# Run frontend tests
docker-compose exec frontend npm test

# Run tests in CI mode
docker-compose exec frontend npm test -- --ci --coverage --watchAll=false
```

_Note: CI/CD pipeline for automated testing will be added in future updates._

---

## FAQ & Debugging

<details>
<summary>How do I test API endpoints?</summary>

- Ensure the backend container is running
- Visit http://localhost:8080/docs for interactive API documentation
- Use the "Authorize" button to add your Firebase auth token
- Test endpoints in Postman or directly in the Swagger UI

**OR**

Use curl for command-line testing (see [Polyline Testing Guide](#polyline-model-testing-guide) below)

</details>

<details>
<summary>Database connection errors</summary>

- Ensure Docker Desktop is running
- Check that the database container is healthy: `docker-compose ps`
- Verify environment variables in `.env` file
- Try rebuilding containers: `docker-compose down --volumes && docker-compose up --build`

</details>

<details>
<summary>"ENOSPC: no space left on device" when building containers</summary>

Clean up Docker resources:

```bash
docker system prune -a --volumes
docker-compose up --build
```

</details>

<details>
<summary>Migration errors</summary>

- Check current migration status: `docker-compose exec backend alembic current`
- Ensure database is running and accessible
- Verify model changes are properly defined in `app/models/`
- For migration conflicts, you may need to manually resolve in the database

</details>

<details>
<summary>Firebase authentication issues</summary>

- Verify Firebase configuration in environment files
- Check that Firebase project settings match your configuration
- Ensure Firebase Admin SDK credentials are properly formatted

</details>

---

## Polyline Model Testing Guide {#polyline-model-testing-guide}

### Table of Contents
1. [What is curl and why use it over Swagger?](#what-is-curl)
2. [Side-by-Side: curl vs Swagger](#curl-vs-swagger)
3. [Ticket Requirements Validation](#ticket-validation)
4. [Complete curl Test Suite](#test-suite)

---

### What is curl? {#what-is-curl}

**curl** (Client URL) is a command-line tool that makes HTTP requests. Think of it as a way to talk to APIs directly from your terminal.

#### Why use curl instead of Swagger UI?

| Feature | curl | Swagger UI |
|---------|------|------------|
| **Automation** | ✅ Easy to script and automate | ❌ Manual clicking required |
| **CI/CD Integration** | ✅ Works in pipelines | ❌ Requires manual intervention |
| **Repeatability** | ✅ Re-run exact same commands | ❌ Easy to forget steps |
| **Output Parsing** | ✅ Pipe to jq, grep, etc. | ❌ Manual copy/paste |
| **Efficiency** | ✅ Batch operations | ❌ Click, wait, click, wait... |
| **Documentation** | ✅ Commands can be saved as docs | ❌ Hard to document UI actions |
| **Speed** | ✅ No browser overhead | ❌ UI rendering overhead |

**Bottom line:** Swagger is great for exploration and learning. curl is better for testing, automation, and validation.

---

### Side-by-Side: curl vs Swagger {#curl-vs-swagger}

#### Example 1: Create a Polyline

**Using curl:**
```bash
curl -X 'POST' \
  'http://localhost:8080/polylines/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "route_id": "550e8400-e29b-41d4-a716-446655440000",
    "encoded_polyline": "test-polyline-data",
    "expires_at": "2025-12-31T23:59:59"
  }'
```

**Using Swagger:**
1. Open http://localhost:8080/docs
2. Navigate to "polylines" section
3. Click "POST /polylines/"
4. Click "Try it out"
5. Fill in JSON body:
   ```json
   {
     "route_id": "550e8400-e29b-41d4-a716-446655440000",
     "encoded_polyline": "test-polyline-data",
     "expires_at": "2025-12-31T23:59:59"
   }
   ```
6. Click "Execute"

**Result:** Identical API call, curl is faster and scriptable!

#### Example 2: Get All Polylines

**Using curl:**
```bash
curl -X 'GET' 'http://localhost:8080/polylines/' -H 'accept: application/json'
```

**Using Swagger:**
1. Click "GET /polylines/"
2. Click "Try it out"
3. Click "Execute"

---

### Ticket Requirements Validation {#ticket-validation}

#### Original Ticket (Reviewer: Eddy)

> **Requirement 1:** Create a new model to store the compressed polyline data (should be a string)

✅ **VERIFIED:** The `polylines` table has `encoded_polyline` column (VARCHAR, 10000 chars)

> **Requirement 2:** Keep track of the time at which the polyline will expire as another field

✅ **VERIFIED:** The `polylines` table has `expires_at` column (TIMESTAMP WITH TIME ZONE)

> **Requirement 3:** Could make a new table/model so that we can delete entries a bit easier when they expire (just delete from polyline table where time < expiry time)

✅ **VERIFIED:** Separate `polylines` table allows clean DELETE operations

> **Requirement 4:** Keep the routes table small and quick to query

✅ **VERIFIED:** Polyline data stored separately in `polylines` table, not in `routes`

> **Requirement 5:** Add a reference to this table in the routes model (foreign key)

✅ **VERIFIED:** Foreign key constraint `fk_polylines_route_id` exists

---

### Complete curl Test Suite {#test-suite}

#### Prerequisites

**⚠️ IMPORTANT: Run these commands with backend and database running**

**Step 1: Setup a test route**
```bash
# Insert a test route (required for foreign key)
docker exec f4k_db psql -U postgres -d f4k \
  -c "INSERT INTO routes (route_id, name, notes, length, created_at, updated_at) VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Test Route', 'Route for testing polylines', 10.5, NOW(), NOW());"

# Verify it was created
docker exec f4k_db psql -U postgres -d f4k \
  -c "SELECT route_id, name FROM routes WHERE route_id = '550e8400-e29b-41d4-a716-446655440000';"
```

**Expected Output:**
```
              route_id               |   name
-------------------------------------+----------
 550e8400-e29b-41d4-a716-446655440000 | Test Route
(1 row)
```

---

#### TEST 1: Create Polyline (Requirement: Store compressed polyline as string)

**Command:**
```bash
curl -X 'POST' \
  'http://localhost:8080/polylines/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "route_id": "550e8400-e29b-41d4-a716-446655440000",
    "encoded_polyline": "sample-polyline-string-abc123"
  }'
```

**Expected Output:**
```json
{
  "route_id": "550e8400-e29b-41d4-a716-446655440000",
  "encoded_polyline": "sample-polyline-string-abc123",
  "expires_at": null,
  "polyline_id": "[GENERATED_UUID]"
}
```

**What it means:**
- ✅ Polyline created successfully
- ✅ Server generated unique `polyline_id`
- ✅ String data stored correctly

**Swagger Equivalent:**
- Navigate to POST /polylines/
- Body: `{"route_id": "...", "encoded_polyline": "sample-polyline-string-abc123"}`
- Click Execute

---

#### TEST 2: Create Polyline with Expiry (Requirement: Track expiry time)

**Command:**
```bash
curl -X 'POST' \
  'http://localhost:8080/polylines/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "route_id": "550e8400-e29b-41d4-a716-446655440000",
    "encoded_polyline": "polyline-with-expiry",
    "expires_at": "2025-12-31T23:59:59"
  }'
```

**Expected Output:**
```json
{
  "route_id": "550e8400-e29b-41d4-a716-446655440000",
  "encoded_polyline": "polyline-with-expiry",
  "expires_at": "2025-12-31T23:59:59Z",
  "polyline_id": "[GENERATED_UUID]"
}
```

**What it means:**
- ✅ Expiry date stored correctly
- ✅ Timezone added automatically (Z = UTC)

**Swagger Equivalent:**
- Navigate to POST /polylines/
- Body: `{"route_id": "...", "encoded_polyline": "polyline-with-expiry", "expires_at": "2025-12-31T23:59:59"}`
- Click Execute

---

#### TEST 3: Get All Polylines (Verify data exists)

**Command:**
```bash
curl -X 'GET' \
  'http://localhost:8080/polylines/' \
  -H 'accept: application/json'
```

**Expected Output:**
```json
[
  {
    "route_id": "550e8400-e29b-41d4-a716-446655440000",
    "encoded_polyline": "sample-polyline-string-abc123",
    "expires_at": null,
    "polyline_id": "[UUID_FROM_TEST_1]"
  },
  {
    "route_id": "550e8400-e29b-41d4-a716-446655440000",
    "encoded_polyline": "polyline-with-expiry",
    "expires_at": "2025-12-31T23:59:59Z",
    "polyline_id": "[UUID_FROM_TEST_2]"
  }
]
```

**What it means:**
- ✅ Both polylines retrieved
- ✅ Array format (multiple results)
- ✅ All fields present

**Swagger Equivalent:**
- Navigate to GET /polylines/
- Click Execute

---

#### TEST 4: Get Polylines by Route (Verify foreign key relationship)

**Command:**
```bash
curl -X 'GET' \
  'http://localhost:8080/polylines/route/550e8400-e29b-41d4-a716-446655440000' \
  -H 'accept: application/json'
```

**Expected Output:**
```json
[
  {
    "route_id": "550e8400-e29b-41d4-a716-446655440000",
    "encoded_polyline": "sample-polyline-string-abc123",
    "expires_at": null,
    "polyline_id": "[UUID_FROM_TEST_1]"
  },
  {
    "route_id": "550e8400-e29b-41d4-a716-446655440000",
    "encoded_polyline": "polyline-with-expiry",
    "expires_at": "2025-12-31T23:59:59Z",
    "polyline_id": "[UUID_FROM_TEST_2]"
  }
]
```

**What it means:**
- ✅ Foreign key relationship working
- ✅ Can query polylines by route_id
- ✅ Returns all polylines for specific route

**Swagger Equivalent:**
- Navigate to GET /polylines/route/{route_id}
- Parameter: route_id = `550e8400-e29b-41d4-a716-446655440000`
- Click Execute

---

#### TEST 5: Get Specific Polyline by ID

**Command:**
```bash
curl -X 'GET' \
  'http://localhost:8080/polylines/[POLYLINE_ID_FROM_TEST_1]' \
  -H 'accept: application/json'
```

**Expected Output:**
```json
{
  "route_id": "550e8400-e29b-41d4-a716-446655440000",
  "encoded_polyline": "sample-polyline-string-abc123",
  "expires_at": null,
  "polyline_id": "[SAME_UUID_AS_TEST_1]"
}
```

**What it means:**
- ✅ Can retrieve single polyline by ID
- ✅ Returns exact match

**Swagger Equivalent:**
- Navigate to GET /polylines/{polyline_id}
- Parameter: polyline_id = `[UUID]`
- Click Execute

---

#### TEST 6: Create Expired Polyline (Requirement: Expiry logic)

**Command:**
```bash
curl -X 'POST' \
  'http://localhost:8080/polylines/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "route_id": "550e8400-e29b-41d4-a716-446655440000",
    "encoded_polyline": "expired-polyline-data",
    "expires_at": "2020-01-01T00:00:00"
  }'
```

**Expected Output:**
```json
{
  "route_id": "550e8400-e29b-41d4-a716-446655440000",
  "encoded_polyline": "expired-polyline-data",
  "expires_at": "2020-01-01T00:00:00Z",
  "polyline_id": "[GENERATED_UUID]"
}
```

**What it means:**
- ✅ Expired polyline created
- ✅ Expiry date in the past (2020)

**Swagger Equivalent:**
- Navigate to POST /polylines/
- Body: `{"route_id": "...", "encoded_polyline": "expired-polyline-data", "expires_at": "2020-01-01T00:00:00"}`
- Click Execute

---

#### TEST 7: Get Expired Polylines (Requirement: Query expired entries)

**Command:**
```bash
curl -X 'GET' \
  'http://localhost:8080/polylines/expired' \
  -H 'accept: application/json'
```

**Expected Output:**
```json
[
  {
    "route_id": "550e8400-e29b-41d4-a716-446655440000",
    "encoded_polyline": "expired-polyline-data",
    "expires_at": "2020-01-01T00:00:00Z",
    "polyline_id": "[UUID_FROM_TEST_6]"
  }
]
```

**What it means:**
- ✅ Can query for expired polylines
- ✅ Finds entries where expires_at < NOW()
- ✅ Essential for cleanup operations

**Swagger Equivalent:**
- Navigate to GET /polylines/expired
- Click Execute

---

#### TEST 8: Delete Expired Polylines (Requirement: Easy deletion)

**Command:**
```bash
curl -X 'POST' \
  'http://localhost:8080/polylines/cleanup-expired' \
  -H 'accept: application/json'
```

**Expected Output:**
```bash
(no output - HTTP 204 No Content)
```

**Verify Deletion:**
```bash
curl -X 'GET' 'http://localhost:8080/polylines/expired' -H 'accept: application/json'
```

**Expected Output:**
```json
[]
```

**What it means:**
- ✅ Deleted all polylines where expires_at < NOW()
- ✅ Expired polylines removed from database
- ✅ Achieves ticket goal: "just delete from polyline table where time < expiry time"

**Database Verification:**
```bash
docker exec f4k_db psql -U postgres -d f4k \
  -c "SELECT COUNT(*) as remaining_polylines FROM polylines;"
```

**Expected Output:**
```
 remaining_polylines
--------------------
                  2
```

**Swagger Equivalent:**
- Navigate to POST /polylines/cleanup-expired
- Click Execute
- Then navigate to GET /polylines/expired and Execute to verify

---

#### TEST 9: Verify Foreign Key Constraint (Requirement: FK reference)

**Command:**
```bash
curl -X 'POST' \
  'http://localhost:8080/polylines/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "route_id": "00000000-0000-0000-0000-000000000000",
    "encoded_polyline": "invalid-route-test"
  }'
```

**Expected Output:**
```json
{
  "detail": "Internal Server Error"
}
```

**Backend Logs:**
```bash
docker logs f4k_backend --tail 30 | grep -A 5 "ForeignKeyViolation"
```

**Expected Output:**
```
sqlalchemy.exc.IntegrityError: (sqlalchemy.dialects.postgresql.asyncpg.IntegrityError)
<class 'asyncpg.exceptions.ForeignKeyViolationError'>: insert or update on table "polylines"
violates foreign key constraint "fk_polylines_route_id"

DETAIL: Key (route_id)=(00000000-0000-0000-0000-000000000000)
is not present in table "routes".
```

**What it means:**
- ✅ Foreign key constraint enforced at database level
- ✅ Cannot insert polyline with invalid route_id
- ✅ Maintains referential integrity

**Swagger Equivalent:**
- Navigate to POST /polylines/
- Body: `{"route_id": "00000000-0000-0000-0000-000000000000", "encoded_polyline": "invalid-route-test"}`
- Click Execute

---

#### TEST 10: Update Polyline

**Command:**
```bash
curl -X 'PUT' \
  'http://localhost:8080/polylines/[POLYLINE_ID_FROM_TEST_1]' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "encoded_polyline": "updated-polyline-data",
    "expires_at": "2026-01-01T00:00:00"
  }'
```

**Expected Output:**
```json
{
  "route_id": "550e8400-e29b-41d4-a716-446655440000",
  "encoded_polyline": "updated-polyline-data",
  "expires_at": "2026-01-01T00:00:00Z",
  "polyline_id": "[SAME_UUID_AS_TEST_1]"
}
```

**What it means:**
- ✅ Can modify polyline data
- ✅ Can add/change expiry date
- ✅ All fields update correctly

**Swagger Equivalent:**
- Navigate to PUT /polylines/{polyline_id}
- Parameter: polyline_id = `[UUID]`
- Body: `{"encoded_polyline": "updated-polyline-data", "expires_at": "2026-01-01T00:00:00"}`
- Click Execute

---

#### TEST 11: Delete Specific Polyline

**Command:**
```bash
curl -X 'DELETE' \
  'http://localhost:8080/polylines/[POLYLINE_ID_FROM_TEST_2]' \
  -H 'accept: application/json'
```

**Expected Output:**
```bash
(no output - HTTP 204 No Content)
```

**Verify Deletion:**
```bash
curl -X 'GET' 'http://localhost:8080/polylines/' -H 'accept: application/json'
```

**Expected Output:**
```json
[
  {
    "route_id": "550e8400-e29b-41d4-a716-446655440000",
    "encoded_polyline": "updated-polyline-data",
    "expires_at": "2026-01-01T00:00:00Z",
    "polyline_id": "[UUID_FROM_TEST_1]"
  }
]
```

**What it means:**
- ✅ Single polyline deleted by ID
- ✅ Only 1 polyline remains
- ✅ Deletion doesn't affect other polylines

**Swagger Equivalent:**
- Navigate to DELETE /polylines/{polyline_id}
- Parameter: polyline_id = `[UUID]`
- Click Execute

---

#### TEST 12: Verify Routes Table Stays Small (Requirement: Keep routes table quick to query)

**Command:**
```bash
docker exec f4k_db psql -U postgres -d f4k \
  -c "\d routes"
```

**Expected Output:**
```
              Table "public.routes"
       Column      |           Type           | Collation | Nullable | Default
------------------+--------------------------+-----------+----------+---------
 route_id         | uuid                     |           | not null |
 created_at       | timestamp with time zone |           |          |
 updated_at       | timestamp with time zone |           |          |
 name             | character varying(255)   |           | not null |
 notes            | character varying(1000)  |           |          |
 length           | double precision         |           | not null |
Indexes:
    "routes_pkey" PRIMARY KEY, btree (route_id)
```

**What it means:**
- ✅ routes table has NO polyline columns
- ✅ No large data fields (encoded_polyline up to 10,000 chars)
- ✅ Querying routes remains fast

**Compare:**
```
routes table: ~5 columns
polylines table: 6 columns (including large encoded_polyline field)
```

**Verification:**
```bash
docker exec f4k_db psql -U postgres -d f4k \
  -c "SELECT table_name,
              pg_size_pretty(pg_total_relation_size(table_name::regclass)) as size
       FROM information_schema.tables
       WHERE table_name IN ('routes', 'polylines');"
```

**Expected Output:**
```
 table_name | size
------------+-------
 polylines  | [varies with data]
 routes     | [minimal, no polyline data]
```

---

#### TEST 13: Verify Database Schema (All Requirements)

**Command:**
```bash
docker exec f4k_db psql -U postgres -d f4k \
  -c "\d polylines"
```

**Expected Output:**
```
                           Table "public.polylines"
      Column      |           Type           | Collation | Nullable | Default
------------------+--------------------------+-----------+----------+---------
 created_at       | timestamp with time zone |           |          |
 updated_at       | timestamp with time zone |           |          |
 route_id         | uuid                     |           | not null |  ← FK to routes
 encoded_polyline | character varying(10000) |           | not null |  ← String data
 expires_at       | timestamp with time zone |           |          |  ← Expiry tracking
 polyline_id      | uuid                     |           | not null |
Indexes:
    "polylines_pkey" PRIMARY KEY, btree (polyline_id)
    "ix_polylines_route_id" btree (route_id)
Foreign-key constraints:
    "fk_polylines_route_id" FOREIGN KEY (route_id) REFERENCES routes(route_id)  ← FK constraint
```

**What it means:**
- ✅ All ticket requirements met
- ✅ Correct column types
- ✅ Foreign key constraint present
- ✅ Indexes for performance

---

### How to Validate Everything Works

#### Step 1: Initialize Test Environment
```bash
# Ensure backend and db are running
docker-compose ps

# Create test route
docker exec f4k_db psql -U postgres -d f4k \
  -c "INSERT INTO routes (route_id, name, notes, length, created_at, updated_at) VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Test Route', 'Route for testing polylines', 10.5, NOW(), NOW()) ON CONFLICT (route_id) DO NOTHING;"
```

#### Step 2: Run Complete Test Suite
```bash
# TEST 1: Create polyline (save the returned UUID for next tests)
curl -X 'POST' 'http://localhost:8080/polylines/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"route_id": "550e8400-e29b-41d4-a716-446655440000", "encoded_polyline": "test-polyline-1"}'

# TEST 2: Get all polylines
curl -X 'GET' 'http://localhost:8080/polylines/' -H 'accept: application/json'

# TEST 3: Get by route ID
curl -X 'GET' 'http://localhost:8080/polylines/route/550e8400-e29b-41d4-a716-446655440000' \
  -H 'accept: application/json'

# TEST 4: Create expired polyline
curl -X 'POST' 'http://localhost:8080/polylines/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"route_id": "550e8400-e29b-41d4-a716-446655440000", "encoded_polyline": "expired-data", "expires_at": "2020-01-01T00:00:00"}'

# TEST 5: Get expired polylines
curl -X 'GET' 'http://localhost:8080/polylines/expired' -H 'accept: application/json'

# TEST 6: Cleanup expired
curl -X 'POST' 'http://localhost:8080/polylines/cleanup-expired' -H 'accept: application/json'

# TEST 7: Verify cleanup
curl -X 'GET' 'http://localhost:8080/polylines/expired' -H 'accept: application/json'
```

#### Step 3: Check Backend Logs
```bash
# Watch real-time logs
docker logs -f f4k_backend

# Or check recent logs
docker logs f4k_backend --tail 50 | grep -E "INSERT|UPDATE|DELETE|COMMIT"
```

**Good signs:**
```
INFO - COMMIT  ← Data was saved
INFO - DELETE FROM polylines WHERE polylines.expires_at <  ← Cleanup query
```

**Normal (read-only):**
```
INFO - ROLLBACK  ← Just reading data, no changes
```

#### Step 4: Verify in Database
```bash
# Direct SQL verification
docker exec f4k_db psql -U postgres -d f4k -c "SELECT * FROM polylines;"

# Check foreign key relationship
docker exec f4k_db psql -U postgres -d f4k \
  -c "SELECT r.name, COUNT(p.polyline_id) as polyline_count
       FROM routes r
       LEFT JOIN polylines p ON r.route_id = p.route_id
       GROUP BY r.route_id, r.name;"
```

#### Step 5: Verify Schema
```bash
# Check table structure
docker exec f4k_db psql -U postgres -d f4k -c "\d polylines"

# Check foreign key
docker exec f4k_db psql -U postgres -d f4k \
  -c "SELECT conname, contype, confrelid::regclass
       FROM pg_constraint
       WHERE conrelid = 'polylines'::regclass AND contype = 'f';"
```

---

### Complete Test Flow Example

#### Full Integration Test

**Step 1: Create test data**
```bash
# Create route (if needed)
docker exec f4k_db psql -U postgres -d f4k \
  -c "INSERT INTO routes (route_id, name, notes, length, created_at, updated_at) VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Test Route', 'Route for testing', 10.5, NOW(), NOW()) ON CONFLICT (route_id) DO NOTHING;"

# Create multiple polylines with different expiry dates
curl -s -X POST http://localhost:8080/polylines/ \
  -H "Content-Type: application/json" \
  -d '{"route_id":"550e8400-e29b-41d4-a716-446655440000","encoded_polyline":"active-polyline-1","expires_at":null}'

curl -s -X POST http://localhost:8080/polylines/ \
  -H "Content-Type: application/json" \
  -d '{"route_id":"550e8400-e29b-41d4-a716-446655440000","encoded_polyline":"expired-polyline-1","expires_at":"2020-01-01T00:00:00"}'

curl -s -X POST http://localhost:8080/polylines/ \
  -H "Content-Type: application/json" \
  -d '{"route_id":"550e8400-e29b-41d4-a716-446655440000","encoded_polyline":"expired-polyline-2","expires_at":"2020-01-01T00:00:00"}'

curl -s -X POST http://localhost:8080/polylines/ \
  -H "Content-Type: application/json" \
  -d '{"route_id":"550e8400-e29b-41d4-a716-446655440000","encoded_polyline":"future-polyline-1","expires_at":"2030-01-01T00:00:00"}'
```

**Step 2: Verify data**
```bash
curl -s http://localhost:8080/polylines/ | jq '. | length'
# Expected: 4 polylines

curl -s http://localhost:8080/polylines/expired | jq '. | length'
# Expected: 2 expired

curl -s http://localhost:8080/polylines/route/550e8400-e29b-41d4-a716-446655440000 | jq '. | length'
# Expected: 4 (all belong to our test route)
```

**Step 3: Execute cleanup (ticket requirement)**
```bash
curl -s -X POST http://localhost:8080/polylines/cleanup-expired
# Expected: HTTP 204

curl -s http://localhost:8080/polylines/ | jq '. | length'
# Expected: 2 (only active + future expiry remain)

curl -s http://localhost:8080/polylines/expired | jq '. | length'
# Expected: 0 (all expired deleted)
```

**Step 4: Database verification**
```bash
docker exec f4k_db psql -U postgres -d f4k \
  -c "SELECT encoded_polyline, expires_at FROM polylines ORDER BY created_at;"
```

**Expected Output:**
```
   encoded_polyline    |       expires_at
-----------------------+------------------------
 active-polyline-1     |
 future-polyline-1     | 2030-01-01 00:00:00+00
(2 rows)
```

**Step 5: Verify routes table unchanged**
```bash
docker exec f4k_db psql -U postgres -d f4k -c "SELECT COUNT(*) FROM routes WHERE route_id = '550e8400-e29b-41d4-a716-446655440000';"
docker exec f4k_db psql -U postgres -d f4k -c "\d routes | grep -c encoded"
# Expected: 0 (no polyline data in routes table)
```

---

### Summary of Ticket Validation

| Requirement | Validation Method | Status |
|-------------|------------------|--------|
| ✅ New model for polyline string data | `\d polylines` shows `encoded_polyline` column | PASS |
| ✅ Track expiry time | `\d polylines` shows `expires_at` column | PASS |
| ✅ Separate table for easy deletion | DELETE via `/cleanup-expired` endpoint works | PASS |
| ✅ Keep routes table small | `\d routes` has no polyline columns | PASS |
| ✅ Foreign key reference | FK constraint `fk_polylines_route_id` exists | PASS |

---

### Quick Reference Commands

**⚠️ Important:** Use this route_id for all tests: `550e8400-e29b-41d4-a716-446655440000`

#### Setup First (Required):
```bash
# Create test route
docker exec f4k_db psql -U postgres -d f4k \
  -c "INSERT INTO routes (route_id, name, notes, length, created_at, updated_at) VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Test Route', 'Route for testing polylines', 10.5, NOW(), NOW()) ON CONFLICT (route_id) DO NOTHING;"
```

#### Useful curls:
```bash
# List all polylines
curl http://localhost:8080/polylines/

# Create polyline
curl -X POST http://localhost:8080/polylines/ -H "Content-Type: application/json" -d '{"route_id":"550e8400-e29b-41d4-a716-446655440000","encoded_polyline":"..."}'

# Get expired polylines
curl http://localhost:8080/polylines/expired

# Cleanup expired
curl -X POST http://localhost:8080/polylines/cleanup-expired

# Get polylines by route
curl http://localhost:8080/polylines/route/550e8400-e29b-41d4-a716-446655440000
```

#### Useful database queries:
```bash
# Check table structure
docker exec f4k_db psql -U postgres -d f4k -c "\d polylines"

# Verify foreign key
docker exec f4k_db psql -U postgres -d f4k -c "SELECT conname FROM pg_constraint WHERE conname LIKE '%polylines%';"

# Count data
docker exec f4k_db psql -U postgres -d f4k -c "SELECT COUNT(*) FROM polylines;"

# View logs
docker logs f4k_backend --tail 20
```

---

### Conclusion

This polyline implementation fulfills **all ticket requirements**:

1. ✅ **String storage**: `encoded_polyline` field (up to 10,000 chars)
2. ✅ **Expiry tracking**: `expires_at` timestamp field
3. ✅ **Easy deletion**: Single `DELETE WHERE expires_at < NOW()` query
4. ✅ **Small routes table**: Polyline data in separate table
5. ✅ **Foreign key**: `fk_polylines_route_id` constraint ensures integrity

All functionality is validated and working via both **curl** and **Swagger UI**.

---

## Contributing

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes following the coding standards
4. Run tests and linting
5. Submit a pull request with a clear description

## License

[Add license information here]
