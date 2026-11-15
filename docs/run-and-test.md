# Run and Test Guide

Living guide for running and testing each part of the project as it is built.
Add a section here whenever a new component is implemented.

## Database

### Prerequisites

- Docker Desktop running.
- `.env` present with `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (see `.env.example`).
- Python venv with `psycopg[binary]` and `faker` installed.

### Start the database

```powershell
docker compose up -d
```

Postgres is on `localhost:5434`. Adminer UI is on `http://localhost:8081`.

### Load the schema and seed data

```powershell
.\.venv\Scripts\python.exe db\seed.py
```

Defaults: seed `42`, 5 rows per table. Override counts:

```powershell
.\.venv\Scripts\python.exe db\seed.py --seed 42 --invoices 300 --customers 100
```

`seed.py` drops existing tables, recreates the schema from `db/models.py`, then inserts generated rows. It is destructive: re-running replaces all data.

### View the data

Open Adminer at `http://localhost:8081`, log in with the `.env` credentials, server `postgres`. Tables appear under the database name.

### Add or change data

1. Edit `data_generation/generate.py` (products, complaints, counts, defects later).
2. Re-run `db\seed.py` to rebuild everything.
3. To add rows to a single table manually, use Adminer or a SQL client against `localhost:5434`; note foreign-key constraints and `ON DELETE CASCADE`.

### Stop the database

```powershell
docker compose down
```

Add `-v` to also remove the persisted volume.

## Tools

_To be added in Phase 2._

## Agent

_To be added in Phase 3._

## Frontend demo

_To be added in Phase 4._

## Evaluation

_To be added in Phase 5._

## Monitoring and hardening

_To be added in Phase 6._