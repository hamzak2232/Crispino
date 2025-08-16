# Crispino Cafe — Local POS (FastAPI + SQLite)

A simple point‑of‑sale web app for the cashier:
- Tap/click items to add them to the order
- Adjust quantities with +/- controls
- Place order and automatically print two slips:
  - Customer receipt (order number, items, prices, totals)
  - Kitchen slip (order number, items and quantities)
- Minimal Admin to manage categories and items (name, price, availability)
- Local SQLite database (no internet required)

## Requirements
- Windows/macOS/Linux with Python 3.11+
- A web browser (Edge/Chrome/Firefox/Safari)
- A printer connected to your machine (for receipts)

## Setup (Windows PowerShell)
```powershell
# 1) Create folders and files from this repository layout
#    Make sure the tree looks like this:
# .
# ├─ app
# │  ├─ db.py
# │  ├─ main.py
# │  ├─ templates
# │  │  ├─ base.html
# │  │  ├─ pos.html
# │  │  ├─ print_customer.html
# │  │  ├─ print_kitchen.html
# │  │  └─ admin.html
# │  └─ static
# │     ├─ pos.js
# │     └─ style.css
# ├─ data (auto-created on first run)
# └─ requirements.txt

# 2) Create and activate a virtual environment
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# 3) Install dependencies
pip install -r requirements.txt

# 4) Run the server
uvicorn app.main:app --reload

# 5) Open in your browser
# POS (cashier): http://127.0.0.1:8000/
# Admin (menu management): http://127.0.0.1:8000/admin
```

## Using the POS
- Click a category tab to view its items.
- Click items to add to the current order.
- Adjust quantities with the +/- controls or type a number.
- Add an optional note (e.g., "no sugar").
- Choose payment method. If cash, enter amount received in pence; change is printed on the receipt.
- Click "Place Order & Print":
  - First, the Customer receipt prints, then it automatically moves to the Kitchen slip, prints, and returns to the POS screen.
  - If your browser blocks printing, allow pop‑ups/printing for the local site.

## Admin
- Change cafe name and tax rate (%). Tax is applied to the order total.
- Add categories.
- Add/edit items (prices are in pence to avoid rounding issues).
- Toggle availability (unavailable items are hidden on the POS).

## Data and Defaults
- SQLite file: `./data/crispino.db` (auto‑created)
- Defaults on first run:
  - Cafe name: "Crispino Cafe"
  - Tax rate: 0%
  - Admin PIN: 1234 (not enforced in UI for simplicity)
  - Starting order number: 1001 (increments)

## Printing Notes
- This app uses the browser's print dialog. Set your desired printer as default for quick printing.
- Receipts are simple text layouts for 80mm thermal printers and standard A4/Letter.
- If you have separate customer/kitchen printers, you can choose the printer in each dialog.
- To target a specific printer automatically, we’d need a native integration (ESC/POS or a print agent). I can add that if you want.

## Customizations
- Add item options (e.g., sizes, milk types)
- Discount buttons or % off
- Dine‑in vs. takeaway markers
- Reprint last order button
- Order history and daily Z report
- Multiple cashier logins with PINs

Open an issue or ask here for any of these and I’ll extend the app.