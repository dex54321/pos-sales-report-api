# POS Sales Report API

A FastAPI service that turns point-of-sale data into business reports: revenue, profit, daily trends, best-selling products, low-stock alerts and M-Pesa vs cash breakdown.

Built as the reporting layer for **Albright POS**, the point-of-sale system I built and run in my hardware shop in Kenya ([Albright-Pos](https://github.com/dex54321/Albright-Pos)). All amounts are in KES.

![tests](https://github.com/dex54321/pos-sales-report-api/actions/workflows/tests.yml/badge.svg)

## Features

- **Profit-accurate:** each sale line stores its price and cost at time of sale, so profit stays correct when prices change.
- **Database-side aggregation:** all totals, grouping and ranking run in SQL, not Python loops.
- **Works on SQLite and PostgreSQL** (including Neon). Neon-style `postgresql://` URLs are converted to the psycopg driver automatically.
- **Validated inputs:** date ranges are checked, sort keys and limits are typed and bounded.
- **Tested:** pytest suite against an in-memory database with hand-calculated expected figures.
- **Dockerised** with a Postgres `docker-compose` setup and GitHub Actions CI.

## Endpoints

All report endpoints accept optional `start` and `end` dates (`YYYY-MM-DD`, both inclusive).

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | Service status |
| GET | `/reports/summary` | Revenue, cost, profit, margin %, sales count, items sold, average sale |
| GET | `/reports/daily` | Revenue, cost, profit and sales count per day |
| GET | `/reports/top-products?by=revenue\|profit\|quantity&limit=5` | Best-performing products |
| GET | `/reports/low-stock` | Products at or below their reorder level, with shortfall |
| GET | `/reports/payment-methods` | Revenue and sales count by payment method (M-Pesa, cash) |

Interactive docs are at `/docs` once the server is running.

Example response from `/reports/summary`:

```json
{
  "start": null, "end": null,
  "revenue": 2077250, "cost": 1696380, "profit": 380870,
  "margin_pct": 18.34, "sales_count": 247, "items_sold": 1529,
  "average_sale": 8409.92
}
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m app.seed                 # 30 days of demo hardware-shop sales
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs

## Run with Docker

```bash
docker compose up --build
docker compose exec api python -m app.seed
```

To point it at an existing database instead, set `DATABASE_URL`:

```bash
docker build -t pos-sales-report-api .
docker run -p 8000:8000 -e DATABASE_URL="postgresql://user:pass@host/db" pos-sales-report-api
```

## Tests

```bash
pytest -q
```

## Project structure

```
app/
  main.py      FastAPI routes and input validation
  reports.py   Report queries (pure functions over a DB session)
  models.py    SQLAlchemy models: Product, Sale, SaleItem
  schemas.py   Pydantic response models
  database.py  Engine, sessions, URL handling
  seed.py      Demo data generator
tests/
  test_reports.py
```

## Roadmap

- API key authentication
- CSV / Excel export of reports
- Weekly and monthly grouping
- Read directly from the live Albright POS (Prisma) schema
