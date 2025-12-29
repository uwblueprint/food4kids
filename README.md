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

## Tech Stack

**Frontend:** React, TypeScript
**Backend:** Python, FastAPI, SQLModel
**Database:** PostgreSQL  
**Authentication:** Firebase Auth  
**Containerization:** Docker & Docker Compose

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
│       │   │   └── jobs/           # Scheduled Cron Jobs
│       │   │   └── protocols/      # Algorithms and how the server handles data
│       │   ├── templates/          # Email/HTML templates
│       │   └── utilities/          # Shared utility functions
│       ├── tests/                  # Unit and functional tests
│       ├── alembic.ini            # Alembic configuration
│       ├── requirements.txt       # Python dependencies
│       └── server.py              # Application entry point
├── frontend/
│   └── src/
│       ├── APIClients/          # API client implementations
│       │   ├── AuthAPIClient.ts         # Authentication API calls
│       │   ├── BaseAPIClient.ts         # Base API client with common functionality
│       │   ├── EntityAPIClient.ts       # Generic entity CRUD operations
│       │   └── SimpleEntityAPIClient.ts # Simplified entity operations
│       ├── components/          # React components
│       │   ├── auth/            # Authentication components
│       │   │   ├── Login.tsx            # User login form
│       │   │   ├── Signup.tsx           # User registration form
│       │   │   ├── Logout.tsx           # Logout handler
│       │   │   ├── PrivateRoute.tsx     # Protected route wrapper
│       │   │   ├── RefreshCredentials.tsx  # Token refresh logic
│       │   │   └── ResetPassword.tsx    # Password reset form
│       │   ├── common/          # Reusable components
│       │   │   └── MainPageButton.tsx   # Common button component
│       │   ├── crud/            # CRUD operation components
│       │   │   ├── CreateForm.tsx       # Generic create form
│       │   │   ├── UpdateForm.tsx       # Generic update form
│       │   │   ├── DisplayTableContainer.tsx  # Data display table
│       │   │   ├── SimpleEntityCreateForm.tsx
│       │   │   ├── SimpleEntityUpdateForm.tsx
│       │   │   └── SimpleEntityDisplayTableContainer.tsx
│       │   └── pages/           # Page-level components
│       │       ├── Default.tsx          # Default/home page
│       │       ├── NotFound.tsx         # 404 error page
│       │       ├── CreatePage.tsx       # Entity creation page
│       │       ├── UpdatePage.tsx       # Entity update page
│       │       ├── DisplayPage.tsx      # Entity display page
│       │       ├── EditTeamPage.tsx     # Team editing page
│       │       ├── HooksDemo/           # Demo components for React hooks
│       │       ├── SimpleEntityCreatePage.tsx
│       │       ├── SimpleEntityUpdatePage.tsx
│       │       └── SimpleEntityDisplayPage.tsx
│       ├── constants/           # Application constants
│       │   ├── AuthConstants.ts         # Authentication-related constants
│       │   └── Routes.ts                # Route path definitions
│       ├── contexts/            # React Context API providers
│       │   ├── AuthContext.ts           # Authentication state context
│       │   ├── SampleContext.ts         # Sample context implementation
│       │   └── SampleContextDispatcherContext.ts
│       ├── reducers/            # State management reducers
│       │   └── SampleContextReducer.ts  # Sample reducer for context
│       ├── types/               # TypeScript type definitions
│       │   ├── AuthTypes.ts             # Authentication types
│       │   └── SampleContextTypes.ts    # Sample context types
│       ├── utils/               # Utility functions
│       │   └── LocalStorageUtils.ts     # Local storage helpers
│       ├── App.tsx              # Main application component
│       ├── index.tsx            # Application entry point
│       └── index.css            # Global styles
├── db-init/                       # Database initialization scripts
├── docker-compose.yml             # Multi-container Docker setup
└── README.md
```

## Frontend Architecture

The frontend is built with React and TypeScript, following a component-based architecture with clear separation of concerns.

### Directory Organization

**APIClients/**
Contains all API communication logic, abstracting HTTP requests to the backend:
- `BaseAPIClient.ts`: Foundation class with common HTTP methods and error handling
- `AuthAPIClient.ts`: Handles authentication endpoints (login, signup, password reset)
- `EntityAPIClient.ts`: Generic CRUD operations for complex entities
- `SimpleEntityAPIClient.ts`: Simplified API client for basic entities

**Components/**
React components organized by functionality:
- `auth/`: Authentication flow components (login, signup, logout, protected routes)
- `common/`: Reusable UI components shared across the application
- `crud/`: Generic forms and tables for Create, Read, Update, Delete operations
- `pages/`: Top-level page components that compose smaller components

**State Management**
The application uses React Context API for global state:
- `contexts/`: Context providers for shared state (authentication, sample data)
- `reducers/`: Reducer functions for complex state updates
- `types/`: TypeScript interfaces and types for type-safe state management

**Routing & Constants**
- `constants/Routes.ts`: Centralized route path definitions
- `constants/AuthConstants.ts`: Authentication-related configuration

**Utilities**
- `utils/LocalStorageUtils.ts`: Helper functions for browser storage operations
- Includes type-safe wrappers around localStorage

### Key Patterns

**Authentication Flow**
- Firebase Authentication integration via `AuthContext`
- Protected routes using `PrivateRoute` component wrapper
- Automatic token refresh with `RefreshCredentials` component
- Persistent session management through localStorage

**CRUD Operations**
The application provides two levels of CRUD abstractions:
1. **Generic Entity**: Full-featured CRUD with complex validation (`EntityAPIClient`, `CreateForm`, `UpdateForm`)
2. **Simple Entity**: Streamlined CRUD for basic data models (`SimpleEntityAPIClient`, `SimpleEntityCreateForm`)

**Type Safety**
- Strong TypeScript typing throughout the application
- Type definitions in `types/` directory
- API response types matching backend schemas

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

## FAQ & Debugging

<details>
<summary>How do I test API endpoints?</summary>

- Ensure the backend container is running
- Visit http://localhost:8080/docs for interactive API documentation
- Use the "Authorize" button to add your Firebase auth token
- Test endpoints in Postman or directly in the Swagger UI

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

## Contributing

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes following the coding standards
4. Run tests and linting
5. Submit a pull request with a clear description

## License

[Add license information here]
