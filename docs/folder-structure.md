# Folder Structure

Layout of the `billing-audit-agent` repository: where each file belongs and what each directory holds.

## Tree

```text
billing-audit-agent/
├── README.md                     # setup in 5 commands, architecture, results summary
├── pyproject.toml                # deps, tool config (ruff, pytest, mypy); pin crewai here
├── .env.example                  # variable names only, never real keys
├── .gitignore
├── Makefile                      # make setup | data | test | eval | gate | run-customer | run-review
├── Dockerfile
├── docker-compose.yml            # app + Phoenix + database
│
├── .github/workflows/            # ci.yml (lint + tests), regression-gate.yml (smoke eval)
│
├── configs/                      # YAML only, no code
│   ├── agent.yaml                # model, temperature, step budget, timeouts
│   ├── thresholds.yaml           # refund limit, escalation confidence, alert limits
│   ├── eval.yaml                 # which evaluators, dataset version, judge model
│   └── experiments/              # one YAML per experiment (exp_01_baseline.yaml, ...)
│
├── data/                         # generated files stay out of git (.gitkeep placeholders)
│   ├── policy/                   # refund_policy.md
│   ├── generated/                # invoices, customers, orders (CSV/JSON/SQLite)
│   ├── tickets/                  # tickets_dev.jsonl, tickets_test.jsonl, adversarial.jsonl
│   ├── labels/                   # ground truth, human judge labels
│   └── invoices_raw/             # optional PDFs/images for extraction
│
├── docs/
│   ├── architecture/             # diagram sources + exports (.mmd, .svg, .png)
│   ├── schema/                   # ERD + schema.md
│   ├── decisions/                # one ADR per choice (0001-use-crewai.md, ...)
│   ├── labeling_guide.md
│   ├── ai_disclosure.md
│   ├── prompts/                  # copies of final agent and judge prompts
│   └── reports/                  # evaluation_report.md, decision_memo.md, screenshots/
│
├── src/billing_agent/
│   ├── config/                   # settings.py (loads .env and YAML)
│   ├── db/                       # models, session, migrations, repositories, seed
│   ├── data_generation/          # invoices, defects, tickets, splits (all seeded)
│   ├── tools/
│   │   ├── core/                 # pure Python: invoice_lookup, math_validator,
│   │   │                         #   duplicate_detector, payment_history,
│   │   │                         #   policy_retrieval, refund, escalation
│   │   ├── schemas.py            # Pydantic inputs/outputs
│   │   └── crewai_tools.py       # thin wrappers around core/
│   ├── agent/                    # crew.py, prompts/, output_schema.py, guardrails.py, runner.py
│   ├── security/                 # authz, redaction, audit_log, rate_limit
│   ├── observability/            # phoenix_setup.py, trace_export.py
│   ├── evaluation/               # evaluators/, judges/, datasets, experiments, faults,
│   │                             #   stats, report
│   ├── monitoring/               # replay, online_checks, business_metrics, alerts
│   └── review/                   # queue.py (pending, approved, rejected)
│
├── apps/                         # thin UIs, no business logic
│   ├── customer_chat/            # Streamlit or Gradio
│   └── review_queue/             # internal reviewer page
│
├── scripts/                      # generate_data, run_eval, run_experiment,
│                                 #   regression_gate, traces_to_dataset
├── tests/                        # unit, integration, failure, security + fixtures
├── notebooks/                    # exploration only
└── results/                      # one folder per run id: metrics.json, config snapshot
```

## What lives where

| Path | Holds |
| --- | --- |
| `configs/` | Every tunable: model settings, thresholds, evaluator selection, experiment variants. |
| `data/` | Policy text (committed) and generated datasets, tickets, labels, PDFs (gitignored). |
| `src/billing_agent/` | All application code. |
| `apps/` | UI shells that call into the agent and the review queue. |
| `scripts/` | CLI entry points behind the `Makefile` targets. |
| `tests/` | Unit, integration, failure, and security coverage. |
| `results/` | Per-run metrics and config snapshots (gitignored). |
| `docs/` | Architecture diagrams, schema, ADRs, labeling guide, prompt copies, reports. |

## Source package

| Module | Responsible for |
| --- | --- |
| `config/` | Loading and validating `.env` + YAML settings. |
| `db/` | Schema, sessions, migrations, queries, seeding. |
| `data_generation/` | Seed-reproducible datasets and defect injection with hidden labels. |
| `tools/core/` | Business rules: lookups, math validation, duplicates, payments, policy retrieval, refunds, escalation. |
| `tools/crewai_tools.py` | Exposes `core/` functions to the agent. No logic of its own. |
| `agent/` | The single agent, its prompts, output schema, guardrails, and `run_ticket()`. |
| `security/` | Authorization, redaction, audit logging, rate limits. |
| `observability/` | Phoenix tracing setup and trace export. |
| `evaluation/` | Evaluators, LLM judges, datasets, experiments, fault injection, stats, reports. |
| `monitoring/` | Replay, online checks, business metrics, alerts. |
| `review/` | Human review queue state machine. |

## Rules

- `tools/core/` is plain Python — no LLM, no CrewAI, no network, fully unit-testable.
- Only `agent/` talks to a model; it never re-implements a business rule.
- Every threshold or model setting lives in `configs/*.yaml`, not in code.
- Prompts are versioned files (`system_prompt_v1.md`, `v2.md`); a change means a new file.
- `tools/refund.py` is the only side-effecting tool — limits and idempotency are enforced there.
- Generated data and results stay out of git; anything worth keeping is copied into `docs/reports/`.
- A new file that fits no row above needs a directory decision first, not an improvised folder.
