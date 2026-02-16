# Food4Kids

## Table of Contents

- [Tech Stack](#tech-stack)
- [Repo Structure](#repo-structure)
- [Frontend Development](#frontend-development)
  - [Project Structure](#project-structure)
  - [Component Development Guidelines](#component-development-guidelines)
  - [Tailwind CSS v4 Setup and Usage](#tailwind-css-v4-setup-and-usage)
  - [TypeScript Conventions](#typescript-conventions)
  - [Development Workflow](#development-workflow)
  - [Code Quality and Formatting](#code-quality-and-formatting)
- [Development Setup](#development-setup)
- [Recommended VSCode Settings](#recommended-vscode-settings)
- [Application Execution](#application-execution)
- [API Testing with Postman](#api-testing-with-postman)
- [Database Interactions](#database-interactions)
- [Version Control Guide](#version-control-guide)
  - [Branching](#branching)
  - [Docker Commands](#docker-commands)
- [Claude Code Integration](#claude-code-integration)
- [Formatting and Linting](#formatting-and-linting)
  - [Package Manager Requirements](#package-manager-requirements)
  - [CI/CD Tasks](#cicd-tasks)
- [Testing](#testing)
- [FAQ & Debugging](#faq--debugging)

## Tech Stack

**Frontend:**
- React 19.2.0
- TypeScript 5.9.3
- Vite 7.2.4 (build tool)
- React Router v7.12.0 (routing)
- Tailwind CSS v4.1.18 (styling)
- pnpm (package manager)

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
├── frontend/                      # React + TypeScript frontend (see Frontend Development section)
├── db-init/                       # Database initialization scripts
├── docker-compose.yml             # Multi-container Docker setup
└── README.md
```

## Frontend Development

The frontend is built with React 19, TypeScript, and Vite, using modern development practices and tooling. This section covers the project structure, coding conventions, and development workflow.

### Project Structure

```
frontend/
├── src/
│   ├── api/                    # API client configuration
│   ├── assets/
│   │   ├── fonts/             # Custom web fonts
│   │   └── images/            # Images, logos, icons
│   ├── common/                # Shared reusable code
│   │   ├── components/        # Reusable UI components (buttons, inputs, cards, modals)
│   │   │   └── skeletons/     # Loading skeleton components
│   │   ├── hooks/             # Custom React hooks (useAuth, useFetch, etc.)
│   │   └── utils/             # Utility helper functions
│   ├── constants/             # Application constants and configuration values
│   ├── contexts/              # React Context providers for state management
│   ├── layouts/               # Role-specific layout wrapper components
│   │   ├── AdminLayout.tsx    # Layout for admin pages
│   │   └── DriverLayout.tsx   # Layout for driver pages
│   ├── pages/                 # Page-level components organized by user role
│   │   ├── admin/             # Admin portal pages
│   │   │   ├── drivers/       # Driver management
│   │   │   ├── home/          # Admin dashboard
│   │   │   ├── routes/        # Route management
│   │   │   └── settings/      # Admin settings
│   │   ├── driver/            # Driver portal pages
│   │   │   └── home/          # Driver dashboard
│   │   └── shared/            # Shared pages (login, 404, etc.)
│   ├── types/                 # TypeScript type definitions and interfaces
│   ├── main.tsx               # Application entry point
│   ├── App.tsx                # Root component with routing
│   └── index.css              # Global styles (Tailwind imports)
├── public/                    # Static assets served directly
├── vite.config.ts             # Vite configuration
├── tsconfig.json              # TypeScript configuration
├── eslint.config.js           # ESLint rules
├── .prettierrc                # Prettier formatting rules
└── package.json               # Dependencies and scripts
```

**Architecture:** The frontend uses a role-based modular architecture with separation by user type (admin, driver). Reusable components and utilities are centralized in `common/`, while page-specific components are colocated with their respective pages.

### Component Development Guidelines

**When to use `common/components/`:**
- Reusable UI elements that can be used across multiple roles and features
- Generic components: buttons, inputs, cards, modals, dropdowns, tooltips, skeletons
- No business logic or role-specific knowledge
- Examples: `Button.tsx`, `Input.tsx`, `Card.tsx`, `Modal.tsx`, `PlaceholderPage.tsx`
- Subdirectories for component categories (e.g., `skeletons/` for loading states)

**When to use `pages/[role]/[feature]/components/`:**
- Components tied to a specific page or feature
- Role-specific or feature-specific functionality
- Business logic that won't be reused in other roles/features
- Examples: Components in `pages/admin/drivers/components/`, `pages/driver/home/components/`
- Colocate with the page they belong to for better organization

**When to use `layouts/`:**
- Role-specific wrapper components (navigation, sidebars, headers, footers)
- Components that define the overall page structure for a user role
- Examples: `AdminLayout.tsx`, `DriverLayout.tsx`

**Naming Conventions:**
- Use PascalCase for component files and names: `UserCard.tsx`, `LoginForm.tsx`
- Use descriptive names that clearly indicate the component's purpose
- Avoid generic names like `Component1.tsx` or `Temp.tsx`
- Page components should be prefixed with their role: `AdminDriversPage.tsx`, `DriverHomePage.tsx`

**Best Practices:**
- One component per file
- Always define TypeScript interfaces for props
- Colocate component-specific types with the component file
- Export components using named exports (not default exports)
- Use barrel exports (`index.ts`) in component directories for cleaner imports
- Keep components focused and single-purpose

### Tailwind CSS v4 Setup and Usage

The project uses **Tailwind CSS v4**, which introduces a CSS-first approach without a `tailwind.config.js` file.

**Setup:**
```css
/* src/index.css */
@import 'tailwindcss';
```

**Utility-First Methodology:**
- Use Tailwind utility classes directly in JSX
- Compose utilities to build complex designs
- Avoid custom CSS unless absolutely necessary

**Class Sorting:**
- Prettier automatically sorts Tailwind classes using `prettier-plugin-tailwindcss`
- Classes are ordered by function (layout → spacing → colors → typography, etc.)

### TypeScript Conventions

The project uses **TypeScript strict mode** for maximum type safety.

**Where to Define Types:**

1. **Global/Shared Types** → `src/types/`
   ```typescript
   // src/types/user.ts
   export interface User {
     id: string;
     name: string;
     email: string;
     role: 'admin' | 'user' | 'donor';
   }
   ```

2. **Component-Specific Types** → Inline or in component file
   ```typescript
   // src/components/UserCard.tsx
   interface UserCardProps {
     user: User;
     onEdit?: () => void;
   }
   ```

3. **API Response Types** → `src/api/types/` (when implemented)
   ```typescript
   // src/api/types/responses.ts
   export interface ApiResponse<T> {
     data: T;
     message: string;
     success: boolean;
   }
   ```

**Props Typing Pattern:**
```typescript
// Always define props interface
interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

export const Button = ({ label, onClick, variant = 'primary', disabled = false }: ButtonProps) => {
  // Component implementation
};
```

**Best Practices:**
- Avoid `any` type - use `unknown` with type guards when type is unclear
- Use union types for string literals: `type Status = 'pending' | 'approved' | 'rejected'`
- Leverage TypeScript utility types:
  - `Partial<T>` - Make all properties optional
  - `Pick<T, K>` - Pick specific properties
  - `Omit<T, K>` - Omit specific properties
  - `Record<K, V>` - Object with specific key-value types

**Example with Utility Types:**
```typescript
interface User {
  id: string;
  name: string;
  email: string;
  password: string;
}
```

### Development Workflow

**Running the Frontend Locally (not recommended, use docker instead):**

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
pnpm install

# Start development server
pnpm dev

# Access at http://localhost:3000
```

**Building for Production:**

```bash
# TypeScript type-check and build
pnpm build

# Preview production build locally
pnpm preview
```

**Port Configuration:**
- Default port: `3000` (configured in [vite.config.ts:7](frontend/vite.config.ts#L7))
- Automatically opens in browser
- Supports HMR (Hot Module Replacement) for instant updates

**Development Features:**
- **Fast Refresh:** React components update instantly without losing state
- **TypeScript Checking:** Vite shows TypeScript errors in the terminal
- **ESLint Integration:** Code quality issues highlighted in real-time
- **Auto-Import Sorting:** Imports automatically organized on save

### Code Quality and Formatting

**ESLint Configuration:**
- TypeScript ESLint with strict rules
- React plugin with recommended settings
- React Hooks rules for proper hook usage
- JSX Accessibility (a11y) rules for inclusive design
- Import plugin with auto-sorting

**Prettier Configuration:**
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
```

**Running Code Quality Checks:**

```bash
# Check for linting issues
pnpm lint

# Auto-fix linting issues
pnpm lint:fix

# Format code with Prettier
pnpm format
```

**Recommended Workflow:**
1. Install recommended VSCode extensions (see [Recommended VSCode Settings](#recommended-vscode-settings))
2. Enable format on save and auto-fix ESLint
3. Code is automatically formatted and linted as you work
4. Run `pnpm lint` before committing changes

## Development Setup

### Prerequisites

- Install [Docker Desktop](https://docs.docker.com/get-started/get-docker/) and ensure it's running
- Clone this repository:

```bash
git clone git@github.com:uwblueprint/food4kids.git
cd food4kids
```

### Environment Configuration

You will need to create environment files: `.env` (backend) and `frontend/.env` (frontend). Talk to the PL to obtain these.

**Frontend Environment Variables:**
- A `frontend/.env.example` file is provided as a template
- Copy it to `frontend/.env` and fill in the required values
- Common variables include API endpoints, Firebase configuration, and feature flags
- **Never commit `.env` files** - they are gitignored for security

### Installation

Build and start all services using Docker Compose:

```bash
docker-compose up --build
```

This will start:

- **Frontend**: React development server on port 3000
- **Backend**: FastAPI server on port 8080
- **Database**: PostgreSQL on port 5432

## Recommended VSCode Settings

To ensure consistent code formatting and linting across the team, configure VSCode with these settings.

### Setup Instructions

1. Create a `.vscode/settings.json` file in the project root (if it doesn't exist)
2. Add the configuration below
3. Install the required VSCode extensions

### Configuration

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  }
}
```

### Setting Explanations

- **`formatOnSave`**: Automatically formats code with Prettier when you save a file
- **`defaultFormatter`**: Sets Prettier as the default code formatter for all file types
- **`source.fixAll.eslint`**: Automatically fixes ESLint errors on save (imports, spacing, etc.)

### Required VSCode Extensions

Install these extensions for the best development experience:

1. **Prettier - Code formatter** (`esbenp.prettier-vscode`)
   - Formats code according to `.prettierrc` configuration
   - Install: [Prettier Extension](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)

2. **ESLint** (`dbaeumer.vscode-eslint`)
   - Highlights linting errors and warnings in real-time
   - Auto-fixes issues on save
   - Install: [ESLint Extension](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)

### Optional but Recommended Extensions

- **Tailwind CSS IntelliSense** (`bradlc.vscode-tailwindcss`)
  - Autocomplete for Tailwind CSS classes
  - Shows CSS preview on hover
  - Install: [Tailwind CSS IntelliSense](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss)

- **TypeScript Error Translator** (`mattpocock.ts-error-translator`)
  - Makes TypeScript errors easier to understand
  - Install: [TS Error Translator](https://marketplace.visualstudio.com/items?itemName=mattpocock.ts-error-translator)

### Verification

After setup, test that everything works:
1. Open a `.tsx` file in the frontend
2. Make a formatting change (e.g., remove a semicolon)
3. Save the file - Prettier should auto-format it
4. Add an unused import - ESLint should highlight it and remove it on save

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
docker-compose exec backend python -m app.seed_database
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

### When Claude Code  AuRunstomatically

Claude Code is integrated into the CI/CD pipeline via GitHub Actions:

**Workflow:** `.github/workflows/claude-code-review.yml`

**Triggered on:**
1. **Pull Request Ready for Review** - Automatically runs when a PR is marked as ready
2. **@claude Comment** - Manually trigger by commenting `@claude review` on any PR

**What it Reviews:**
- Code quality and adherence to best practices
- Potential bugs and edge cases
- Performance considerations
- Security vulnerabilities
- Test coverage and quality
- TypeScript/Python type safety
- Documentation completeness

**Benefits:**
- Catches issues before human review
- Provides consistent, objective feedback
- Suggests concrete improvements with examples
- Saves review time by flagging common mistakes
- Helps maintain code quality standards

**Example Usage:**
```bash
# In a pull request comment, trigger a review:
@claude review

# Claude Code will respond with:
# - Code quality analysis
# - Bug reports with severity levels
# - Performance recommendations
# - Security concerns
# - Suggested fixes with code examples
```

For more details on CI/CD workflows, see [CI/CD Tasks](#cicd-tasks) below.

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
docker-compose exec backend mypy . --config-file mypy.ini
```

#### Combined Quality Checks

```bash
# Run all quality checks (linting, formatting, type checking)
docker-compose exec backend ruff check . && docker-compose exec backend ruff format --check . && docker-compose exec backend mypy . --config-file mypy.ini
```

**Configuration Files:**

- Ruff: `backend/python/pyproject.toml` (under `[tool.ruff]`)
- mypy: `backend/python/mypy.ini`

### Frontend (TypeScript/React)

```bash
# Check linting issues
docker-compose exec frontend pnpm lint

# Auto-fix linting issues
docker-compose exec frontend pnpm lint:fix

# Format code with Prettier
docker-compose exec frontend pnpm format
```

**Configuration Files:**
- ESLint: `frontend/eslint.config.js`
- Prettier: `frontend/.prettierrc`
- TypeScript: `frontend/tsconfig.json`

### Package Manager Requirements

**IMPORTANT:** This project uses **pnpm** as the package manager, not npm or yarn.

**Why pnpm?**
- **Faster installs:** Up to 2x faster than npm
- **Efficient disk usage:** Hard links save space by sharing packages across projects
- **Strict dependency resolution:** Prevents phantom dependencies and ensures consistency
- **CI/CD compatibility:** All workflows use pnpm exclusively

**Installation:**

```bash
# Option 1: Via npm (recommended)
npm install -g pnpm

# Option 2: Via Homebrew (macOS)
brew install pnpm

# Option 3: Via Corepack (Node.js 16.13+)
corepack enable
corepack prepare pnpm@latest --activate

# Verify installation
pnpm --version
```

**Usage:**

```bash
# Install dependencies
cd frontend
pnpm install

# Add a new package
pnpm add <package-name>

# Add a dev dependency
pnpm add -D <package-name>

# Remove a package
pnpm remove <package-name>

# Update dependencies
pnpm update
```

**Important Notes:**
- `pnpm-lock.yaml` must be committed to version control
- Do NOT use `npm install` or `yarn install` - this will cause dependency conflicts
- CI workflows will fail if you don't use pnpm
- Docker containers are configured to use pnpm

### CI/CD Tasks

The project uses **GitHub Actions** for continuous integration. All workflows are located in `.github/workflows/`.

**Active Workflows:**

1. **`lint.yml`** - Code Quality Checks
   - **Triggers:** Push or PR to `main` branch (frontend and backend paths)
   - **Frontend:**
     - Runs `pnpm install --frozen-lockfile`
     - Executes `pnpm lint`
     - Uses Node.js 20.11.1 with pnpm 9
   - **Backend:**
     - Runs Ruff linter: `ruff check .`
     - Runs Ruff formatter check: `ruff format --check .`
     - Runs MyPy type checker: `mypy .`

2. **`pytest.yml`** - Backend Testing
   - **Triggers:** Push or PR to `main` for `backend/python/**` paths
   - Sets up PostgreSQL service container
   - Runs `pytest -q --disable-warnings -ra`
   - Python 3.11

3. **`claude-code-review.yml`** - Automated Code Review
   - **Triggers:** PR ready for review, or `@claude review` comment
   - Reviews code quality, bugs, performance, security, and test coverage
   - See [Claude Code Integration](#claude-code-integration) for details

**Running CI Checks Locally:**

Before pushing changes, run the same checks that CI will run:

```bash
# Frontend checks
cd frontend
pnpm lint           # ESLint check
pnpm format         # Prettier format
pnpm build          # TypeScript compilation check

# Backend checks
docker-compose exec backend ruff check .
docker-compose exec backend ruff format --check .
docker-compose exec backend mypy . --config-file mypy.ini
docker-compose exec backend pytest
```

**Note:** Frontend testing framework is not yet configured. This will be added in a future update.

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
