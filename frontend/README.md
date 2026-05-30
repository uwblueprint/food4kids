# Frontend
 
Built with React 19, TypeScript, and Vite.

## Project Structure

```
frontend/
├── src/
│   ├── api/                    # Hand-written hooks + generated OpenAPI client (see "API Client" below)
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

**Architecture:** Role-based modular architecture separated by user type (admin, driver). Reusable components and utilities are centralized in `common/`, while page-specific components are colocated with their respective pages.

## Component Guidelines

**`common/components/`** — Reusable, role-agnostic UI elements (buttons, inputs, cards, modals, skeletons). No business logic.

**`pages/[role]/[feature]/components/`** — Components tied to a specific page or feature, with role-specific logic.

**`layouts/`** — Role-specific wrapper components defining overall page structure (navigation, sidebars, headers).

**Naming:**

- PascalCase for component files: `UserCard.tsx`, `LoginForm.tsx`
- Page components prefixed with role: `AdminDriversPage.tsx`, `DriverHomePage.tsx`
- One component per file; named exports (not default); barrel `index.ts` files in component directories

## Design System

The design system is defined in [`src/index.css`](src/index.css) using Tailwind CSS v4's CSS-first config. A live reference is available at `/style-guide` ([StyleGuidePage.tsx](src/pages/StyleGuidePage.tsx)).

### Design Tokens — `@theme`

All colors, fonts, shadows, spacing, and typography are declared as CSS custom properties. Tailwind v4 auto-generates utility classes from them.

```css
@theme {
  --font-nunito: "Nunito", sans-serif;
  --color-blue-300: #226ca7; /* → bg-blue-300, text-blue-300, border-blue-300 */
  --shadow-card: 0px 4px 10px rgba(0, 0, 0, 0.05); /* → shadow-card */
  --text-h1: 2rem; /* → text-h1 */
  --text-h1--line-height: 1.375;
}
```

### Heading Elements

`h1`–`h3` are styled globally — no `className` needed. They use a mobile-first scale that switches at `md` (768px).

| Element | Mobile                     | Desktop                    |
| ------- | -------------------------- | -------------------------- |
| `h1`    | Nunito Bold 24px/32px      | Nunito ExtraBold 32px/44px |
| `h2`    | Nunito SemiBold 20px/24px  | Nunito SemiBold 20px/28px  |
| `h3`    | Nunito Sans Bold 18px/24px | Nunito Sans Bold 16px/20px |

### Paragraph Utilities

| Class     | Mobile       | Desktop      |
| --------- | ------------ | ------------ |
| `text-p1` | 18px / 1.333 | 16px / 1.25  |
| `text-p2` | 16px / 1.5   | 14px / 1.286 |
| `text-p3` | 14px / 1.286 | 12px / 1.5   |

### Spacing

Tailwind's default 4px grid covers all design padding increments natively:

| Design value | Tailwind class  |
| ------------ | --------------- |
| 4px          | `p-1` / `m-1`   |
| 8px          | `p-2` / `m-2`   |
| 12px         | `p-3` / `m-3`   |
| 16px         | `p-4` / `m-4`   |
| 20px         | `p-5` / `m-5`   |
| 24px         | `p-6` / `m-6`   |
| 40px         | `p-10` / `m-10` |
| 80px         | `p-20` / `m-20` |

Use `.page-margins` on top-level page wrappers for consistent page-level margins:

| Breakpoint            | Left / Right | Top  |
| --------------------- | ------------ | ---- |
| Mobile (default)      | 20px         | 20px |
| Tablet `md` (768px)   | 40px         | 20px |
| Desktop `lg` (1024px) | 80px         | 40px |

```tsx
<main className="page-margins">...</main>
```

### Fonts

Loaded via Google Fonts in [`index.html`](index.html). Use `font-nunito` for headings and buttons, `font-nunito-sans` for body text.

### Example

```tsx
<div className="rounded-2xl border border-grey-300 bg-grey-150 p-6 shadow-card">
  <h2 className="mb-1 text-grey-500">Route Generated</h2>
  <p className="text-p2 text-grey-400">Oct 20, 2025 at 10:42 AM</p>
  <div className="mt-4 flex items-center gap-2 rounded-xl border border-success-stroke bg-success-fill px-4 py-3">
    <span className="text-success-stroke">✓</span>
    <p className="text-p2 font-semibold text-success-stroke">
      All 12 stops assigned successfully.
    </p>
  </div>
</div>
```

## TypeScript Conventions

Strict mode is enabled. Follow these placement rules:

- **Global/shared types** → `src/types/`
- **Component-specific types** → inline in the component file
- **API request/response types** → `src/api/generated/types.gen.ts` (auto-generated from FastAPI; see "API Client")

**Best practices:**

- Avoid `any` — use `unknown` with type guards
- Use union types for string literals: `type Status = 'pending' | 'approved' | 'rejected'`
- Always define a props interface; use named destructuring with defaults

## API Client (generated from OpenAPI)

The frontend talks to the backend through a TypeScript SDK generated from FastAPI's OpenAPI schema. This gives end-to-end types: a backend schema change becomes a TypeScript compile error at every call site.

**Layout:**

| Path                       | What it is                                                   | Commit? |
| -------------------------- | ------------------------------------------------------------ | ------- |
| `openapi.json`             | Snapshot of the backend's `/openapi.json`                    | yes     |
| `openapi-ts.config.ts`     | Codegen config                                               | yes     |
| `src/api/runtime.ts`       | Wires the generated client to reuse `src/lib/axiosClient.ts` | yes     |
| `src/api/generated/`       | Auto-generated SDK + types + tanstack-query helpers          | yes     |
| `src/api/*.ts`             | Hand-written hook layer that consumes the generated SDK      | yes     |

`openapi.json` and `src/api/generated/` are both committed so fresh clones and CI work without a generate step. The snapshot also doubles as a human-readable changelog of the API contract — when a PR changes the backend, the diff in `openapi.json` shows the contract change.

**Staying in sync — the pre-commit hook does it for you.** A repo hook regenerates `openapi.json` and the client whenever a commit touches the contract (`backend/python/**`, `frontend/openapi.json`, `frontend/scripts/fetch-openapi.mjs`) and stages the result, so you rarely have to think about it. It dumps the schema by introspecting the FastAPI app — **no running backend needed**. The hook **enables itself** the first time you `pnpm install` here (the `prepare` script points `core.hooksPath` at `scripts/git-hooks`); to enable it by hand, run `git config core.hooksPath scripts/git-hooks` once per clone (worktrees share it).

**Regenerate manually** with the same no-server pipeline the hook uses (from the repo root):

```bash
./scripts/regen-openapi.sh
```

Or, with the backend already running, `pnpm generate:api` from `frontend/` hits `http://localhost:8080/openapi.json` instead (override with `OPENAPI_URL=...`).

CI enforces that `openapi.json` matches the backend schema (the `OpenAPI client in sync` workflow) as a backstop for commits made without the hook. If it fails, the log prints a ready-to-apply patch — `git apply` it, run `pnpm openapi-ts`, and commit (no backend needed; `openapi-ts` reads the local `openapi.json`). The generated client under `src/api/generated/` is a deterministic function of `openapi.json` + the pinned `@hey-api/openapi-ts`, so keeping the snapshot in sync keeps the client in sync.

**Using the generated client.** Prefer the tanstack-query helpers from `src/api/generated/@tanstack/react-query.gen.ts` over the raw SDK functions — they produce query keys and matching `queryOptions` / mutation configs for you. See `src/api/system-settings.ts` for the query pattern and `src/api/locations.ts` for a mutation (incl. multipart upload).

```ts
import { useQuery } from '@tanstack/react-query';
import { getSystemSettingsOptions } from '@/api/generated/@tanstack/react-query.gen';

const { data, isLoading } = useQuery(getSystemSettingsOptions());
```

## Development

```bash
cd frontend

# Install dependencies (first time)
pnpm install

# Start dev server (prefer Docker instead — see root README)
pnpm dev          # http://localhost:3000

# Build for production
pnpm build

# Lint / format
pnpm lint
pnpm lint:fix
pnpm format

# Regenerate API client after backend changes (backend must be running)
pnpm generate:api
```

**Config files:** `vite.config.ts`, `tsconfig.json`, `eslint.config.js`, `.prettierrc`, `openapi-ts.config.ts`
