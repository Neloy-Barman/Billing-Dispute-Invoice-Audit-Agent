"""Seeded generator for the billing dataset."""

import argparse
import json
import random
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from faker import Faker

AS_OF = date(2026, 11, 1)
NAMESPACE = uuid.UUID("9f2b6c1d-4a8e-4b7f-9c3d-1e5a7b9c2d40")
CURRENCIES = ("USD", "EUR")
PAYMENT_METHODS = ("card", "bank_transfer", "paypal")
TAX_RATES = (Decimal("0.05"), Decimal("0.08"), Decimal("0.10"), Decimal("0.20"))
PRODUCTS = (
    ("Denim Jacket", "Premium denim jacket with reinforced stitching", Decimal("349.00")),
    ("Cashmere Sweater", "Luxury cashmere knit sweater", Decimal("599.00")),
    ("Leather Belt", "Hand-stitched leather belt with gold buckle", Decimal("275.00")),
    ("Silk Scarf", "Printed silk scarf, limited edition", Decimal("195.00")),
    ("Evening Gown", "Floor-length evening gown with crystal detailing", Decimal("1299.00")),
)
COMPLAINTS = (
    (
        "Charged twice for one order",
        "I was charged twice for my denim jacket order. Please refund the duplicate charge.",
    ),
    (
        "Invoice total looks wrong",
        "The total on my invoice does not match the cashmere sweater and belt I ordered. Please check the figures.",
    ),
    (
        "Refund has not arrived",
        "I was told a refund had been issued for my silk scarf, but nothing has reached my account yet.",
    ),
    (
        "Billed after cancellation",
        "I cancelled my subscription before this invoice for the evening gown was raised, so I should not have been charged.",
    ),
    (
        "Wrong currency on my invoice",
        "My invoice for the leather belt was issued in a different currency from the one on my order.",
    ),
)


def _money(value):
    """Round a Decimal to two places, half up."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _ref(prefix, *parts):
    """Build a prefixed UUIDv5 id that stays the same for a given seed and index."""
    return f"{prefix}-{uuid.uuid5(NAMESPACE, ':'.join(str(p) for p in parts))}"


def _day(rng, start, end):
    """Pick a random date between two dates, both inclusive."""
    return start + timedelta(days=rng.randrange((end - start).days + 1))


def _stamp(day, rng):
    """Turn a date into a UTC timestamp at a random time of day."""
    return datetime.combine(day, time(rng.randrange(24), rng.randrange(60)), tzinfo=timezone.utc)


def _email(full_name, taken):
    """Derive a unique email address from a customer's full name."""
    slug = full_name.lower().replace("'", "").replace(".", "").replace(" ", ".")
    address = f"{slug}@example.com"
    suffix = 2
    while address in taken:
        address = f"{slug}{suffix}@example.com"
        suffix += 1
    taken.add(address)
    return address


def _customers(seed, count):
    """Create customers with a name, contact details and an account date."""
    fake = Faker()
    fake.seed_instance(seed)
    rng = random.Random(seed)
    taken = set()
    rows = []
    for i in range(count):
        full_name = fake.name()
        created = _stamp(_day(rng, AS_OF - timedelta(days=730), AS_OF - timedelta(days=90)), rng)
        rows.append(
            {
                "customer_id": _ref("CUST", seed, "customer", i),
                "full_name": full_name,
                "email": _email(full_name, taken),
                "phone": fake.phone_number(),
                "created_at": created.isoformat(),
                "updated_at": created.isoformat(),
            }
        )
    return rows


def _orders(seed, customer_ids, count):
    """Create orders, each with its own line items and total."""
    rng = random.Random(seed + 1)
    rows = []
    lines = {}
    for i in range(count):
        order_id = _ref("ORD", seed, "order", i)
        currency = CURRENCIES[i % len(CURRENCIES)]
        order_date = _day(rng, AS_OF - timedelta(days=365), AS_OF - timedelta(days=10))
        items = {}
        for _ in range(rng.randint(1, 3)):
            product, description, price = PRODUCTS[rng.randrange(len(PRODUCTS))]
            if product in items:
                items[product]["quantity"] += 1
            else:
                items[product] = {
                    "product_name": product,
                    "description": description,
                    "quantity": 1,
                    "unit_price": str(price),
                }
        line_items = list(items.values())
        subtotal = sum(Decimal(item["unit_price"]) * item["quantity"] for item in line_items)
        created = _stamp(order_date, rng)
        rows.append(
            {
                "order_id": order_id,
                "customer_id": customer_ids[i % len(customer_ids)],
                "currency": currency,
                "order_date": order_date.isoformat(),
                "total_amount": str(_money(subtotal)),
                "created_at": created.isoformat(),
                "updated_at": created.isoformat(),
            }
        )
        lines[order_id] = {"order_date": order_date, "currency": currency, "items": line_items}
    return rows, lines


def _invoices(seed, orders, lines, count):
    """Create one invoice per order, with tax and totals computed from its line items."""
    rng = random.Random(seed + 2)
    rows = []
    for i in range(count):
        order = orders[i % len(orders)]
        line = lines[order["order_id"]]
        invoice_date = min(line["order_date"] + timedelta(days=rng.randint(0, 3)), AS_OF)
        subtotal = sum(Decimal(item["unit_price"]) * item["quantity"] for item in line["items"])
        tax_rate = TAX_RATES[rng.randrange(len(TAX_RATES))]
        tax_amount = _money(subtotal * tax_rate)
        rows.append(
            {
                "invoice_id": _ref("INV", seed, "invoice", i),
                "order_id": order["order_id"],
                "invoice_date": invoice_date.isoformat(),
                "currency": line["currency"],
                "tax_rate": str(tax_rate),
                "tax_amount": str(tax_amount),
                "subtotal": str(_money(subtotal)),
                "total_amount": str(_money(subtotal + tax_amount)),
                "line_items": line["items"],
            }
        )
    return rows


def _payments(seed, invoices, count):
    """Create one full payment per invoice, dated shortly after it."""
    rng = random.Random(seed + 3)
    rows = []
    for i in range(count):
        invoice = invoices[i % len(invoices)]
        invoice_date = date.fromisoformat(invoice["invoice_date"])
        paid_on = min(invoice_date + timedelta(days=rng.randint(0, 10)), AS_OF)
        rows.append(
            {
                "payment_id": _ref("PAY", seed, "payment", i),
                "invoice_id": invoice["invoice_id"],
                "paid_at": _stamp(paid_on, rng).isoformat(),
                "amount": invoice["total_amount"],
                "currency": invoice["currency"],
                "method": PAYMENT_METHODS[i % len(PAYMENT_METHODS)],
            }
        )
    return rows


def _refunds(seed, payments, count):
    """Create issued refunds that follow the payments they belong to."""
    rng = random.Random(seed + 4)
    rows = []
    for i in range(count):
        payment = payments[i % len(payments)]
        requested = datetime.fromisoformat(payment["paid_at"]) + timedelta(days=rng.randint(1, 5))
        requested = min(requested, datetime.combine(AS_OF, time(12, 0), tzinfo=timezone.utc))
        decided = min(
            requested + timedelta(days=rng.randint(1, 3)),
            datetime.combine(AS_OF, time(18, 0), tzinfo=timezone.utc),
        )
        rows.append(
            {
                "refund_id": _ref("REF", seed, "refund", i),
                "invoice_id": payment["invoice_id"],
                "amount": payment["amount"],
                "currency": payment["currency"],
                "reason": "Customer reported a duplicate charge",
                "status": "issued",
                "idempotency_key": _ref("idem", seed, "refund", i),
                "requested_at": requested.isoformat(),
                "decided_at": decided.isoformat(),
            }
        )
    return rows


def _tickets(seed, customer_ids, count):
    """Create support tickets, one complaint per customer in rotation."""
    rng = random.Random(seed + 5)
    rows = []
    for i in range(count):
        subject, body = COMPLAINTS[i % len(COMPLAINTS)]
        created = _stamp(_day(rng, AS_OF - timedelta(days=120), AS_OF), rng)
        rows.append(
            {
                "ticket_id": _ref("TKT", seed, "ticket", i),
                "customer_id": customer_ids[i % len(customer_ids)],
                "subject": subject,
                "body": body,
                "created_at": created.isoformat(),
            }
        )
    return rows


def _review_cases(seed, tickets, invoices, count):
    """Create pending review cases linking a ticket to the invoice it disputes."""
    rng = random.Random(seed + 6)
    rows = []
    for i in range(count):
        ticket = tickets[i % len(tickets)]
        invoice = invoices[i % len(invoices)]
        created = datetime.fromisoformat(ticket["created_at"]) + timedelta(hours=rng.randint(1, 24))
        rows.append(
            {
                "case_id": _ref("CASE", seed, "case", i),
                "ticket_id": ticket["ticket_id"],
                "invoice_id": invoice["invoice_id"],
                "summary": f"Customer disputes invoice {invoice['invoice_id'][-12:]}",
                "status": "pending",
                "reviewer_id": None,
                "decision_note": None,
                "refund_id": None,
                "created_at": created.isoformat(),
                "decided_at": None,
            }
        )
    return rows


def _audit_log(seed, refunds):
    """Create one refund.issued log entry per refund."""
    rows = []
    for i, refund in enumerate(refunds):
        rows.append(
            {
                "log_id": _ref("LOG", seed, "log", i),
                "actor": "agent",
                "action": "refund.issued",
                "entity_type": "refund",
                "entity_id": refund["refund_id"],
                "trace_id": None,
                "details": {
                    "invoice_id": refund["invoice_id"],
                    "amount": refund["amount"],
                    "currency": refund["currency"],
                },
                "created_at": refund["decided_at"],
            }
        )
    return rows


def generate(seed, counts):
    """Build every table for one seed and a per-table row count."""
    customers = _customers(seed, counts["customers"])
    customer_ids = [row["customer_id"] for row in customers]
    orders, lines = _orders(seed, customer_ids, counts["orders"])
    invoices = _invoices(seed, orders, lines, counts["invoices"])
    payments = _payments(seed, invoices, counts["payments"])
    refunds = _refunds(seed, payments, counts["refunds"])
    tickets = _tickets(seed, customer_ids, counts["tickets"])
    cases = _review_cases(seed, tickets, invoices, counts["review_cases"])
    logs = _audit_log(seed, refunds)
    return {
        "customers": customers,
        "orders": orders,
        "invoices": invoices,
        "payments": payments,
        "refunds": refunds,
        "tickets": tickets,
        "review_cases": cases,
        "audit_log": logs,
    }


def main():
    """Parse the CLI flags and print each table as JSON lines."""
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
    for table, rows in generate(args.seed, counts).items():
        print(f"--- {table} ({len(rows)}) ---")
        for row in rows:
            print(json.dumps(row, default=str))


if __name__ == "__main__":
    main()
