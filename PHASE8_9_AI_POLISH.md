# Phase 8 + 9 — AI Assistant & Polish

Combined into one pass: a rule-based AI Inventory Assistant, dark mode,
pagination, and bulk CSV import/export.

---

## What's new

### AI Inventory Assistant (backend)
- `services/ai_assistant_service.py` — rule-based natural language Q&A grounded in live Firestore data. Matches questions against intents (low stock, out of stock, category comparisons, reorder suggestions, total products, stock value, greeting) using pattern matching, then answers from real data — never invented.
- **Why rule-based instead of a real LLM API**: keeps the entire project on free tiers with zero API keys or billing (see `PHASE2_SETUP.md` for the same reasoning behind skipping Firebase Storage). It fully covers the three example questions from the original spec ("what products are low?", "which category has highest stock?", "suggest reorder items") plus several natural variations.
- `routes/ai_assistant_routes.py`: `POST /api/ai-assistant/ask` with `{ "question": "..." }`
- Tested against 8 real question variations before shipping.

### AI Inventory Assistant (frontend)
- `pages/ai-assistant.html` + `js/pages/ai-assistant.js` — a real chat interface: message bubbles, suggested-question chips, typing indicator, all wired to the live backend.

### Dark Mode
- `data-theme="dark"` attribute on `<html>`, toggled via a button in every authenticated page's topbar, persisted in `localStorage`.
- Applied immediately on page load (before first paint) to avoid a flash of the wrong theme.

### Pagination
- `GET /api/products` now accepts `?page=1&page_size=20` and returns `{ items, pagination: { page, page_size, total_items, total_pages } }` instead of a bare array.
- Inventory page shows Prev/Next controls and a "Page X of Y · N products" indicator; the category filter dropdown is populated from a separate full-list fetch so it isn't limited to whatever's on the current page.

### Bulk CSV Import/Export
- `GET /api/products/export` — downloads all products as CSV (same column format as reports' inventory export, so it round-trips: export → edit in Excel → re-import).
- `POST /api/products/import` — accepts a multipart file upload, validates each row independently (bad rows are reported with their row number, good rows still get imported), returns a summary.
- Verified with a mixed valid/invalid CSV before shipping (2 valid rows imported, 1 invalid row correctly rejected with a clear error).
- Inventory page has **Export CSV** and **Import CSV** buttons in the toolbar.

---

## How to test this locally

1. Backend + frontend running, logged in.
2. **AI Assistant**: click the sidebar link, try the suggested question chips, then type a few of your own (e.g. "how many products do I have", "what's my stock worth").
3. **Dark mode**: click the 🌙/☀️ button in the topbar on any page — confirm the whole app switches themes, and that it stays switched after navigating to another page or refreshing.
4. **Pagination**: if you have more than 10 products, confirm Prev/Next appear and work on the Inventory page. With fewer than 10, the controls should still show ("Page 1 of 1") but be disabled.
5. **CSV export**: click **Export CSV** on Inventory, confirm a real CSV downloads with your product data.
6. **CSV import**: edit that exported CSV (e.g. add a new row), then click **Import CSV** and select the file — confirm the new row appears as a new product, and any intentionally broken rows are reported without blocking the good ones.

---

## API breaking change note

`GET /api/products` response shape changed from a plain array to
`{ items: [...], pagination: {...} }`. If you were calling this
endpoint directly (outside the provided frontend), update accordingly.
