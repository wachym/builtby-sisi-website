# Sisi OS — backend

Django 6.1 + Django Ninja Extra. The system of record: the append-only
delivery ledger and the services built on it.

Phase 0 of the programme plan is implemented here: the spine. Perception,
cognition, and settlement apps are scaffolded with their bounded contexts and
land in later phases.

## Run it

```bash
cd backend
python -m venv venv && venv/Scripts/activate     # Windows; use bin/activate elsewhere
python -m pip install -r requirements-dev.txt
cp .env.example .env                             # then edit
python manage.py migrate
python manage.py runserver                       # or the ASGI server below
```

ASGI is what production runs, and what the telemetry socket will need:

```bash
uvicorn bbsbackend.asgi:application --host 0.0.0.0 --port 8000
```

With Postgres and Redis from the repository root:

```bash
docker compose -f ../infra/docker-compose.yml up -d
# then set DATABASE_URL=postgres://sisi:sisi@localhost:5432/sisi in .env
```

## Try the ledger

```bash
python manage.py ledger_demo        # appends one complete Loop (DEBUG only)
python manage.py ledger_verify --signatures
python manage.py ledger_anchor --date 2026-09-08
```

```
GET  /api/v1/system/health          liveness + migration state
GET  /api/v1/ledger/head            chain head — the cheapest integrity check
GET  /api/v1/ledger/events          paginated, filterable by type and subject
GET  /api/v1/ledger/verify          re-derives every hash and reports breaks
GET  /api/v1/ledger/anchors         daily Merkle roots
POST /api/v1/ledger/events          append — requires X-Internal-Key
GET  /api/v1/docs                   interactive API documentation
```

## Settings

There is no importable default settings module, so no environment is ever
selected by accident:

| Module | Use |
| --- | --- |
| `bbsbackend.settings.dev` | Local development. DEBUG on, signatures optional. |
| `bbsbackend.settings.test` | In-memory database, deterministic. |
| `bbsbackend.settings.prod` | Refuses to start on SQLite, without a secret key, without allowed hosts, or with signatures disabled. |

`.env.example` is the environment contract. `.env` is gitignored and must
never be committed.

## The ledger

Every meaningful act is one row in `ledger_event`, hash-chained to its
predecessor and signed by its actor. Two rules make it worth trusting:

1. **It is append-only.** `save()` refuses updates, `delete()` refuses, the
   default queryset refuses bulk writes, and database triggers reject `UPDATE`
   and `DELETE` outright — so raw SQL and a careless future migration are
   covered too. Corrections are new events, never edits.
2. **It is verifiable.** `/api/v1/ledger/verify` re-derives every hash from the
   returned fields. A day of events reduces to a Merkle root (`ledger_anchor`),
   which Phase 5 publishes on-chain so an outsider can check that the history
   was not rewritten.

Write through `apps.ledger.services.append_event()`. Constructing an `Event`
directly is rejected: a row without a computed chain is worse than no row.

`apps/ledger/hashing.py` defines what a hash covers. Treat it as append-only
too — changing it invalidates every anchored root.

## Tests

```bash
python -m pytest
```

The suite covers canonical hashing and Merkle construction, chain linkage and
tamper detection, all four append-only guards, signing and its refusals,
anchoring idempotence, the HTTP surface, and the OpenAPI contract that the
frontend client is generated from.

## The contract with the frontend

```bash
python manage.py export_openapi -o openapi.json      # regenerate
python manage.py export_openapi -o openapi.json --check   # CI: fail if stale
```

`openapi.json` is generated, gitignored, and consumed by `app/bbs` to produce
typed API access. A backend change that would break the frontend fails in CI
rather than in a browser.

## Layout

```
bbsbackend/       settings package, ASGI/WSGI, URL mounting, API composition root
apps/core/        health, version, OpenAPI export
apps/ledger/      the spine: events, hashing, signing, anchoring, verification
apps/accounts/    clients, API keys, permissions        (models: Phase 2)
apps/intake/      leads, briefs, estimates              (Phase 2)
apps/vision/      model registry, server inference      (Phase 1)
apps/agents/      runs, steps, approvals, budgets       (Phase 2)
apps/telemetry/   devices, sessions, perception events  (Phase 4)
apps/rails/       invoices, escrow, yield, metering     (Phase 3)
tests/            pytest suite
```

Controllers are registered centrally in `bbsbackend/api.py` so the public
surface is reviewable in one file.
