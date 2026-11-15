"""Create the schema and load generated data into PostgreSQL."""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import psycopg

from data_generation.generate import generate
from db.models import SCHEMA_SQL

ENV_FILE = ROOT / ".env"


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def conn_params():
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5434")),
        "dbname": os.getenv("POSTGRES_DB", "billing"),
        "user": os.getenv("POSTGRES_USER", "billing"),
        "password": os.getenv("POSTGRES_PASSWORD", "billing"),
    }


TABLES = (
    "audit_log",
    "review_cases",
    "refunds",
    "payments",
    "invoices",
    "tickets",
    "orders",
    "customers",
)


def main():
    load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    for table in ("customers", "orders", "invoices", "payments", "refunds", "tickets", "review-cases"):
        parser.add_argument(f"--{table}", type=int, default=5)
    args = parser.parse_args()
    counts = {
        "customers": args.customers,
        "orders": args.orders,
        "invoices": args.invoices,
        "payments": args.payments,
        "refunds": args.refunds,
        "tickets": args.tickets,
        "review_cases": args.review_cases,
    }
    data = generate(args.seed, counts)

    with psycopg.connect(**conn_params()) as conn:
        with conn.cursor() as cur:
            for table in TABLES:
                cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            cur.execute(SCHEMA_SQL)

            for row in data["customers"]:
                cur.execute(
                    "INSERT INTO customers (customer_id, full_name, email, phone, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s)",
                    (row["customer_id"], row["full_name"], row["email"], row["phone"], row["created_at"], row["updated_at"]),
                )
            for row in data["orders"]:
                cur.execute(
                    "INSERT INTO orders (order_id, customer_id, currency, order_date, total_amount, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (row["order_id"], row["customer_id"], row["currency"], row["order_date"], row["total_amount"], row["created_at"], row["updated_at"]),
                )
            for row in data["invoices"]:
                cur.execute(
                    "INSERT INTO invoices (invoice_id, order_id, invoice_date, currency, tax_rate, tax_amount, subtotal, total_amount, line_items) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        row["invoice_id"],
                        row["order_id"],
                        row["invoice_date"],
                        row["currency"],
                        row["tax_rate"],
                        row["tax_amount"],
                        row["subtotal"],
                        row["total_amount"],
                        json.dumps(row["line_items"]),
                    ),
                )
            for row in data["payments"]:
                cur.execute(
                    "INSERT INTO payments (payment_id, invoice_id, paid_at, amount, currency, method) VALUES (%s,%s,%s,%s,%s,%s)",
                    (row["payment_id"], row["invoice_id"], row["paid_at"], row["amount"], row["currency"], row["method"]),
                )
            for row in data["refunds"]:
                cur.execute(
                    "INSERT INTO refunds (refund_id, invoice_id, amount, currency, reason, status, idempotency_key, requested_at, decided_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        row["refund_id"],
                        row["invoice_id"],
                        row["amount"],
                        row["currency"],
                        row["reason"],
                        row["status"],
                        row["idempotency_key"],
                        row["requested_at"],
                        row["decided_at"],
                    ),
                )
            for row in data["tickets"]:
                cur.execute(
                    "INSERT INTO tickets (ticket_id, customer_id, subject, body, created_at) VALUES (%s,%s,%s,%s,%s)",
                    (row["ticket_id"], row["customer_id"], row["subject"], row["body"], row["created_at"]),
                )
            for row in data["review_cases"]:
                cur.execute(
                    "INSERT INTO review_cases (case_id, ticket_id, invoice_id, summary, status, reviewer_id, decision_note, refund_id, created_at, decided_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        row["case_id"],
                        row["ticket_id"],
                        row["invoice_id"],
                        row["summary"],
                        row["status"],
                        row["reviewer_id"],
                        row["decision_note"],
                        row["refund_id"],
                        row["created_at"],
                        row["decided_at"],
                    ),
                )
            for row in data["audit_log"]:
                cur.execute(
                    "INSERT INTO audit_log (log_id, actor, action, entity_type, entity_id, trace_id, details, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        row["log_id"],
                        row["actor"],
                        row["action"],
                        row["entity_type"],
                        row["entity_id"],
                        row["trace_id"],
                        json.dumps(row["details"]),
                        row["created_at"],
                    ),
                )
        conn.commit()
    print("loaded", {k: len(v) for k, v in data.items()})


if __name__ == "__main__":
    main()
