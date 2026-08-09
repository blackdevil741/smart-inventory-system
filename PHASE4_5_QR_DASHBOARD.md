# Phase 4 + 5 — QR System & Real Dashboard

Combined into one pass: QR code generation + real webcam scanning, and
a real Dashboard replacing the earlier placeholder.

---

## What's new

### QR System (backend)
- `services/qr_service.py` — generates a QR code PNG (as a base64 data URL, no file storage needed) encoding `product:<firestore-id>`
- `routes/qr_routes.py`:
  - `GET /api/qr/<product_id>` — generate a QR image for a product
  - `GET /api/qr/resolve/<product_id>` — look up a product from a scanned code

### QR System (frontend)
- Inventory table now has a **QR** button per row → opens a modal showing the code, with a **Download QR** button
- `pages/qr-scanner.html` + `js/pages/qr-scanner.js` — a real webcam-based scanner page using the `html5-qrcode` library:
  - Click "Start camera" → browser asks for camera permission → live video feed with a scan box overlay
  - On a successful scan, calls the backend to confirm the product exists, then shows its name/SKU/category/quantity
  - Quick +1/+5/+10/-1/-5/-10 stock buttons right there, so you can scan-and-adjust at the till without opening the full inventory table

**Note:** camera access requires `https://` or `localhost` — this works out of the box in local dev (`http://localhost:5500`) and will keep working once deployed via Firebase Hosting (Phase 10), which serves over HTTPS by default.

### Real Dashboard (backend)
- `services/dashboard_service.py` — aggregates: total products, low-stock count, out-of-stock count, category count, total stock value (at cost), a low-stock items list, and a recent activity feed (from the `logs` collection written in Phase 3)
- `routes/dashboard_routes.py`:
  - `GET /api/dashboard/summary`
  - `GET /api/dashboard/activity?limit=15`

### Real Dashboard (frontend)
- `pages/dashboard.html` fully replaces the old placeholder — five summary cards, a "needs attention" low-stock list, and a live activity feed showing what was added/edited/deleted/adjusted and when ("2h ago", etc.)

---

## How to test this locally

1. Backend running (`python app.py`), frontend running (`python -m http.server 5500`).
2. Log in, land on the real **Dashboard** — you should see your product counts and recent activity from Phase 3 testing already showing up.
3. Go to **Inventory**, click the **QR** button on a product → confirm a QR code image appears and downloads correctly.
4. Go to **QR Scanner** → click **Start camera** → allow camera permission when your browser prompts.
5. Either:
   - Display the downloaded QR image on your phone screen and point your laptop camera at it, or
   - Print/open the QR image on a second device
   and confirm the scanner picks it up and shows the product with working stock buttons.
6. Adjust stock from the scanner, then go back to **Dashboard** — confirm the activity feed shows the new entry, and summary cards update.

---

## Known limitations (by design, for this phase)

- The scanner defaults to the rear/environment-facing camera (`facingMode: "environment"`) which matters most on phones; on a laptop with only one camera, it'll just use that one.
- No dedicated barcode support yet (QR only) — listed as a future enhancement in the README.
