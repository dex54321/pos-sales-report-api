"""ORM models for products, sales and sale line items.

Prices are stored as whole Kenyan shillings (KES). Each sale item keeps the
unit price and unit cost at the time of sale, so profit stays correct even if
product prices change later.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    sku: Mapped[str] = mapped_column(String(40), unique=True)
    category: Mapped[str] = mapped_column(String(60))
    buying_price: Mapped[int]
    selling_price: Mapped[int]
    stock_qty: Mapped[int] = mapped_column(default=0)
    reorder_level: Mapped[int] = mapped_column(default=5)


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    payment_method: Mapped[str] = mapped_column(String(20))  # "cash" | "mpesa"

    items: Mapped[list["SaleItem"]] = relationship(
        back_populates="sale", cascade="all, delete-orphan"
    )


class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int]
    unit_price: Mapped[int]
    unit_cost: Mapped[int]

    sale: Mapped[Sale] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()
