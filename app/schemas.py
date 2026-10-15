"""Response models for the report endpoints."""

from datetime import date

from pydantic import BaseModel


class Summary(BaseModel):
    start: date | None
    end: date | None
    revenue: int
    cost: int
    profit: int
    margin_pct: float
    sales_count: int
    items_sold: int
    average_sale: float


class DailyRow(BaseModel):
    day: date
    revenue: int
    cost: int
    profit: int
    sales_count: int


class ProductPerformance(BaseModel):
    product_id: int
    name: str
    quantity: int
    revenue: int
    profit: int


class LowStockItem(BaseModel):
    product_id: int
    name: str
    sku: str
    stock_qty: int
    reorder_level: int
    shortfall: int


class PaymentMethodRow(BaseModel):
    payment_method: str
    revenue: int
    sales_count: int
