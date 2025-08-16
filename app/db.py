from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Resolve a writable data directory:
# - Dev: <repo-root>/data
# - Packaged (PyInstaller): <exe-dir>/data
if getattr(sys, "frozen", False):
    APP_HOME = Path(sys.executable).resolve().parent  # EXE directory
else:
    APP_HOME = Path(__file__).resolve().parents[1]  # repo root

DATA_DIR = APP_HOME / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "crispino.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_schema() -> None:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price_cents INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                available INTEGER NOT NULL DEFAULT 1,
                sort_order INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(category_id) REFERENCES categories(id)
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                number INTEGER NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                total_cents INTEGER NOT NULL,
                tax_cents INTEGER NOT NULL,
                paid_cents INTEGER NOT NULL DEFAULT 0,
                payment_method TEXT NOT NULL,
                note TEXT DEFAULT ''
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                unit_price_cents INTEGER NOT NULL,
                qty INTEGER NOT NULL,
                category_name TEXT NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            );
            """
        )

        # Defaults
        if not get_setting("cafe_name", conn=conn):
            set_setting("cafe_name", "Crispino Cafe", conn=conn)
        if not get_setting("tax_rate_percent", conn=conn):
            set_setting("tax_rate_percent", "0", conn=conn)
        if not get_setting("admin_pin", conn=conn):
            set_setting("admin_pin", "1234", conn=conn)
        if not get_setting("order_seq", conn=conn):
            set_setting("order_seq", "1000", conn=conn)

        # Best-effort unique indexes (skip if current data violates)
        try:
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_categories_name_nocase ON categories(lower(name))")
        except Exception:
            pass
        try:
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_items_cat_name_nocase ON items(category_id, lower(name))"
            )
        except Exception:
            pass

        # Seed demo data if empty
        cnt = cur.execute("SELECT COUNT(*) AS c FROM items").fetchone()["c"]
        if cnt == 0:
            seed_menu(conn)
        conn.commit()
    finally:
        conn.close()


def seed_menu(conn: Optional[sqlite3.Connection] = None) -> None:
    close_after = False
    if conn is None:
        conn = connect()
        close_after = True
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO categories(name, sort_order) VALUES(?,?)", ("Coffee", 1))
        cur.execute("INSERT INTO categories(name, sort_order) VALUES(?,?)", ("Tea", 2))
        cur.execute("INSERT INTO categories(name, sort_order) VALUES(?,?)", ("Snacks", 3))
        cat_ids = {row["name"]: row["id"] for row in cur.execute("SELECT id, name FROM categories")}
        items = [
            ("Espresso", 300, cat_ids["Coffee"], 1, 1),
            ("Americano", 350, cat_ids["Coffee"], 1, 2),
            ("Latte", 450, cat_ids["Coffee"], 1, 3),
            ("Cappuccino", 450, cat_ids["Coffee"], 1, 4),
            ("Black Tea", 250, cat_ids["Tea"], 1, 1),
            ("Green Tea", 300, cat_ids["Tea"], 1, 2),
            ("Chai", 350, cat_ids["Tea"], 1, 3),
            ("Blueberry Muffin", 275, cat_ids["Snacks"], 1, 1),
            ("Croissant", 300, cat_ids["Snacks"], 1, 2),
            ("Chocolate Chip Cookie", 200, cat_ids["Snacks"], 1, 3),
        ]
        cur.executemany(
            "INSERT INTO items(name, price_cents, category_id, available, sort_order) VALUES(?,?,?,?,?)",
            items,
        )
    finally:
        if close_after:
            conn.close()


def get_setting(key: str, *, conn: Optional[sqlite3.Connection] = None) -> Optional[str]:
    close_after = False
    if conn is None:
        conn = connect()
        close_after = True
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None
    finally:
        if close_after:
            conn.close()


def set_setting(key: str, value: str, *, conn: Optional[sqlite3.Connection] = None) -> None:
    close_after = False
    if conn is None:
        conn = connect()
        close_after = True
    try:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        conn.commit()
    finally:
        if close_after:
            conn.close()


def list_categories() -> List[sqlite3.Row]:
    conn = connect()
    try:
        sql = """
            SELECT c.*, (
                SELECT COUNT(*) FROM items i WHERE i.category_id = c.id
            ) AS item_count
            FROM categories c
            ORDER BY c.sort_order, c.name
        """
        return list(conn.execute(sql))
    finally:
        conn.close()


def list_items(include_unavailable: bool = False) -> List[sqlite3.Row]:
    conn = connect()
    try:
        if include_unavailable:
            sql = """SELECT i.*, c.name AS category_name
                     FROM items i JOIN categories c ON i.category_id=c.id
                     ORDER BY c.sort_order, i.sort_order, i.name"""
            return list(conn.execute(sql))
        sql = """SELECT i.*, c.name AS category_name
                 FROM items i JOIN categories c ON i.category_id=c.id
                 WHERE i.available=1
                 ORDER BY c.sort_order, i.sort_order, i.name"""
        return list(conn.execute(sql))
    finally:
        conn.close()


def _next_category_sort(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM categories").fetchone()
    return int(row["m"]) + 1


def _next_item_sort(conn: sqlite3.Connection, category_id: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(sort_order), 0) AS m FROM items WHERE category_id=?",
        (category_id,),
    ).fetchone()
    return int(row["m"]) + 1


def _category_exists(name: str, conn: sqlite3.Connection, *, exclude_id: Optional[int] = None) -> bool:
    name = (name or "").strip()
    if not name:
        return False
    if exclude_id is None:
        sql = "SELECT 1 FROM categories WHERE lower(name)=lower(?) LIMIT 1"
        row = conn.execute(sql, (name,)).fetchone()
    else:
        sql = "SELECT 1 FROM categories WHERE lower(name)=lower(?) AND id<>? LIMIT 1"
        row = conn.execute(sql, (name, exclude_id)).fetchone()
    return row is not None


def _item_exists_in_category(
    name: str, category_id: int, conn: sqlite3.Connection, *, exclude_id: Optional[int] = None
) -> bool:
    name = (name or "").strip()
    if not name:
        return False
    if exclude_id is None:
        sql = "SELECT 1 FROM items WHERE category_id=? AND lower(name)=lower(?) LIMIT 1"
        row = conn.execute(sql, (category_id, name)).fetchone()
    else:
        sql = "SELECT 1 FROM items WHERE category_id=? AND lower(name)=lower(?) AND id<>? LIMIT 1"
        row = conn.execute(sql, (category_id, name, exclude_id)).fetchone()
    return row is not None


def create_category(name: str, sort_order: Optional[int] = None) -> int:
    conn = connect()
    try:
        name = name.strip()
        if not name:
            raise ValueError("Category name cannot be blank.")
        if _category_exists(name, conn):
            raise ValueError(f'Category "{name}" already exists.')
        if sort_order is None or sort_order <= 0:
            sort_order = _next_category_sort(conn)
        cur = conn.execute("INSERT INTO categories(name, sort_order) VALUES(?,?)", (name, sort_order))
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def create_item(
    name: str,
    price_cents: int,
    category_id: int,
    available: bool = True,
    sort_order: Optional[int] = None,
) -> int:
    conn = connect()
    try:
        name = name.strip()
        if not name:
            raise ValueError("Item name cannot be blank.")
        if _item_exists_in_category(name, category_id, conn):
            cat = conn.execute("SELECT name FROM categories WHERE id=?", (category_id,)).fetchone()
            cat_name = cat["name"] if cat else f"#{category_id}"
            raise ValueError(f'Item "{name}" already exists in category "{cat_name}".')
        if sort_order is None or sort_order <= 0:
            sort_order = _next_item_sort(conn, category_id)
        cur = conn.execute(
            "INSERT INTO items(name, price_cents, category_id, available, sort_order) VALUES(?,?,?,?,?)",
            (name, price_cents, category_id, 1 if available else 0, sort_order),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def update_item(
    item_id: int,
    *,
    name: Optional[str] = None,
    price_cents: Optional[int] = None,
    category_id: Optional[int] = None,
    available: Optional[bool] = None,
    sort_order: Optional[int] = None,
) -> bool:
    conn = connect()
    try:
        if name is not None or category_id is not None:
            current = conn.execute("SELECT name, category_id FROM items WHERE id=?", (item_id,)).fetchone()
            if not current:
                return False
            new_name = (name if name is not None else current["name"]).strip()
            new_cat = category_id if category_id is not None else int(current["category_id"])
            if not new_name:
                raise ValueError("Item name cannot be blank.")
            if _item_exists_in_category(new_name, new_cat, conn, exclude_id=item_id):
                cat = conn.execute("SELECT name FROM categories WHERE id=?", (new_cat,)).fetchone()
                cat_name = cat["name"] if cat else f"#{new_cat}"
                raise ValueError(f'Item "{new_name}" already exists in category "{cat_name}".')

        fields = []
        params: List[Any] = []
        if name is not None:
            fields.append("name=?")
            params.append(name.strip())
        if price_cents is not None:
            fields.append("price_cents=?")
            params.append(price_cents)
        if category_id is not None:
            fields.append("category_id=?")
            params.append(category_id)
        if available is not None:
            fields.append("available=?")
            params.append(1 if available else 0)
        if sort_order is not None:
            fields.append("sort_order=?")
            params.append(sort_order)
        if not fields:
            return False
        params.append(item_id)
        cur = conn.execute(f"UPDATE items SET {', '.join(fields)} WHERE id=?", params)
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_item(item_id: int) -> bool:
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_category(category_id: int) -> bool:
    conn = connect()
    try:
        row = conn.execute("SELECT COUNT(*) AS c FROM items WHERE category_id=?", (category_id,)).fetchone()
        if int(row["c"]) > 0:
            return False
        cur = conn.execute("DELETE FROM categories WHERE id=?", (category_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def list_menu_grouped() -> Dict[str, List[Dict[str, Any]]]:
    cats = list_categories()
    items = list_items()
    groups: Dict[str, List[Dict[str, Any]]] = {c["name"]: [] for c in cats}
    for i in items:
        groups.setdefault(i["category_name"], []).append(
            {"id": i["id"], "name": i["name"], "price_cents": i["price_cents"], "category": i["category_name"]}
        )
    return groups


# Backward-compat: used by main.py
get_menu_grouped = list_menu_grouped


@dataclass
class Order:
    id: int
    number: int
    created_at: str
    total_cents: int
    tax_cents: int
    paid_cents: int
    payment_method: str
    note: str


def _next_order_number(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT value FROM settings WHERE key='order_seq'").fetchone()
    current = int(row["value"]) if row else 1000
    next_num = current + 1
    conn.execute(
        "INSERT INTO settings(key, value) VALUES('order_seq', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(next_num),),
    )
    return next_num


def get_order(order_id: int) -> Tuple[Order, List[sqlite3.Row]]:
    conn = connect()
    try:
        o = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not o:
            raise ValueError("Order not found")
        items = list(conn.execute("SELECT * FROM order_items WHERE order_id=? ORDER BY id", (order_id,)))
        order = Order(
            id=o["id"],
            number=o["number"],
            created_at=o["created_at"],
            total_cents=o["total_cents"],
            tax_cents=o["tax_cents"],
            paid_cents=o["paid_cents"],
            payment_method=o["payment_method"],
            note=o["note"] or "",
        )
        return order, items
    finally:
        conn.close()


def _lookup_items(item_quantities: Dict[int, int], conn: sqlite3.Connection) -> List[sqlite3.Row]:
    ids = list(item_quantities.keys())
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    sql = f"SELECT i.*, c.name AS category_name FROM items i JOIN categories c ON i.category_id=c.id WHERE i.id IN ({placeholders})"
    return list(conn.execute(sql, ids))


def create_order_from_cart(
    cart_lines: List[Dict[str, Any]],
    payment_method: str,
    cash_received_cents: int,
    note: str,
) -> int:
    conn = connect()
    try:
        with conn:
            item_quantities: Dict[int, int] = {}
            for line in cart_lines:
                iid = int(line["item_id"])
                qty = int(line["qty"])
                if qty <= 0:
                    continue
                item_quantities[iid] = item_quantities.get(iid, 0) + qty

            if not item_quantities:
                raise ValueError("Cart is empty")

            rows = _lookup_items(item_quantities, conn)
            if not rows:
                raise ValueError("No valid items in cart")

            tax_rate_percent = float(get_setting("tax_rate_percent", conn=conn) or "0")
            subtotal = 0
            for r in rows:
                subtotal += int(r["price_cents"]) * item_quantities[int(r["id"])]
            tax_cents = round(subtotal * tax_rate_percent / 100.0)
            total_cents = subtotal + tax_cents

            order_number = _next_order_number(conn)
            created = now_iso()

            cur = conn.execute(
                "INSERT INTO orders(number, created_at, total_cents, tax_cents, paid_cents, payment_method, note) VALUES(?,?,?,?,?,?,?)",
                (order_number, created, total_cents, tax_cents, cash_received_cents, payment_method, note),
            )
            order_id = int(cur.lastrowid)

            for r in rows:
                iid = int(r["id"])
                qty = item_quantities[iid]
                conn.execute(
                    "INSERT INTO order_items(order_id, item_id, name, unit_price_cents, qty, category_name) VALUES(?,?,?,?,?,?)",
                    (order_id, iid, r["name"], int(r["price_cents"]), qty, r["category_name"]),
                )
            return order_id
    finally:
        conn.close()


def renumber_categories_and_items() -> None:
    """Renumber categories 1..N and items 1..N by current order; update references."""
    conn = connect()
    try:
        with conn:
            cur = conn.cursor()
            # Categories
            cat_rows = list(
                cur.execute("SELECT id, name, sort_order FROM categories ORDER BY sort_order, name, id")
            )
            cat_map = {r["id"]: idx + 1 for idx, r in enumerate(cat_rows)}
            if any(old != new for old, new in cat_map.items()):
                cur.execute(
                    "CREATE TABLE categories_new (id INTEGER PRIMARY KEY, name TEXT NOT NULL, sort_order INTEGER NOT NULL DEFAULT 0)"
                )
                for r in cat_rows:
                    new_id = cat_map[r["id"]]
                    cur.execute(
                        "INSERT INTO categories_new(id, name, sort_order) VALUES(?,?,?)",
                        (new_id, r["name"], r["sort_order"]),
                    )
                for old_id, new_id in cat_map.items():
                    if old_id != new_id:
                        cur.execute("UPDATE items SET category_id=? WHERE category_id=?", (new_id, old_id))
                cur.execute("DROP TABLE categories")
                cur.execute("ALTER TABLE categories_new RENAME TO categories")

            # Items
            item_rows = list(
                cur.execute(
                    """SELECT i.id, i.name, i.price_cents, i.category_id, i.available, i.sort_order
                       FROM items i
                       JOIN categories c ON i.category_id=c.id
                       ORDER BY c.sort_order, c.name, i.sort_order, i.name, i.id"""
                )
            )
            item_map = {r["id"]: idx + 1 for idx, r in enumerate(item_rows)}
            if any(old != new for old, new in item_map.items()):
                cur.execute(
                    "CREATE TABLE items_new (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price_cents INTEGER NOT NULL, category_id INTEGER NOT NULL, available INTEGER NOT NULL DEFAULT 1, sort_order INTEGER NOT NULL DEFAULT 0)"
                )
                for r in item_rows:
                    new_id = item_map[r["id"]]
                    cur.execute(
                        "INSERT INTO items_new(id, name, price_cents, category_id, available, sort_order) VALUES(?,?,?,?,?,?)",
                        (new_id, r["name"], r["price_cents"], r["category_id"], r["available"], r["sort_order"]),
                    )
                for old_id, new_id in item_map.items():
                    if old_id != new_id:
                        cur.execute("UPDATE order_items SET item_id=? WHERE item_id=?", (new_id, old_id))
                cur.execute("DROP TABLE items")
                cur.execute("ALTER TABLE items_new RENAME TO items")
    finally:
        conn.close()