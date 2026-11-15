# Code Map

Short per-file overview for agent handoff. Read this before opening files.

## Source code

- `db/models.py` — PostgreSQL DDL as one `SCHEMA_SQL` string: 8 tables (customers, orders, invoices, payments, refunds, tickets, review_cases, audit_log), FKs with ON DELETE CASCADE, constraints.
- `db/seed.py` — Drops/recreates schema and loads generated rows into Postgres from `.env` connection settings. CLI: `--seed`, per-table counts.
- `data_generation/generate.py` — Seeded generator; builds all 8 tables from a seed and per-table counts; prints JSON lines. Prefixed UUIDv5 ids, two currencies (USD/EUR).

## Config / infra

- `requirements.txt` — psycopg[binary], faker, pytest (pinned).
- `docker-compose.yml` — PostgreSQL service for local DB.
- `.env.example` — Variable names only (no real keys).
- `.gitignore` — Standard ignores.

## Docs

- `docs/PLAN.md` — Phased build plan + checklists (source of progress).
- `docs/folder-structure.md` — Target repo layout and module responsibilities.
- `docs/schema/schema.md` — ERD + per-table/column documentation.
- `docs/run-and-test.md` — Living guide: run and test steps per component (DB now; tools/agent/etc. as built).
- `docs/developer-instructions.md` — Working rules for coding agents.
- `docs/AI Engineer Project ...pdf` — Original assignment spec (Tasks 1–9).

## Top-level

- `README.md` — Project blurb; points to PLAN.md.
- `AGENTS.md`, `WORKING-STYLE.md` — Agent working rules (copies).
- `x.md` — Scratch notes.

## Not yet created

All other folders/modules from folder-structure.md (src/billing_agent/, apps/, tests/, scripts/, configs/, etc.) do not exist yet.