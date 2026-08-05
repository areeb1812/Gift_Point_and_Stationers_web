# Inventory Management System — GiftPoint

A proof-of-concept Information System for a small stationery / gift shop
("GiftPoint"). Built with a **Flask JSON API + SQLite** backend and a
**vanilla HTML / CSS / JavaScript** frontend that talks to the API purely
through `fetch()` — no post-and-refresh, no server-rendered templates.

---

## 1. What the system covers

Full CRUD is implemented on the two core entities of the business, plus a
transactional checkout flow that ties everything together.

| Area                | Endpoints                                                    | CRUD           |
| ------------------- | ------------------------------------------------------------ | -------------- |
| Authentication      | `POST /api/auth/login`                                       | — (validation) |
| Products            | `GET/POST /api/products`, `PUT/DELETE /api/products/<id>`    | C R U D        |
| Customers (loyalty) | `GET/POST /api/customers`, `DELETE /api/customers/<phone>`   | C R D          |
| Orders / Checkout   | `POST /api/orders` (multi-item, atomic, stock + loyalty)     | C              |
| Reporting           | `GET /api/sales/overview`, `/api/sales/recent`, `/invoice/<id>` | R           |
| Exchange rate proxy | `GET /api/exchange-rate` (live API + offline fallback)       | R              |

Additional non-CRUD requirements met: users & roles (admin / employee /
owner), search (products by name, customers by phone), sorting (recent
sales), input validation (numeric, non-empty, non-negative), referential
integrity (FKs), transactional integrity (BEGIN / ROLLBACK on checkout),
and reporting.

---

## 2. Project layout

```
inventory_management_system/
├── app.py            # Flask app + REST API + serves the frontend
├── database.py       # SQLite schema + seed data
├── test_app.py       # 8 unit tests + 1 integration test (unittest)
├── requirements.txt  # Flask, Flask-CORS
├── index.html        # Single-page frontend
├── style.css         # Frontend styling
├── app.js            # Frontend logic — all API calls via fetch()
└── inventory.db      # Created automatically on first run
```

---

## 3. Fixes applied to the original submission

1. **`sqlite3.IntegrityError` was referenced but `sqlite3` was never
   imported in `app.py`** — inserting a customer with a duplicate phone
   number crashed the server with `NameError`. Fixed by adding
   `import sqlite3`.
2. **`DB_PATH` used `dirname(dirname(__file__))`**, which put
   `inventory.db` one folder *above* the project — tests and the app
   pointed to different files depending on the working directory.
   Corrected to the folder containing `database.py`.
3. **`init_db()` was never called by `app.py`** — running
   `python app.py` on a clean checkout produced `no such table: Product`.
   `init_db()` now runs on startup.
4. **The frontend had to be opened manually as `file://`** — Flask now
   serves `index.html` / `app.js` / `style.css` from `/`, so a single
   command starts the whole app.

Verification: all 9 tests in `test_app.py` pass, and manual smoke tests
of `GET /`, `GET /api/products`, and duplicate-phone `POST /api/customers`
all behave correctly.

---

## 4. How to run the project — step by step

### Prerequisites

- Python **3.9+** (tested on 3.13)
- `pip`
- Any modern browser

### Step 1 — Get the code

```bash
git clone <your-repo-url>
cd inventory_management_system
```

### Step 2 — (Recommended) create a virtual environment

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Run the server

```bash
python app.py
```

On first launch, `inventory.db` is created and seeded automatically with
sample users, products, customers, and two historical orders. You should
see:

```
 * Running on http://127.0.0.1:5000
```

### Step 5 — Open the app

Go to **http://127.0.0.1:5000/** in your browser. The frontend loads and
immediately calls the API via `fetch()`.

### Step 6 — Log in

Three seeded accounts are available:

| Role     | User ID | Name   | Password    |
| -------- | ------- | ------ | ----------- |
| Admin    | 1       | Admin  | `admin123`  |
| Employee | 241462  | Aruj   | `aruj123`   |
| Owner    | 3       | Owner  | `owner123`  |

Each role sees a different section of the UI (product management,
checkout, or sales reporting).

### Step 7 — Run the tests

In a second terminal (with the venv activated):

```bash
python -m unittest test_app.py -v
```

Expected output: **9 passed** (8 unit tests + 1 end-to-end checkout
integration test that verifies stock decrement, loyalty accrual, and
order + order-item persistence in a single transaction).

### Step 8 — Reset the database (optional)

Stop the server and delete `inventory.db`; it will be recreated and
reseeded on the next `python app.py`.

---

## 5. Manual API smoke test (optional)

With the server running:

```bash
# List products
curl http://127.0.0.1:5000/api/products

# Create a product
curl -X POST http://127.0.0.1:5000/api/products \
     -H "Content-Type: application/json" \
     -d '{"name":"Eraser","description":"Soft","price":30,"stockQty":100}'

# Sales overview
curl http://127.0.0.1:5000/api/sales/overview
```

---

## 6. Attribution

- **Flask 3.0.3** and **Flask-CORS 4.0.1** — BSD-3-Clause. See
  `requirements.txt`.
- Live currency data from **open.er-api.com** (free tier, no key
  required); the backend falls back to hardcoded rates if the service is
  unreachable.
- All application code (schema, endpoints, frontend, tests) is original
  to this project.
