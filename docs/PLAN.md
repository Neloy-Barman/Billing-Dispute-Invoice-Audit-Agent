# Project Plan and Checklist: Billing Dispute & Invoice Audit Agent

## How to use this plan

This plan splits the project into the order you described: build the database, check it, build the tools and the agent on top of it, check them, build the frontend so the demo works, and only then build the evaluators. Each phase has a checklist and an exit check. The exit check is the one thing that must be true before you move on.

Working rules:

- Every step has a number made of its phase and its position, for example 2.4. Use these numbers when you ask for work, such as "implement steps 1.4 to 1.8". Each subsection heading shows the range of steps it covers.
- Set up only what the current phase needs. Create folders, install dependencies, and add tools such as Phoenix, a Makefile, CI, or Docker the first time something actually requires them. Record each dependency as you install it, and pin its version.
- Finish one phase at a time. Do not start the next until the exit check passes.
- Commit and tag the repository at every exit check (v0.1-database, v0.2-tools, and so on), so you can always return to a working state.
- Keep a short build log of what broke and what fixed it. You will need it for the debugging case study and the evaluation report.
- Change this plan whenever your approach changes, before changing the code.
- Details for each item are in the project doc. This plan only orders the work.

## Phase overview

| Phase | What you build | Project doc tasks | Rough effort |
| --- | --- | --- | --- |
| 1. Database | The repository, schema, synthetic data with seeded defects, refund policy, verification report | Task 1 | 1.5 days |
| 2. Tools | Every tool, tested without an LLM | Task 2 | 1 day |
| 3. Agent | The CrewAI agent, guardrails, tracing, manual smoke testing | Tasks 3 and 4 | 1.5 days |
| 4. Frontend demo | Customer chat app and review queue, working end to end | Task 8 (apps) | 1 day |
| 5. Evaluation | Labeled datasets, evaluators, judge, experiments, regression gate | Tasks 1 (labels), 5, 6, 7 | 2 days |
| 6. Delivery | Monitoring replay, security pass, documentation, walkthrough video | Tasks 8 (monitoring) and 9 | 1 day |

The total is about eight days of focused work. Treat the effort column as a guide, not a deadline.

## Phase 1: Database

Goal: a database designed around what your tools need, filled with realistic data whose defects you know in advance, and checked before anything is built on it.

### Start small (steps 1.1 to 1.3)

- [x] **1.1** Create the repository with a short README and a .gitignore
- [x] **1.2** Create only the folders this phase uses: db/, data\_generation/, data/, docs/schema/, and tests/
- [x] **1.3** Create a virtual environment and install only what the database work needs: a database library, a data-generation helper, and pytest

### Design the schema (steps 1.4 to 1.8)

- [x] **1.4** For each planned tool, write down what it reads and writes, and derive the tables from that list
- [x] **1.5** Draw the entity-relationship diagram: customers, orders, invoices, invoice line items, payments, refunds, tickets, review cases, audit log
- [ ] **1.6** Decide keys, constraints, and indexes, keeping in mind that seeded defects such as duplicate invoices must still be storable
  - [x] **1.6a** Decide primary keys: prefixed text UUIDs on all eight tables
  - [x] **1.6b** Decide foreign keys between customers, orders, invoices, payments, refunds, tickets and review cases
  - [x] **1.6c** Decide NOT NULL, UNIQUE and CHECK constraints on the eight designed tables
  - [ ] **1.6d** Decide indexes on foreign keys and on `refunds.status`
  - [x] **1.6e** Decide foreign-key delete behaviour: `ON DELETE CASCADE` on every foreign key, so deletes never conflict
  - [ ] **1.6f** Decide the duplicate-invoice match rule (missing-field defect dropped for now)
  - [ ] **1.6g** Design the remaining tables: `defect_labels`, and `invoice_extractions` if extraction is built
  - [ ] **1.6h** Resolve deferred column decisions: invoice `status`, timestamps on `invoices` and `payments`, `tickets.status`, `audit_log` id type, `review_cases.refund_id`
- [x] **1.7** Write the table definitions in db/models.py, plus migrations if you use them
  - [x] **1.7a** Write the eight table definitions in `db/models.py` as one `SCHEMA_SQL` string
  - [x] **1.7b** Decide migrations: not used, the schema is applied as a single string
  - [x] **1.7c** Validate the DDL against PostgreSQL: run it in a transaction and roll back
- [x] **1.8** Write a schema.md explaining each table and column

### Generate the data (steps 1.9 to 1.12)

- [ ] **1.9** Write the seeded generator for customers, orders, invoices with line items, and payments (at least 300 invoices, two currencies)
  - [x] **1.9a** Write `data_generation/generate.py`: seeded, prefixed UUIDv5 ids, five rows per table by default
  - [ ] **1.9b** Scale the run to at least 300 invoices in two currencies
- [ ] **1.10** Write the defect injector with hidden ground-truth labels: subtotal mismatch, wrong tax rate, wrong line total, duplicate invoice, double charge, missing field, currency mismatch, refund already issued, outside the refund window
- [ ] **1.11** Write the refund policy with concrete numeric rules
- [ ] **1.12** Write a single command that creates the database and loads the data
  - [x] **1.12a** Provide PostgreSQL via `docker-compose.yml` (written; start, connect and stop all verified)
  - [ ] **1.12b** Create the schema and load the generated data in one command

### Verify the database (steps 1.13 to 1.18)

- [ ] **1.13** Check that row counts per table match what the generator was asked to create
- [ ] **1.14** Check that there are no orphan rows: every line item, payment, and refund points to a real invoice
- [ ] **1.15** Check that about a third of invoices carry a defect, with a count for each defect type
- [ ] **1.16** Run the generator twice with the same seed and confirm the data is identical
- [ ] **1.17** Hand-check ten invoices against their labels
- [ ] **1.18** Write tests for the repository functions that tools will use

**Exit check:** one command rebuilds the database from scratch, a verification script prints a clean report, and the ERD and schema.md are committed. Tag the commit v0.1-database.

## Phase 2: Tools

Goal: every tool works on its own, with no LLM involved, against the database from Phase 1. Most tools depend on the database, so this phase only starts once the database passes its exit check.

**New in this phase:** Pydantic, for typed tool inputs and outputs. Add a fuzzy-matching library only if duplicate detection needs it, and a PDF or OCR library only if you build the optional extraction tool.

### Foundations (step 2.1)

- [ ] **2.1** Define the shared result schema (status, data, error) in tools/schemas.py

### Read and audit tools (steps 2.2 to 2.6)

- [ ] **2.2** get\_invoice and search\_invoices, with a check that a customer can only read their own records
- [ ] **2.3** validate\_invoice\_math, with a rounding tolerance and a currency check
- [ ] **2.4** detect\_duplicates, with exact and fuzzy matching
- [ ] **2.5** check\_payment\_history, returning double charges and prior refunds as evidence rows
- [ ] **2.6** retrieve\_policy, returning policy passages with section ids

### Action tools (steps 2.7 to 2.8)

- [ ] **2.7** issue\_refund, with an idempotency key, the approval limit enforced in code, and an audit log entry
- [ ] **2.8** escalate\_to\_human, creating a review case with a summary

### Optional tool (step 2.9)

- [ ] **2.9** extract\_invoice for PDFs or images, returning null for uncertain fields

### Verify the tools (steps 2.10 to 2.12)

- [ ] **2.10** Write unit tests for every tool, including rounding, negative amounts, mixed currencies, and authorization failures
- [ ] **2.11** Write a plain script that calls each tool by hand and prints the result
- [ ] **2.12** Take a first measurement: run the math validator and duplicate detector over all invoices and compare with the hidden defect labels

**Exit check:** every tool passes its tests, the script demonstrates each one, and the validators catch the seeded defects. Tag the commit v0.2-tools.

## Phase 3: Agent

Goal: one CrewAI agent that uses the tools to handle a ticket, visible in Phoenix, and tested by hand before any evaluator exists.

### Set up what the agent needs (steps 3.1 to 3.3)

- [ ] **3.1** Choose the LLM provider, add the key to .env, and make one successful test call
- [ ] **3.2** Install CrewAI and pin its version
- [ ] **3.3** Start Phoenix locally and confirm the dashboard opens

### Build the agent (steps 3.4 to 3.9)

- [ ] **3.4** Wrap the tools as CrewAI tools, keeping the wrappers thin
- [ ] **3.5** Define the Pydantic output model: intent, confidence, decision, cited policy section, evidence ids
- [ ] **3.6** Write system prompt v1 as a versioned file: role, tool-use rules, escalation rules
- [ ] **3.7** Create one Agent and one Task, run in a crew of one, with a step limit and a timeout
- [ ] **3.8** Add guardrails: loop detection, out-of-scope refusal, treating customer and invoice text as untrusted, and no refund without audit evidence
- [ ] **3.9** Write run\_ticket, which returns the decision and a trace id

### Trace it (steps 3.10 to 3.12)

- [ ] **3.10** Connect Phoenix tracing for CrewAI and LiteLLM
- [ ] **3.11** Run one ticket and confirm the trace shows every LLM call and every tool call with arguments and results
- [ ] **3.12** Redact personal data before it reaches traces and logs

### Test it by hand (steps 3.13 to 3.17)

- [ ] **3.13** Write about 20 smoke tickets: a clear duplicate, a wrong tax, a double charge, a refund status question, out of scope, vague, a prompt injection, an over-limit refund, and a request about another customer's invoice
- [ ] **3.14** Run each one and read its trace; fix the prompt or tools where the agent goes wrong
- [ ] **3.15** Write integration tests with a mocked LLM for the deterministic parts: escalation triggers and the step limit
- [ ] **3.16** Write failure tests: tool timeout, malformed tool output, and an agent that loops
- [ ] **3.17** Keep notes on one real failure, its root cause, and its fix, for the debugging case study

**Exit check:** all smoke tickets end in a sensible decision or escalation, nothing crashes, no other customer's data is ever returned, and the refund limit is never exceeded. Tag the commit v0.3-agent.

## Phase 4: Frontend demo

Goal: a working demo that shows the agent running, before you spend time on evaluation. Traces and evaluation results stay in Phoenix, so you only build the two surfaces below.

### Customer chat app (steps 4.1 to 4.6)

- [ ] **4.1** Choose Streamlit or Gradio, install it, and use it for both apps
- [ ] **4.2** Build the chat page with a few sample tickets to click
- [ ] **4.3** Pick a customer from a mock login, so the agent's authorization checks are exercised
- [ ] **4.4** Show progress while the agent works without freezing the page
- [ ] **4.5** Show the final answer and the refund status (issued or pending approval), and hide all internals
- [ ] **4.6** Show a friendly message when the agent fails or escalates

### Review queue, internal (steps 4.7 to 4.10)

- [ ] **4.7** Keep it a separate page from the customer app
- [ ] **4.8** List escalated cases with the agent's summary and the evidence it found
- [ ] **4.9** Add approve and reject buttons that update the refund and store the reviewer's decision
- [ ] **4.10** Store reviewer decisions in a form you can export later as labeled data

### Connect and rehearse (steps 4.11 to 4.13)

- [ ] **4.11** Make both apps call run\_ticket and the review functions only, with no business logic of their own
- [ ] **4.12** Run the full path: submit a ticket, find its trace in Phoenix, see an escalation appear in the queue, approve it
- [ ] **4.13** Record a rough two-minute screen capture to check the demo reads clearly

**Exit check:** from a clean start, the whole path works with no more than two commands. Tag the commit v0.4-demo.

## Phase 5: Evaluation

Goal: measure the agent you built, at every level, and show you can improve it with evidence. The agent already runs and is traced, so the evaluators can be built against real traces.

**New in this phase:** a statistics and data library (for example numpy and pandas) for confidence intervals and comparisons, and GitHub Actions for the regression gate. CrewAI and Phoenix are already in place from Phase 3.

### Datasets (steps 5.1 to 5.5)

- [ ] **5.1** Build the full labeled ticket set (at least 120 tickets) with expected intent, tool calls, findings, and resolution
- [ ] **5.2** Add at least 20 adversarial tickets: prompt injection, social engineering, another customer's invoice, over-limit refunds
- [ ] **5.3** Split into 70% development and 30% held-out test, and never tune on the test split
- [ ] **5.4** Write the labeling guide
- [ ] **5.5** Upload the datasets to Phoenix

### Evaluators, code-based first (steps 5.6 to 5.15)

- [ ] **5.6** Intent accuracy, per-class precision and recall, and a confusion matrix
- [ ] **5.7** Tool selection: correct first tool, correct next tool, correct arguments
- [ ] **5.8** Defect-detection precision and recall for each defect type
- [ ] **5.9** Trajectory: convergence score, redundant calls, loops, step and cost distribution
- [ ] **5.10** Outcome: decision class, exact refund amount, policy adherence, groundedness
- [ ] **5.11** Safety suite: injection, unauthorized access, over-limit refunds, hallucinated values
- [ ] **5.12** Fault injection: tool timeouts, malformed output, empty retrieval
- [ ] **5.13** Bootstrap confidence intervals, per-slice breakdowns, at least three repeats per configuration, and latency at p50 and p95 with cost per ticket
- [ ] **5.14** Log every score to Phoenix and store each run with an id, config, and dataset version
- [ ] **5.15** Write tests for the evaluators themselves

### LLM-as-a-judge (steps 5.16 to 5.20)

- [ ] **5.16** Write judge prompt v1 with a rubric, using a different model family from the agent
- [ ] **5.17** Hand-label at least 60 agent outputs
- [ ] **5.18** Measure agreement with accuracy, per-class precision and recall, and Cohen's kappa
- [ ] **5.19** Improve the judge to v2 and report the change
- [ ] **5.20** Check for position, verbosity, and self-preference bias

### Experiments and the regression gate (steps 5.21 to 5.26)

- [ ] **5.21** Define at least four experiments as config files: baseline, improved prompt, cheaper model, and a design ablation such as with and without a verify-before-refund step
- [ ] **5.22** Compare runs on the same tickets and report quality, safety, cost, and latency
- [ ] **5.23** Sort failures into a named taxonomy with counts
- [ ] **5.24** Confirm the winning configuration once on the test split
- [ ] **5.25** Write the decision memo
- [ ] **5.26** Write the regression gate script and the GitHub Actions workflow, and prove it blocks a deliberately worse prompt

**Exit check:** one command runs the full suite on the test split and writes a results file and Phoenix scores, judge agreement is reported, and the gate blocks a worse change. Tag the commit v0.5-eval.

## Phase 6: Monitoring, hardening, and delivery

Goal: turn a working project into a submission a stranger can run and trust.

### Monitoring (steps 6.1 to 6.4)

- [ ] **6.1** Replay at least 500 synthetic tickets as simulated live traffic
- [ ] **6.2** Run online checks on every ticket and the judge on a sample
- [ ] **6.3** Compute escalation rate, tool error rate, refund total, latency p95, and cost per ticket, with alert thresholds
- [ ] **6.4** Inject one regression on purpose and show the monitor catching it

### Hardening (steps 6.5 to 6.7)

- [ ] **6.5** Security pass: secrets only in environment variables, personal data redacted, rate limiting, audit log on every money action
- [ ] **6.6** Re-run the prompt-injection and unauthorized-access tests
- [ ] **6.7** Make sure the whole test suite passes from a clean checkout

### Packaging (steps 6.8 to 6.9)

- [ ] **6.8** Add a Makefile for the commands you have been repeating (setup, test, eval, run the apps)
- [ ] **6.9** Add CI that runs lint and tests on every push, next to the regression gate workflow from Phase 5

### Documentation and delivery (steps 6.10 to 6.16)

- [ ] **6.10** Final architecture diagram and database schema
- [ ] **6.11** Design decision records and a limitations section that says what the system should not be trusted to do yet
- [ ] **6.12** Evaluation report where every number links to a run id
- [ ] **6.13** Prompts used and the AI-assistance disclosure
- [ ] **6.14** One-command Docker setup, and a README that works in five commands or fewer
- [ ] **6.15** Record the 5 to 8 minute walkthrough: ask a ticket, open its trace in Phoenix, handle an escalation, show an experiment comparison, trigger the regression gate
- [ ] **6.16** Test the README on a fresh clone in a new folder

**Exit check:** someone who has never seen the project can run it from the README alone. Tag the commit v1.0.
