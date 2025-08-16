from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db

app = FastAPI(title="Crispino Cafe POS")

# Support frozen/packaged (PyInstaller) and dev
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS) / "app"  # type: ignore[attr-defined]
else:
    BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.on_event("startup")
def startup() -> None:
    db.ensure_schema()


@app.get("/", response_class=HTMLResponse)
def pos(request: Request):
    menu = db.get_menu_grouped()
    cafe_name = db.get_setting("cafe_name") or "Crispino Cafe"
    tax_rate = float(db.get_setting("tax_rate_percent") or "0")
    return templates.TemplateResponse(
        "pos.html",
        {"request": request, "menu": menu, "cafe_name": cafe_name, "tax_rate": tax_rate},
    )


@app.post("/checkout")
def checkout(
    request: Request,
    cart_json: str = Form(...),
    payment_method: str = Form("cash"),
    cash_received: int = Form(0),  # paisa (minor unit)
    note: str = Form(""),
):
    try:
        cart_lines = json.loads(cart_json)
        if not isinstance(cart_lines, list):
            raise ValueError("Invalid cart")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cart")

    if payment_method not in ("cash", "card", "other"):
        raise HTTPException(status_code=400, detail="Invalid payment method")

    try:
        cash_received_cents = int(cash_received)
    except Exception:
        cash_received_cents = 0

    try:
        order_id = db.create_order_from_cart(
            cart_lines=cart_lines,
            payment_method=payment_method,
            cash_received_cents=cash_received_cents,
            note=note or "",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    next_url = request.url_for("print_kitchen", order_id=order_id)
    back_url = request.url_for("pos")
    customer_url = request.url_for("print_customer", order_id=order_id)
    return RedirectResponse(f"{customer_url}?next={next_url}&back={back_url}", status_code=303)


@app.get("/print/customer/{order_id}", response_class=HTMLResponse)
def print_customer(request: Request, order_id: int, next: str = "", back: str = ""):
    order, items = db.get_order(order_id)
    cafe_name = db.get_setting("cafe_name") or "Crispino Cafe"
    return templates.TemplateResponse(
        "print_customer.html",
        {"request": request, "order": order, "items": items, "cafe_name": cafe_name, "next_url": next, "back_url": back},
    )


@app.get("/print/kitchen/{order_id}", response_class=HTMLResponse)
def print_kitchen(request: Request, order_id: int, back: str = ""):
    order, items = db.get_order(order_id)
    cafe_name = db.get_setting("cafe_name") or "Crispino Cafe"
    return templates.TemplateResponse(
        "print_kitchen.html",
        {"request": request, "order": order, "items": items, "cafe_name": cafe_name, "back_url": back or request.url_for("pos")},
    )


# --- Admin ---

@app.get("/admin", response_class=HTMLResponse)
def admin_home(request: Request):
    cats = db.list_categories()
    items = db.list_items(include_unavailable=True)
    cafe_name = db.get_setting("cafe_name") or "Crispino Cafe"
    tax_rate = db.get_setting("tax_rate_percent") or "0"
    error = request.query_params.get("error", "")
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "categories": cats, "items": items, "cafe_name": cafe_name, "tax_rate": tax_rate, "error": error},
    )


@app.post("/admin/category/new")
def admin_new_category(name: str = Form(...), sort_order: Optional[str] = Form("")):
    so: Optional[int] = None
    try:
        if sort_order and int(sort_order) > 0:
            so = int(sort_order)
    except Exception:
        so = None
    try:
        db.create_category(name, so)
    except ValueError as e:
        return RedirectResponse(f"/admin?error={str(e)}", status_code=303)
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/category/delete")
def admin_delete_category(category_id: int = Form(...)):
    ok = db.delete_category(category_id)
    if not ok:
        return RedirectResponse("/admin?error=Cannot delete category: it still has items.", status_code=303)
    db.renumber_categories_and_items()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/item/new")
def admin_new_item(
    name: str = Form(...),
    price_rupees: float = Form(...),
    category_id: int = Form(...),
    available: str = Form("1"),
    sort_order: Optional[str] = Form(""),
):
    price_cents = int(round(float(price_rupees) * 100))
    so: Optional[int] = None
    try:
        if sort_order and int(sort_order) > 0:
            so = int(sort_order)
    except Exception:
        so = None
    try:
        db.create_item(name, price_cents, category_id, available == "1", so)
    except ValueError as e:
        return RedirectResponse(f"/admin?error={str(e)}", status_code=303)
    db.renumber_categories_and_items()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/item/update")
def admin_update_item(
    item_id: int = Form(...),
    name: str = Form(...),
    price_rupees: float = Form(...),
    category_id: int = Form(...),
    available: str = Form("1"),
    sort_order: int = Form(0),
):
    price_cents = int(round(float(price_rupees) * 100))
    try:
        db.update_item(
            item_id,
            name=name,
            price_cents=price_cents,
            category_id=category_id,
            available=(available == "1"),
            sort_order=sort_order,
        )
    except ValueError as e:
        return RedirectResponse(f"/admin?error={str(e)}", status_code=303)
    db.renumber_categories_and_items()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/item/delete")
def admin_delete_item(item_id: int = Form(...)):
    ok = db.delete_item(item_id)
    if not ok:
        return RedirectResponse("/admin?error=Failed to delete item.", status_code=303)
    db.renumber_categories_and_items()
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/settings")
def admin_settings(cafe_name: str = Form(...), tax_rate_percent: float = Form(...)):
    db.set_setting("cafe_name", cafe_name)
    db.set_setting("tax_rate_percent", str(tax_rate_percent))
    return RedirectResponse("/admin", status_code=303)


# Renumber endpoint (supports both POST button and direct GET)
@app.post("/admin/renumber")
@app.get("/admin/renumber")
def admin_renumber(request: Request):
    db.renumber_categories_and_items()
    return RedirectResponse("/admin", status_code=303)