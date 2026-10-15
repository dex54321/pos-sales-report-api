"""FastAPI app exposing sales reports for the Albright POS."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from . import reports
from .database import Base, engine, get_db
from .schemas import DailyRow, LowStockItem, PaymentMethodRow, ProductPerformance, Summary


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Albright POS Sales Report API",
    description="Sales, profit and stock reports for a hardware shop POS. Amounts are in KES.",
    version="1.0.0",
    lifespan=lifespan,
)


def date_range(
    start: date | None = Query(None, description="First day to include (YYYY-MM-DD)"),
    end: date | None = Query(None, description="Last day to include (YYYY-MM-DD)"),
) -> tuple[date | None, date | None]:
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="start must be on or before end")
    return start, end


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/reports/summary", response_model=Summary)
def summary(rng=Depends(date_range), db: Session = Depends(get_db)):
    return reports.sales_summary(db, *rng)


@app.get("/reports/daily", response_model=list[DailyRow])
def daily(rng=Depends(date_range), db: Session = Depends(get_db)):
    return reports.daily_sales(db, *rng)


@app.get("/reports/top-products", response_model=list[ProductPerformance])
def top_products(
    rng=Depends(date_range),
    limit: int = Query(5, ge=1, le=50),
    by: reports.SortKey = Query("revenue"),
    db: Session = Depends(get_db),
):
    return reports.top_products(db, *rng, limit=limit, by=by)


@app.get("/reports/low-stock", response_model=list[LowStockItem])
def low_stock(db: Session = Depends(get_db)):
    return reports.low_stock(db)


@app.get("/reports/payment-methods", response_model=list[PaymentMethodRow])
def payment_methods(rng=Depends(date_range), db: Session = Depends(get_db)):
    return reports.payment_methods(db, *rng)
