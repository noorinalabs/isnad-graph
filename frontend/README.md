# isnad-graph Frontend

React 19 + TypeScript SPA for the isnad-graph computational hadith analysis platform.

## Setup

```bash
npm install
npx playwright install chromium   # Required for E2E tests
```

Or from the repo root:

```bash
make setup-frontend
```

## Development

```bash
npm run dev       # Start Vite dev server (http://localhost:5173)
npm run build     # TypeScript check + production build
npm run preview   # Preview production build (http://localhost:4173)
```

## Testing

### Unit Tests (Vitest)

```bash
npm run test      # Watch mode
npm run test -- --run  # Single run
```

### E2E Tests (Playwright)

E2E tests are in `tests/e2e/` and run against the preview server (`localhost:4173` by default).

```bash
# Headless (CI mode)
npx playwright test

# Headed (visible browser)
npx playwright test --headed

# Interactive UI mode
npx playwright test --ui

# Single test file
npx playwright test tests/e2e/auth.spec.ts --headed

# Against the live site
BASE_URL=https://isnad-graph.noorinalabs.com npx playwright test --headed
```

Or from the repo root:

```bash
make frontend-e2e            # Headless
make frontend-e2e-headed     # Visible browser
make frontend-e2e-ui         # Interactive UI
make frontend-e2e-live       # Against live site (headed)
```

### Test Files

| File | Coverage |
|------|----------|
| `auth.spec.ts` | Login, logout, OAuth flows |
| `navigation.spec.ts` | Page navigation, routing |
| `search.spec.ts` | Search functionality |
| `accessibility.spec.ts` | Accessibility checks (axe-core) |

## Linting

```bash
npm run lint      # ESLint
```

## Tech Stack

- React 19, TypeScript, Vite
- Radix UI primitives, Tailwind CSS, CVA
- TanStack Query (server state)
- D3.js (graph visualization)
- Playwright (E2E), Vitest (unit)
