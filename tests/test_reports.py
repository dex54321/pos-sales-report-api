"""API tests using an in-memory SQLite database with known data.

Expected figures are worked out by hand from the fixture below.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db, normalize_url
from app.main import app
from app.models import Product, Sale, SaleItem


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    with TestSession() as db:
        cement = Product(name="Cement 50kg", sku="CEM", category="Building",
                         buying_price=700, selling_price=850, stock_qty=3, reorder_level=10)
        nails = Product(name="Nails 1kg", sku="NAI", category="Hardware",
                        buying_price=150, selling_price=200, stock_qty=40, reorder_level=10)
        paint = Product(name="Paint 4L", sku="PNT", category="Paint",
                        buying_price=1800, selling_price=2200, stock_qty=10, reorder_level=10)
        db.add_all([cement, nails, paint])
        db.flush()

        def item(p, qty):
            return SaleItem(product_id=p.id, quantity=qty,
                            unit_price=p.selling_price, unit_cost=p.buying_price)

        db.add_all([
            Sale(created_at=datetime(2026, 10, 1, 10), payment_method="mpesa",
                 items=[item(cement, 2), item(nails, 3)]),
            Sale(created_at=datetime(2026, 10, 1, 15), payment_method="cash",
                 items=[item(paint, 1)]),
            Sale(created_at=datetime(2026, 10, 2, 9), payment_method="mpesa",
                 items=[item(nails, 4)]),
        ])
        db.commit()

    def override_get_db():
        with TestSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_summary_all_time(client):
    data = client.get("/reports/summary").json()
    assert data["revenue"] == 5300
    assert data["cost"] == 4250
    assert data["profit"] == 1050
    assert data["margin_pct"] == 19.81
    assert data["sales_count"] == 3
    assert data["items_sold"] == 10
    assert data["average_sale"] == 1766.67


def test_summary_single_day_is_inclusive(client):
    data = client.get("/reports/summary", params={"start": "2026-10-02", "end": "2026-10-02"}).json()
    assert data["revenue"] == 800
    assert data["sales_count"] == 1


def test_summary_empty_range_returns_zeros(client):
    data = client.get("/reports/summary", params={"start": "2027-01-01"}).json()
    assert data["revenue"] == 0
    assert data["margin_pct"] == 0.0
    assert data["average_sale"] == 0.0


def test_invalid_range_rejected(client):
    r = client.get("/reports/summary", params={"start": "2026-10-05", "end": "2026-10-01"})
    assert r.status_code == 422


def test_daily(client):
    assert client.get("/reports/daily").json() == [
        {"day": "2026-10-01", "revenue": 4500, "cost": 3650, "profit": 850, "sales_count": 2},
        {"day": "2026-10-02", "revenue": 800, "cost": 600, "profit": 200, "sales_count": 1},
    ]


@pytest.mark.parametrize(
    "by, expected",
    [
        ("revenue", ["Paint 4L", "Cement 50kg", "Nails 1kg"]),
        ("quantity", ["Nails 1kg", "Cement 50kg", "Paint 4L"]),
        ("profit", ["Paint 4L", "Nails 1kg", "Cement 50kg"]),
    ],
)
def test_top_products_sorting(client, by, expected):
    rows = client.get("/reports/top-products", params={"by": by}).json()
    assert [r["name"] for r in rows] == expected


def test_top_products_limit_and_bad_sort(client):
    assert len(client.get("/reports/top-products", params={"limit": 1}).json()) == 1
    assert client.get("/reports/top-products", params={"by": "colour"}).status_code == 422


def test_low_stock(client):
    rows = client.get("/reports/low-stock").json()
    assert [(r["name"], r["shortfall"]) for r in rows] == [("Cement 50kg", 7), ("Paint 4L", 0)]


def test_payment_methods(client):
    assert client.get("/reports/payment-methods").json() == [
        {"payment_method": "mpesa", "revenue": 3100, "sales_count": 2},
        {"payment_method": "cash", "revenue": 2200, "sales_count": 1},
    ]


def test_normalize_url_for_neon():
    assert normalize_url("postgresql://u:p@host/db") == "postgresql+psycopg://u:p@host/db"
    assert normalize_url("postgres://u:p@host/db") == "postgresql+psycopg://u:p@host/db"
    assert normalize_url("sqlite:///./pos.db") == "sqlite:///./pos.db"
