# Smart Inventory System for Local Vendors

A production-style inventory management system for local shopkeepers and small
vendors — QR-based stock tracking, real-time updates, analytics, and an AI
inventory assistant, built with Flask, Firebase, and vanilla JS.

> **Status: Phases 8–9 of 10 — AI Assistant & Polish.** Only deployment
> remains. See [Roadmap](#roadmap) below, and see `PHASE2_SETUP.md` /
> `PHASE3_INVENTORY.md` / `PHASE4_5_QR_DASHBOARD.md` /
> `PHASE6_7_ANALYTICS_REPORTS.md` / `PHASE8_9_AI_POLISH.md` for setup and
> testing details.

---

## Overview

Shopkeepers running small stores usually track stock in a notebook or a
spreadsheet. This project gives them a real, modern web app instead: scan a
product's QR code to instantly adjust stock, watch low-stock alerts fire in
real time, and see at a glance which categories are moving and which products
need reordering.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask (Python) |
| Frontend | HTML5, CSS3, Bootstrap 5, vanilla JavaScript |
| Database | Firebase Firestore |
| Auth | Firebase Authentication |
| File storage | Firebase Storage |
| Charts | Chart.js |
| QR codes | `qrcode` (Python, server-side generation) + HTML5 QR scanner (browser) |
| Backend hosting | Render |
| Frontend hosting | Firebase Hosting |

## Architecture

```
Browser (HTML/CSS/JS)
   │  fetch() with Firebase ID token
   ▼
Flask API (Render)
   │  Firebase Admin SDK
   ▼
Firestore / Firebase Auth / Firebase Storage
```

The frontend authenticates directly against Firebase Auth (client SDK) and
talks to the Flask backend for everything else — CRUD, QR generation,
analytics aggregation, and reports. Every protected Flask route verifies the
caller's Firebase ID token server-side before touching Firestore, so
Firestore security rules and the API layer both enforce access control.

## Folder Structure

```
smart-inventory-system/
├── backend/
│   ├── app.py                  # Flask app factory + blueprint registration
│   ├── firebase_config.py      # Firebase Admin SDK init (Firestore/Auth/Storage)
│   ├── requirements.txt
│   ├── .env.example
│   ├── routes/                 # One blueprint per feature area
│   │   ├── health_routes.py
│   │   ├── auth_routes.py
│   │   ├── products_routes.py  # Real: CRUD + search/filter/sort/pagination + stock adjust + CSV import/export
│   │   ├── qr_routes.py        # Real: generate QR + resolve scanned product
│   │   ├── dashboard_routes.py # Real: summary + recent activity
│   │   ├── analytics_routes.py # Real: category/stock-value/growth/most-active
│   │   ├── reports_routes.py   # Real: PDF/CSV report downloads
│   │   ├── ai_assistant_routes.py # Real: rule-based Q&A over live data
│   │   └── vendors_routes.py
│   ├── services/               # Firestore business logic, kept out of routes
│   │   ├── auth_service.py
│   │   ├── product_service.py  # Real: create/read/update/delete/search/adjust-stock/CSV import-export
│   │   ├── qr_service.py       # Real: QR PNG generation (base64 data URL)
│   │   ├── dashboard_service.py # Real: summary + activity aggregation
│   │   ├── analytics_service.py # Real: chart data aggregation (unit-tested)
│   │   ├── report_service.py   # Real: PDF (reportlab) + CSV report builders
│   │   └── ai_assistant_service.py # Real: intent matching + grounded answers (tested)
│   ├── models/                 # Data schemas (Product, User, Vendor, Log)
│   │   ├── product_model.py    # Real: validation + doc builders
│   │   └── log_model.py        # Real: activity log entries
│   └── utils/
│       ├── auth_middleware.py  # @require_auth decorator (verifies ID tokens)
│       └── responses.py        # Consistent {success, data|error} JSON shape
│
├── frontend/
│   ├── index.html               # Redirects to pages/login.html
│   ├── pages/                   # login, signup, forgot-password, dashboard, inventory, qr-scanner, analytics, reports, ai-assistant
│   ├── css/
│   │   ├── tokens.css           # Design tokens: color, type, spacing + dark mode overrides
│   │   ├── auth.css             # Auth screens ("price tag" card styling)
│   │   ├── app-shell.css        # Sidebar + topbar layout for authenticated pages
│   │   ├── inventory.css        # Product table, modal, badges, toasts
│   │   ├── qr-scanner.css       # Camera viewport + scan result panel
│   │   ├── dashboard.css        # Summary cards, low-stock list, activity feed
│   │   ├── analytics.css        # Chart cards, stat highlights
│   │   └── ai-assistant.css     # Chat bubbles, suggestion chips
│   ├── js/
│   │   ├── firebase-init.js     # Real Firebase client SDK config
│   │   ├── services/
│   │   │   ├── api.js           # fetch() wrapper for the Flask API
│   │   │   └── products-api.js  # Products, QR, Dashboard, Analytics, Reports, AI Assistant, CSV import/export API calls (auto ID token)
│   │   ├── components/
│   │   │   ├── toast.js         # Toast notification helper
│   │   │   └── theme-toggle.js  # Shared dark mode toggle (persisted in localStorage)
│   │   └── pages/               # Per-page JS (login.js, signup.js, inventory.js, qr-scanner.js, dashboard.js, analytics.js, reports.js, ai-assistant.js, ...)
│   └── assets/
│
└── firebase/
    └── firestore.rules          # Security rules (users, products, vendors, logs)
```

## What's built so far

**Phase 1 — Skeleton**
- Full backend skeleton: Flask app factory, all blueprints registered
  (most as placeholders returning `501 Not Implemented` until their phase),
  Firebase Admin SDK wiring, auth middleware, standardized responses.
- Frontend design system (`tokens.css`) and page shells for
  Login / Signup / Forgot Password.

**Phase 2 — Firebase setup & real authentication**
- Connected to a real Firebase project (Firestore + Authentication,
  Storage intentionally skipped to stay on the free Spark plan with no
  billing account required).
- Real Firebase Auth wired into Login, Signup, and Forgot Password —
  actual account creation, sign-in, sign-out, and password reset emails.
- `POST /api/auth/register-profile` — creates a Firestore user profile
  (shop name, role) linked to the Firebase Auth account by `uid`.
- `GET /api/auth/me` / `GET /api/auth/verify` — protected routes that
  verify a Firebase ID token via `@require_auth` before responding.
- `firebase/firestore.rules` — real security rules restricting each user
  to their own profile document and requiring sign-in for all other data.
- A route-guarded placeholder dashboard (`dashboard.html`) that redirects
  unauthenticated visitors back to login, and confirms successful login
  with a working logout button.
- See `PHASE2_SETUP.md` for the exact steps to run this with your own
  Firebase credentials.

**Phase 3 — Inventory CRUD**
- Real Product model + Firestore-backed CRUD: create, read, update, delete.
- Search (name/SKU/vendor/category), filter (category, low stock, out of
  stock), and sort (name, quantity, price, newest).
- Quick stock adjustment buttons (+1/+5/+10/-1/-5/-10) directly in the table.
- Every change (create/update/delete/stock adjustment) is written to a
  `logs` collection for future Activity Timeline / Undo features.
- Full Inventory page UI: color-coded low-stock/out-of-stock rows, Add/Edit
  modal, delete confirmation, loading skeletons, empty state, toasts.
- See `PHASE3_INVENTORY.md` for details and testing steps.

**Phases 4–5 — QR System & Real Dashboard**
- Real QR code generation per product (`/api/qr/<id>`), viewable and
  downloadable from the Inventory table.
- Real webcam-based QR Scanner page (`html5-qrcode`) — scan a product's
  code to instantly see its details and adjust stock with quick buttons,
  right from the scan result (no need to open the full inventory table).
- Real Dashboard replacing the earlier placeholder: total products,
  low-stock/out-of-stock counts, category count, total stock value, a
  "needs attention" low-stock list, and a live recent-activity feed
  pulled from the same `logs` collection written during Phase 3.
- See `PHASE4_5_QR_DASHBOARD.md` for details and testing steps.

**Phases 6–7 — Analytics & Reports**
- Real Chart.js analytics: category distribution (pie), stock value by
  category (bar), monthly inventory growth (bar), and an approximated
  "most active products" list — all backed by real Firestore
  aggregation, with the aggregation math unit-tested.
- Real downloadable reports: Inventory, Stock Value, and Low Stock,
  each exportable as a styled PDF (via reportlab) or CSV, generated
  entirely in memory and streamed as a direct browser download.
- See `PHASE6_7_ANALYTICS_REPORTS.md` for details and testing steps.

**Phases 8–9 — AI Assistant & Polish**
- Rule-based AI Inventory Assistant with a real chat UI — answers
  questions about low stock, out-of-stock items, category comparisons,
  reorder suggestions, and stock value, grounded in live Firestore data
  (no external LLM API required, keeping the project fully free).
- Dark mode toggle, persisted across sessions and pages.
- Pagination on the Inventory page (`?page=&page_size=`).
- Bulk CSV import and export for products, with per-row validation on
  import so a few bad rows don't block the good ones.
- See `PHASE8_9_AI_POLISH.md` for details and testing steps.

## Installation (current state)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Then, in Phase 2, add your Firebase service account key + project config.
python app.py
```

The server will refuse to start until a valid Firebase service account key
is present — this is expected until Phase 2.

### Frontend

No build step. Serve the `frontend/` folder with any static server, e.g.:

```bash
cd frontend
python -m http.server 5500
```

Then open `http://localhost:5500/pages/login.html`.

## Screenshots

_Placeholder — screenshots will be added as each phase's UI is completed._

- `docs/screenshots/login.png`
- `docs/screenshots/dashboard.png`
- `docs/screenshots/inventory.png`
- `docs/screenshots/qr-scan.png`
- `docs/screenshots/analytics.png`

## Roadmap

- [x] **Phase 1** — Project skeleton
- [x] **Phase 2** — Firebase setup + real Authentication (Login, Signup, Forgot Password, Logout, route protection)
- [x] **Phase 3** — Inventory CRUD (Add/Edit/Delete/Search/Filter/Sort products)
- [x] **Phase 4** — QR system (generation + real webcam scan-to-adjust-stock)
- [x] **Phase 5** — Dashboard (summary cards, activity feed, low-stock list)
- [x] **Phase 6** — Analytics (Chart.js: category distribution, growth, stock value)
- [x] **Phase 7** — Reports (Inventory / Stock Value / Low Stock — PDF & CSV export)
- [x] **Phase 8** — AI Inventory Assistant (rule-based Q&A over live Firestore data)
- [x] **Phase 9** — Polish (dark mode toggle, pagination, bulk CSV import/export)
- [ ] **Phase 10** — Deployment (Render backend, Firebase Hosting frontend)

## Future Enhancements

- Inventory prediction using moving average
- Role-based auth (Admin / Staff)
- Barcode support alongside QR
- PWA support with offline caching
- Email notifications for low stock

## License

MIT
