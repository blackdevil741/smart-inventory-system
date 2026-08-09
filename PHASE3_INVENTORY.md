# Phase 3 — Inventory CRUD

This phase adds real product management: Add, Edit, Delete, Search,
Filter, and Sort — all backed by Firestore, with quick stock adjustment
buttons and an activity log for every change.

---

## What's new

### Backend
- `models/product_model.py` — Product schema + validation
- `models/log_model.py` — Activity log entry schema
- `services/product_service.py` — Firestore CRUD, search/filter/sort logic, stock adjustment, and automatic activity logging
- `routes/products_routes.py` — real endpoints:
  - `GET /api/products` — list, with `?search=`, `?category=`, `?stock_filter=low_stock|out_of_stock`, `?sort_by=`
  - `GET /api/products/<id>` — single product
  - `POST /api/products` — create
  - `PUT /PATCH /api/products/<id>` — update
  - `DELETE /api/products/<id>` — delete
  - `POST /api/products/<id>/adjust-stock` — body `{ "delta": <int> }`, used by the +1/+5/+10/-1/-5/-10 buttons

Every product change (create/update/delete/stock adjustment) writes an
entry to a `logs` collection in Firestore — this powers the Activity
Timeline feature in a later phase, and means nothing is silently lost.

### Frontend
- `pages/inventory.html` + `js/pages/inventory.js` — the real Inventory page:
  - Product table with live search (debounced), category filter, stock-level filter, and sort
  - Color-coded rows/badges for low-stock (amber) and out-of-stock (red)
  - Add/Edit modal with validation
  - Delete confirmation modal
  - Quick stock buttons directly in the table
  - Loading skeletons and an empty state
  - Toast notifications for success/error feedback
- `css/app-shell.css` — shared sidebar + topbar layout for authenticated pages
- `css/inventory.css` — table, modal, badge, and toast styling
- `js/services/products-api.js` — wraps all product API calls with the current user's Firebase ID token attached automatically

---

## How to test this locally

1. Make sure your backend is running (`python app.py` inside `backend/`, with your `.env` and `firebase-service-account.json` in place from Phase 2).
2. Make sure your frontend is running (`python -m http.server 5500` inside `frontend/`).
3. Log in at `http://localhost:5500/pages/login.html`.
4. From the placeholder dashboard, click **"Go to Inventory"**, or go directly to:
   ```
   http://localhost:5500/pages/inventory.html
   ```
5. Click **+ Add Product** and create a few test products — try:
   - One with quantity **0** (should show red "out of stock")
   - One with quantity **below** its low-stock threshold (should show amber "low stock")
   - One well-stocked (should show green)
6. Try the **search box** — type part of a product name, SKU, category, or vendor.
7. Try the **category filter** and **stock filter** dropdowns.
8. Try the **quick stock buttons** (+1/+5/+10/-1/-5/-10) — the table should update immediately.
9. Try **Edit** and **Delete** on a product.

### Verifying in Firestore directly
Go to:
```
https://console.firebase.google.com/project/smart-inventory-system-6dea3/firestore/data
```
You should now see two collections:
- `products` — one document per product
- `logs` — one entry per change you made

---

## Known limitations (by design, for this phase)

- Search/filter/sort happens by fetching all products and processing them in Python — perfectly fine for a single small shop's inventory size, but not built for tens of thousands of products. A later phase could move filtering into Firestore queries if needed.
- No pagination yet (all products load at once) — planned as a later enhancement.
- No image upload (Firebase Storage requires a billing account — skipped to keep this project fully free, see `PHASE2_SETUP.md`).
