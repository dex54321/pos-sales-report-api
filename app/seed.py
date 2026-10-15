"""Fill the database with realistic demo data for a hardware shop.

Run with:  python -m app.seed
"""

import random
from datetime import datetime, timedelta

from .database import Base, SessionLocal, engine
from .models import Product, Sale, SaleItem

PRODUCTS = [
    # name, sku, category, buying, selling, stock, reorder
    ("Cement 50kg", "CEM-50", "Building", 720, 850, 40, 20),
    ("Iron Sheet Gauge 30 (3m)", "IRS-30", "Roofing", 780, 950, 12, 15),
    ("PVC Pipe 1/2 inch (6m)", "PVC-12", "Plumbing", 260, 350, 55, 20),
    ("Wire Nails 3 inch (1kg)", "NAI-3", "Hardware", 150, 200, 8, 10),
    ("Emulsion Paint White 4L", "PNT-W4", "Paint", 1800, 2250, 18, 6),
    ("Twin Cable 1.5mm (100m)", "CBL-15", "Electrical", 3900, 4600, 5, 5),
    ("Padlock Medium", "PDL-M", "Hardware", 300, 450, 30, 10),
    ("Gate Valve 1/2 inch", "GTV-12", "Plumbing", 420, 600, 3, 8),
]


def seed(days: int = 30, seed_value: int = 42) -> None:
    rng = random.Random(seed_value)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        products = [
            Product(name=n, sku=s, category=c, buying_price=b, selling_price=p,
                    stock_qty=q, reorder_level=r)
            for n, s, c, b, p, q, r in PRODUCTS
        ]
        db.add_all(products)
        db.flush()

        start = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0) - timedelta(days=days)
        for day in range(days):
            for _ in range(rng.randint(4, 12)):
                sale = Sale(
                    created_at=start + timedelta(days=day, minutes=rng.randint(0, 600)),
                    payment_method=rng.choice(["mpesa", "mpesa", "cash"]),
                )
                for product in rng.sample(products, rng.randint(1, 3)):
                    sale.items.append(SaleItem(
                        product_id=product.id,
                        quantity=rng.randint(1, 5),
                        unit_price=product.selling_price,
                        unit_cost=product.buying_price,
                    ))
                db.add(sale)
        db.commit()
    print(f"Seeded {len(PRODUCTS)} products and {days} days of sales.")


if __name__ == "__main__":
    seed()
