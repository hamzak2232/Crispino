from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import db

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

    # Get the order number for client-side tracking
    order, _ = db.get_order(order_id)
    
    next_url = request.url_for("print_kitchen", order_id=order_id)
    back_url = request.url_for("pos")
    customer_url = request.url_for("print_customer", order_id=order_id)
    
    # Add order number to URL for client-side tracking
    return RedirectResponse(f"{customer_url}?next={next_url}&back={back_url}&order_number={order.number}", status_code=303)


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


# --- New API Endpoints ---

@app.get("/api/orders/recent")
def api_recent_orders(limit: int = 10):
    """Get recent orders for order history."""
    try:
        orders = db.get_recent_orders(limit)
        return {"orders": [dict(order) for order in orders]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/daily")
def api_daily_report(date: str = None):
    """Get daily sales report."""
    try:
        report = db.get_daily_report(date)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orders/search")
def api_search_orders(q: str, limit: int = 20):
    """Search orders by number, note, or item names."""
    try:
        orders = db.search_orders(q, limit)
        return {"orders": [dict(order) for order in orders]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orders/{order_number}")
def api_get_order_by_number(order_number: int):
    """Get order by order number."""
    try:
        result = db.get_order_by_number(order_number)
        if not result:
            raise HTTPException(status_code=404, detail="Order not found")
        order, items = result
        return {
            "order": {
                "id": order.id,
                "number": order.number,
                "created_at": order.created_at,
                "total_cents": order.total_cents,
                "tax_cents": order.tax_cents,
                "paid_cents": order.paid_cents,
                "payment_method": order.payment_method,
                "note": order.note
            },
            "items": [dict(item) for item in items]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/items/popular")
def api_popular_items(days: int = 7, limit: int = 10):
    """Get most popular items in the last N days."""
    try:
        items = db.get_popular_items(days, limit)
        return {"items": [dict(item) for item in items]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/backup")
def api_create_backup():
    """Create a database backup."""
    try:
        backup_path = db.backup_database()
        return {"message": "Backup created successfully", "path": backup_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/export")
def api_export_data(format: str = "json"):
    """Export all data."""
    try:
        export_path = db.export_data(format)
        return {"message": "Data exported successfully", "path": export_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- New Admin Pages ---

@app.get("/admin/reports", response_class=HTMLResponse)
def admin_reports(request: Request, date: str = None):
    """Daily reports page."""
    try:
        report = db.get_daily_report(date)
        cafe_name = db.get_setting("cafe_name") or "Crispino Cafe"
        return templates.TemplateResponse(
            "reports.html",
            {"request": request, "report": report, "cafe_name": cafe_name, "date": date or datetime.now().strftime("%Y-%m-%d")},
        )
    except Exception as e:
        return RedirectResponse(f"/admin?error={str(e)}", status_code=303)


@app.get("/admin/history", response_class=HTMLResponse)
def admin_history(request: Request, q: str = ""):
    """Order history page."""
    try:
        if q:
            orders = db.search_orders(q, 50)
        else:
            orders = db.get_recent_orders(50)
        cafe_name = db.get_setting("cafe_name") or "Crispino Cafe"
        return templates.TemplateResponse(
            "history.html",
            {"request": request, "orders": orders, "cafe_name": cafe_name, "search_query": q},
        )
    except Exception as e:
        return RedirectResponse(f"/admin?error={str(e)}", status_code=303)