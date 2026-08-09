# Phase 6 + 7 — Analytics & Reports

Combined into one pass: real Chart.js analytics backed by Firestore
aggregation, and downloadable PDF/CSV reports.

---

## What's new

### Analytics (backend)
- `services/analytics_service.py`:
  - `get_category_distribution()` — product count + total quantity per category
  - `get_monthly_growth()` — products added per month, last 6 months (including empty months)
  - `get_stock_value_breakdown()` — cost value + potential revenue per category, plus totals and potential profit
  - `get_most_active_products()` — approximates "most sold" from recorded `stock_decreased` log entries (this app doesn't track point-of-sale transactions, so this is clearly labeled as an approximation, not exact sales data)
- `routes/analytics_routes.py`:
  - `GET /api/analytics/category-distribution`
  - `GET /api/analytics/monthly-growth`
  - `GET /api/analytics/stock-value`
  - `GET /api/analytics/most-active-products?limit=5`
- All aggregation math is unit-tested against fake data (category totals, stock value calculations, month rollover logic).

### Analytics (frontend)
- `pages/analytics.html` + `js/pages/analytics.js` — real Chart.js visualizations:
  - Pie chart: category distribution by quantity
  - Bar chart: stock value by category
  - Bar chart: monthly inventory growth
  - List: most active products (with the approximation caveat shown in the UI, not just the API)
  - Three stat highlights: total cost value, potential revenue, potential profit

### Reports (backend)
- `services/report_service.py` — builds three report types (Inventory, Stock Value, Low Stock) and exports each as either PDF (via `reportlab`, styled to match the app's palette) or CSV, entirely in memory (no temp files, no Firebase Storage needed)
- `routes/reports_routes.py`:
  - `GET /api/reports/<report_type>?format=pdf|csv` — streams the file back as a direct download
- Verified: generated PDFs start with a real `%PDF` header and generated CSVs contain correctly formatted, sorted data.

### Reports (frontend)
- `pages/reports.html` + `js/pages/reports.js` — three report cards (Inventory / Stock Value / Low Stock), each with a **Download PDF** and **Download CSV** button that triggers a real browser file download.

---

## How to test this locally

1. Backend + frontend running as usual, logged in with a few test products (ideally some low-stock/out-of-stock ones, and some stock adjustments made via Inventory or the QR Scanner, so the "Most Active Products" list has data).
2. Go to **Analytics** — confirm the pie chart, bar charts, and stat highlights reflect your actual product data.
3. Go to **Reports** — click each **Download PDF** and **Download CSV** button, confirm files download and open correctly (PDF should look like a clean styled table; CSV should open cleanly in Excel/Sheets).

---

## Known limitations (by design, for this phase)

- "Most Active Products" is an approximation based on recorded stock decreases, not true point-of-sale data — this is intentional (the app doesn't have a checkout/sales module) and is labeled as such in both the API response and the UI.
- Monthly growth is based on `created_at` timestamps of products, so it reflects when products were *added to the system*, not necessarily when they were first stocked in real life.
