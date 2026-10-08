# LingoLab Frontend

Web interface for LingoLab, built to the Karabakh University Digital Design
System (KUDS v1.0): React, Next.js (App Router), TypeScript, Tailwind CSS.

This connects to the **LingoLab backend** (`apps/api/`, Django) over
its REST API. Run the backend first (see its own README), then this app.

## 1. What's included

| Page | Route | Notes |
|---|---|---|
| Landing / Home | `/` | Marketing page: hero, the 7-stage model, live skills status, CTA |
| Sign up | `/signup` | Live-validated form (Zod) + **Continue as guest** |
| Log in | `/login` | Same, for returning users |
| Dashboard | `/dashboard` | Welcome banner, quick actions, stats, recent activity |
| Start a test | `/dashboard/assessment` | Pick Vocabulary or Grammar |
| Take a test | `/dashboard/assessment/[sessionId]` | One question at a time, adapts by level |
| Result | `/dashboard/assessment/[sessionId]/result` | CEFR result + per-level chart (Recharts) |
| Progress | `/dashboard/progress` | History of all past sessions, filterable by skill |
| Profile | `/dashboard/profile` | Edit your own name/email, delete your account |
| Admin · Questions | `/dashboard/admin/questions` | **Admin only.** Full CRUD on the question bank: filter, create, edit, delete |

All of `/dashboard/*` requires being logged in (as a real user or a guest);
unauthenticated visitors are redirected to `/login`.

## 2. Setup & run

Requires Node.js 18.18+ (Next.js 14 requirement).

```bash
cd apps/web
npm install
cp .env.local.example .env.local
npm run dev
```

Open **http://localhost:3000**.

By default the app calls the backend at `http://127.0.0.1:8000` (set in
`.env.local` via `NEXT_PUBLIC_API_URL`). Make sure the Django backend is
running (`python manage.py runserver`) before using the app - the backend
already has CORS open for local development, so no extra config is needed
on that side.

### Production build

```bash
npm run build
npm run start
```

Note: both `npm run dev` and `npm run build` fetch the Poppins font from
Google Fonts at build/start time via `next/font/google` - this needs an
internet connection once (Next.js self-hosts the font file afterwards, no
runtime calls to Google).

## 3. How authentication works (Sprint 1)

- Matches the backend's simple Token auth: no JWT, no refresh flow.
- On login/signup/guest, the token is stored in `localStorage` and attached
  to every API request as `Authorization: Token <token>`.
- "Continue as guest" (`POST /api/v1/auth/guest/`) creates a temporary,
  password-less account server-side and logs the person in immediately -
  no form, so someone can try the placement test with zero friction. A
  guest banner appears in the dashboard header as a reminder.
- Logging out simply clears the stored token.

## 4. Design system compliance (KUDS v1.0)

Everything below is centralized in `tailwind.config.ts` and `globals.css`
so no component hardcodes its own values:

- **Colors**: KU Green `#44766C`, Dark Green `#16423C`, Soft Green, Light
  Blue, Cream, plus semantic Success/Warning/Danger - exactly as specified.
- **Type**: Poppins (fallback Tahoma), 150% line height, the full
  Display/H1-H4/Body/Small/Caption scale from the guidelines table.
- **Radius**: Button/Input 8px, Card 12px, Modal 16px, Badge/Avatar full.
- **Shadows**: only the three specified levels (xs/sm/md) - no heavy shadows.
- **Spacing**: only the approved steps (4/8/12/16/24/32/48/64/96px).
- **Layout**: 1440px desktop container, 280px sidebar, 72px header.
- **Icons**: Lucide only. **Charts**: Recharts only.
- **Shared components**: Button, Input, Card, Badge, Alert, Sidebar,
  Header live in `src/components/ui` and `src/components/layout` - reused
  everywhere rather than redesigned per page, per KUDS section 18/23.

## 5. Project structure

```
src/
├── app/                     # Next.js App Router pages
│   ├── page.tsx             # Landing
│   ├── (auth)/               # Sign up / Log in (shared centered layout)
│   └── dashboard/            # Sidebar+Header shell, auth-guarded
│       ├── assessment/       # Start test, take test, result
│       ├── progress/         # Session history
│       ├── profile/          # Edit / delete own account
│       └── admin/questions/  # Admin-only question bank CRUD
├── components/
│   ├── ui/                  # Button, Card, Input, Badge, Alert, feedback
│   │                        # (Spinner/FullPageSpinner/ErrorState), EmptyState, ConfirmDialog
│   ├── layout/               # Sidebar, Header, MobileSidebar, Footer
│   ├── landing/               # Hero, PipelineSection, SkillsSection, CTA
│   ├── auth/                 # GuestContinueButton, OrDivider
│   └── assessment/             # QuestionCard, LevelBreakdownChart, QuestionForm (admin)
├── hooks/                    # useAuth, useToast, useAssessment (React Query), QueryProvider
├── services/                  # api.ts (fetch client), types.ts (API contracts)
└── lib/                      # utils.ts (cn helper)
```

Sprint 2 additions: a global toast notification system (`useToast`), reusable
`EmptyState`/`ErrorState` components used across Dashboard/Progress/Admin,
and a `ConfirmDialog` modal for destructive actions (delete account, delete
question).

## 6. Known limitations (intentional for Sprint 1/2)

- No SSR-protected routes (auth guard is client-side); acceptable since the
  backend itself enforces auth on every request regardless of the UI.
  A later sprint can move this to middleware-based route protection.
- No password reset / email verification flow (matches the backend, which
  doesn't implement these yet either).
- `npm audit` flags advisories in Next.js that are only fixed by upgrading
  to the Next.js 16 major version, which involves breaking changes not
  yet tested against this codebase. For a local MVP/coursework deployment
  this is a reasonable tradeoff; revisit before any real production/public
  deployment.
