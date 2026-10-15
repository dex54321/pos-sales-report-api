"""Report queries. Pure functions over a Session, so they are easy to test.

All queries run in the database (aggregates, grouping, ordering), and work on
both SQLite and PostgreSQL.
"""

from datetime import date, datetime, time, timedelta
from typing import Literal

from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from .models import Product, Sale, SaleItem

SortKey = Literal["revenue", "profit", "quantity"]


def _revenue():
    return func.coalesce(func.sum(SaleItem.quantity * SaleItem.unit_price), 0)


def _cost():
    return func.coalesce(func.sum(SaleItem.quantity * SaleItem.unit_cost), 0)


def _items_with_sales() -> Select:
    return select().select_from(SaleItem).join(Sale, SaleItem.sale_id == Sale.id)


def _in_range(stmt: Select, start: date | None, end: date | None) -> Select:
    """Filter by sale date, inclusive of both start and end days."""
    if start:
        stmt = stmt.where(Sale.created_at >= datetime.combine(start, time.min))
    if end:
        next_day = datetime.combine(end + timedelta(days=1), time.min)
        stmt = stmt.where(Sale.created_at < next_day)
    return stmt


def _pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 2) if whole else 0.0


def sales_summary(db: Session, start: date | None = None, end: date | None = None) -> dict:
    stmt = _items_with_sales().add_columns(
        _revenue(),
        _cost(),
        func.coalesce(func.sum(SaleItem.quantity), 0),
        func.count(func.distinct(Sale.id)),
    )
    revenue, cost, items, count = db.execute(_in_range(stmt, start, end)).one()
    revenue, cost, items, count = int(revenue), int(cost), int(items), int(count)
    profit = revenue - cost
    return {
        "start": start,
        "end": end,
        "revenue": revenue,
        "cost": cost,
        "profit": profit,
        "margin_pct": _pct(profit, revenue),
        "sales_count": count,
        "items_sold": items,
        "average_sale": round(revenue / count, 2) if count else 0.0,
    }


def daily_sales(db: Session, start: date | None = None, end: date | None = None) -> list[dict]:
    day = func.date(Sale.created_at)
    stmt = (
        _items_with_sales()
        .add_columns(day.label("day"), _revenue(), _cost(), func.count(func.distinct(Sale.id)))
        .group_by(day)
        .order_by(day)
    )
    rows = db.execute(_in_range(stmt, start, end)).all()
    return [
        {
            # SQLite returns 'YYYY-MM-DD' strings, Postgres returns date objects.
            "day": d if isinstance(d, date) else date.fromisoformat(str(d)),
            "revenue": int(rev),
            "cost": int(cost),
            "profit": int(rev) - int(cost),
            "sales_count": int(count),
        }
        for d, rev, cost, count in rows
    ]


def top_products(
    db: Session,
    start: date | None = None,
    end: date | None = None,
    limit: int = 5,
    by: SortKey = "revenue",
) -> list[dict]:
    stmt = (
        _items_with_sales()
        .join(Product, SaleItem.product_id == Product.id)
        .add_columns(
            Product.id,
            Product.name,
            func.sum(SaleItem.quantity).label("quantity"),
            func.sum(SaleItem.quantity * SaleItem.unit_price).label("revenue"),
            func.sum(SaleItem.quantity * (SaleItem.unit_price - SaleItem.unit_cost)).label("profit"),
        )
        .group_by(Product.id, Product.name)
        .order_by(desc(by), Product.name)
        .limit(limit)
    )
    rows = db.execute(_in_range(stmt, start, end)).all()
    return [
        {"product_id": pid, "name": name, "quantity": int(q), "revenue": int(r), "profit": int(p)}
        for pid, name, q, r, p in rows
    ]


def low_stock(db: Session) -> list[dict]:
    stmt = (
        select(Product)
        .where(Product.stock_qty <= Product.reorder_level)
        .order_by(Product.stock_qty, Product.name)
    )
    return [
        {
            "product_id": p.id,
            "name": p.name,
            "sku": p.sku,
            "stock_qty": p.stock_qty,
            "reorder_level": p.reorder_level,
            "shortfall": max(p.reorder_level - p.stock_qty, 0),
        }
        for p in db.scalars(stmt)
    ]


def payment_methods(db: Session, start: date | None = None, end: date | None = None) -> list[dict]:
    stmt = (
        _items_with_sales()
        .add_columns(
            Sale.payment_method,
            _revenue().label("revenue"),
            func.count(func.distinct(Sale.id)),
        )
        .group_by(Sale.payment_method)
        .order_by(desc("revenue"), Sale.payment_method)
    )
    rows = db.execute(_in_range(stmt, start, end)).all()
    return [
        {"payment_method": m, "revenue": int(r), "sales_count": int(c)} for m, r, c in rows
    ]
