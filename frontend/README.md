# Resume Intelligence — Frontend

Production React frontend for the [Resume Intelligence](https://github.com/Kushal-phbs/resume-intellegence) FastAPI backend.

## Tech Stack

React 18 · TypeScript · Vite · React Router v6 · TanStack Query v5 · Axios · React Hook Form · Zod · Tailwind CSS · Framer Motion · Recharts · Lucide Icons · Zustand

---

## Installation

```bash
tar -xzf frontend.tar.gz   # if starting from the archive
cd frontend
npm install
```

---

## Environment Variables

Copy `.env.example` to `.env` and set:

```env
# Base URL of the FastAPI backend — no trailing slash, no /api prefix
VITE_API_BASE_URL=http://localhost:8000
```

The backend mounts all routes at root (e.g. `/auth/login`, not `/api/v1/auth/login`).

---

## Development

```bash
npm run dev          # starts at http://localhost:5173
```

The dev server proxies nothing — the axios client calls `VITE_API_BASE_URL` directly.
Backend must have CORS enabled for `http://localhost:5173` (it does by default).

---

## Production Build

```bash
npm run build        # outputs to dist/
npm run preview      # preview the production build locally
```

---

## Backend Connection

| Frontend route | Backend endpoint(s) |
|----------------|---------------------|
| `/login` | `POST /auth/login` |
| `/register` | `POST /auth/register` |
| `/` (Dashboard) | `GET /dashboard` · `POST /dashboard/refresh` · `GET /dashboard/trends` |
| `/resumes` | `GET /resumes` · `POST /resumes/upload` · `DELETE /resumes/{id}` |
| `/resumes/:id` | `GET /resumes/{id}` · `GET /resumes/{id}/download` |
| `/resumes/:id/analysis` | `GET /analysis/{id}` · `POST /analysis/{id}` · `GET /analysis/{id}/history` · `DELETE /analysis/{id}` |
| `/job-analysis` | `GET /job-analysis/history` · `POST /job-analysis/{resumeId}/{jobId}` |
| `/job-analysis/:id` | `GET /job-analysis/{id}` |
| `/tailoring` | `POST /resume-tailoring/{resumeId}/{jobId}` · `GET /resume-tailoring/history` · `GET /resume-tailoring/{id}/resume` · `GET /resume-tailoring/{id}/cover-letter` |
| `/chat` | `GET/POST /chat/conversations` · `GET/PATCH/DELETE /chat/conversations/{id}` · `GET/POST /chat/conversations/{id}/messages` |
| `/profile` | `GET /users/me` |
| `/settings` | `GET/PATCH /notifications` · `PATCH /notifications/read-all` |

**Authentication**: Bearer JWT. Access token (15 min) stored in `localStorage`. Axios interceptor silently refreshes via `POST /auth/refresh` on 401. On refresh failure, tokens are cleared and user is redirected to `/login`.

---

## Known Backend Limitations

1. **No profile editing** — `GET /users/me` is read-only. No `PATCH /users/me` exists. The Profile page displays a banner explaining this.

2. **No password change** — No password-update endpoint exists. The Settings page shows a disabled button with an explanatory banner.

3. **No logout endpoint** — `POST /auth/logout` does not exist. Logout is client-side only (tokens discarded, React Query cache cleared).

4. **No job description creation** — Job Analysis and Resume Tailoring both require an existing `job_id` (a `JobDescription` UUID already in the database). Neither `/job-descriptions` nor any equivalent endpoint exists. Both pages display an info banner explaining this, and accept a raw UUID input.

5. **No SSE/streaming for chat** — `POST /chat/conversations/{id}/messages` is a synchronous JSON endpoint. The typing indicator is optimistic (shown from request start until response arrives), not driven by a real stream.

6. **No server-side pagination on `GET /resumes`** — the endpoint returns all resumes in one payload. The Resume Library implements client-side search and pagination over the full list.

7. **No resume text preview after upload** — extracted content is only returned in the `POST /resumes/upload` response, not retrievable afterward. The Resume Detail page links to the original file download instead.

---

## Code Structure

```
src/
├── api/           # Axios API modules — one file per backend domain
├── components/    # Reusable components (ui/, common/, domain/)
├── constants/     # Route paths, React Query cache keys
├── hooks/         # React Query hooks — one file per domain
├── layouts/       # AppLayout (authenticated shell), AuthLayout (public)
├── lib/           # queryClient, utils, toastBus
├── pages/         # Page components, one directory per section
├── routes/        # Router config, ProtectedRoute, PublicRoute
├── store/         # Zustand stores (authStore, themeStore)
└── types/         # TypeScript interfaces mirroring backend Pydantic schemas
```

---

## Validation

```bash
npm run lint        # ESLint — 0 errors, 0 warnings
npx tsc --noEmit    # TypeScript — 0 errors
npm run build       # Vite production build — succeeds
```
