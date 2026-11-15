"""PostgreSQL table definitions."""

SCHEMA_SQL = """
CREATE TABLE customers (
    customer_id     TEXT PRIMARY KEY,
    full_name       TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    phone           TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    order_id        TEXT PRIMARY KEY,
    customer_id     TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    currency        CHAR(3) NOT NULL CHECK (currency IN ('USD','EUR')),
    order_date      DATE NOT NULL,
    total_amount    NUMERIC(12,2) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE invoices (
    invoice_id      TEXT PRIMARY KEY,
    order_id        TEXT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    invoice_date    DATE NOT NULL,
    currency        CHAR(3) NOT NULL,
    tax_rate        NUMERIC(5,4) NOT NULL,
    tax_amount      NUMERIC(12,2) NOT NULL,
    subtotal        NUMERIC(12,2) NOT NULL,
    total_amount    NUMERIC(12,2) NOT NULL,
    line_items      JSONB NOT NULL
);

CREATE TABLE payments (
    payment_id      TEXT PRIMARY KEY,
    invoice_id      TEXT NOT NULL REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    paid_at         TIMESTAMPTZ NOT NULL,
    amount          NUMERIC(12,2) NOT NULL,
    currency        CHAR(3) NOT NULL,
    method          TEXT NOT NULL
);

CREATE TABLE refunds (
    refund_id       TEXT PRIMARY KEY,
    invoice_id      TEXT NOT NULL REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    amount          NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    currency        CHAR(3) NOT NULL,
    reason          TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('pending','approved','rejected','issued')),
    idempotency_key TEXT NOT NULL UNIQUE,
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at      TIMESTAMPTZ
);

CREATE TABLE tickets (
    ticket_id       TEXT PRIMARY KEY,
    customer_id     TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    subject         TEXT,
    body            TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE review_cases (
    case_id         TEXT PRIMARY KEY,
    ticket_id       TEXT NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    invoice_id      TEXT REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    summary         TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('pending','approved','rejected')),
    reviewer_id     TEXT,
    decision_note   TEXT,
    refund_id       TEXT REFERENCES refunds(refund_id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at      TIMESTAMPTZ
);

CREATE TABLE audit_log (
    log_id          TEXT PRIMARY KEY,
    actor           TEXT NOT NULL,
    action          TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    entity_id       TEXT NOT NULL,
    trace_id        TEXT,
    details         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""
