# ADR-002: Frontend Technology Stack for Career Attendant Web UI

Status: Accepted

## Context

Career Attendant needs a web-based frontend to complement the browser extension. The frontend will provide:

- Landing/marketing page for new users
- Dashboard with job search analytics
- Full-featured job tracking interface (saved jobs table, job detail views)
- AI workflow status display (job fit scores, generated documents)

Key considerations:

- **Existing ecosystem**: Backend is FastAPI with Clerk authentication already integrated.
- **Project rules**: `windsurf-rules/` defines conventions for React (functional components, hooks), state management (TanStack Query for server state, Zustand for client state), and testing (AAA pattern).
- **Wireframe exists**: `Wireframe Mockup/job-tracker-final.tsx` is a 1100+ line React component using Tailwind CSS and Lucide icons.
- **Team familiarity**: Need to balance modern best practices with maintainability.
- **Future scalability**: May need SSR/SEO for marketing pages, but job tracker is authenticated SPA.

## Alternatives Considered

### Option A: Next.js (App Router)
- **Pros**: SSR for SEO, file-based routing, React Server Components, great DX
- **Cons**: More complexity, learning curve for App Router patterns, may be overkill for primarily SPA use case

### Option B: Vite + React + React Router
- **Pros**: Fast builds, simple mental model, matches wireframe structure, lighter weight
- **Cons**: No SSR out of box (can add later), manual routing setup

### Option C: Remix
- **Pros**: Great data loading patterns, nested routes, progressive enhancement
- **Cons**: Different mental model from typical React, smaller ecosystem

## Decision

**Option B: Vite + React + React Router** with the following stack:

| Category | Choice | Rationale |
|----------|--------|-----------|
| **Build Tool** | Vite | Fast HMR, simple config, TypeScript support |
| **Framework** | React 18 | Project rules mandate functional components + hooks |
| **Routing** | React Router v6 | Simple, well-documented, matches SPA needs |
| **Server State** | TanStack Query v5 | Per `state-management.md` rules - caching, loading states |
| **Client State** | Zustand | Per rules - lightweight, no Context re-render issues |
| **Styling** | Tailwind CSS v3 | Matches wireframe, utility-first, fast iteration |
| **Icons** | Lucide React | Already used in wireframe, tree-shakeable |
| **Auth** | Clerk React SDK | Matches existing backend integration |
| **HTTP Client** | Axios or fetch | For TanStack Query, matches `httpx` pattern on backend |
| **Testing** | Vitest + React Testing Library | Fast, Vite-native, supports AAA pattern |
| **Forms** | React Hook Form + Zod | Type-safe validation, minimal re-renders |

### Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components (PascalCase.tsx)
│   ├── pages/          # Route-level components
│   ├── hooks/          # Custom hooks (kebab-case.ts)
│   ├── stores/         # Zustand stores
│   ├── lib/            # Utilities, API client
│   └── types/          # TypeScript interfaces
├── public/
└── tests/
```

## Consequences

### Pros
- **Fast development**: Vite's HMR + Tailwind JIT = instant feedback
- **Aligned with rules**: Follows existing `windsurf-rules/` conventions exactly
- **Wireframe reuse**: Can extract components directly from `job-tracker-final.tsx`
- **Simple deployment**: Static build can deploy to Railway, Vercel, Netlify, or S3
- **Clear data flow**: TanStack Query handles API state, Zustand for UI-only state

### Cons / Tradeoffs
- **No SSR**: Marketing/SEO pages won't have server rendering. Mitigation: Can add `@tanstack/react-router` with SSR later, or use prerendering.
- **Manual route setup**: No file-based routing like Next.js. Acceptable for small route count.
- **Separate deploys**: Frontend and API are separate services. This is already the pattern with the browser extension.

### Future Options
- If SEO becomes critical, can migrate marketing pages to Next.js while keeping job tracker as SPA.
- Can add PWA support via `vite-plugin-pwa` for offline job viewing.
- TanStack Router could replace React Router if we need type-safe routing later.

## Resolved Questions

1. **Hosting**: **Railway** - Same platform as API. Simplifies ops, one bill, shared env vars.
2. **Monorepo**: **Yes** - Keep `frontend/` in same repo for easier coordination.
3. **Shared types**: Future consideration - can use OpenAPI codegen when needed.

## Deployment Strategy

- Frontend deploys as separate Railway service in same project
- Static build output served via Railway's static site hosting
- API and frontend share Railway project for unified management

## Monorepo Exit Criteria

The monorepo structure should be maintained until one or more of these signals appear:

### Keep Monorepo While
- Solo developer or small team (1-3 people)
- API + frontend changes are tightly coupled
- Shared release cycle (deploy both together)
- CI runs in <10 minutes
- Still in learning/MVP stage

### Consider Splitting When
| Signal | Threshold |
|--------|-----------|
| Team size | >2 regular contributors working in parallel |
| CI duration | Full test suite exceeds 15-20 minutes |
| Deploy cadence | Frontend needs to ship 5x more frequently than API |
| Repo size | Git clone or IDE indexing becomes noticeably slow |
| Specialization | Dedicated frontend/backend teams who don't touch each other's code |
| API contracts | Need formal versioning between services |

### Expected Timeline
Monorepo is appropriate for 6-12+ months of solo/small team development. Splitting too early adds coordination overhead that slows iteration. The pain of staying monorepo will become obvious when it's time to split.
