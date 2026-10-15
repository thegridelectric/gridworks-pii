# gridworks-pii

The private customer store for GridWorks houses: the only place a person
is linked to a house. Street address, contact details, the installing
business, and the label each partner knows a house by. Nothing here is
ever published, put on the message broker, or copied into the analytics
database.

The anchor for every record is the house's TerminalAsset GNodeId. No
customer id exists anywhere else in the system, and a record can exist
before the TerminalAsset is active. Coordinates are never stored.

## What is here

- `src/gwpii/` — the `gwpii` package: SQLAlchemy models for the `pii`
  schema, pydantic records, partner-label minting, the store operations
  and the operator CLI.
- `alembic/` — the schema migrations. The baseline creates the `pii`
  schema and its five tables.
- `tests/` — run against an ephemeral Postgres (testcontainers, needs
  Docker).

## Operator setup

```
uv sync --all-groups
cp template.env .env     # fill in GWPII_DB_URL and GWPII_OPERATOR
uv run alembic upgrade head
uv run gwpii --help
```

The CLI runs on the operator's laptop against an ssh tunnel to the
store's box; the database is bound to loopback there.

## Commands

- `gwpii add-scheme <partner> --prefix HH- --digits 3` — register the
  label scheme a partner's houses are named under. Labels are drawn at
  random without replacement, so a label never says when a house was
  enrolled and is never reused.
- `gwpii add-customer <ta-g-node-id> --partner <partner>` — prompts for
  the customer's fields, mints the partner label, records the change,
  prints the label to hand to the partner.
- `gwpii show <ta-g-node-id>` — the record and its labels.

Every write appends a row to `pii.changes` (who, when, table, key,
before, after). A deletion is a real delete plus that row.

## Development store

`docker compose up -d` runs a Postgres on `localhost:5441` (user `pii`,
password `piipass`, database `pii`). Migrate it and fill it with bogus
households:

```
GWPII_DB_URL=postgresql+psycopg://pii:piipass@localhost:5441/pii uv run alembic upgrade head
uv run python scripts/seed_dev.py --db-url postgresql+psycopg://pii:piipass@localhost:5441/pii --count 12
```

The dev seed is deterministic and idempotent, and takes its URL on the
command line so it can never read the operator `.env`. Point the CLI at
the dev store with the same `GWPII_DB_URL` (and any `GWPII_OPERATOR`).

## The seed from journaldb

`scripts/seed_from_journaldb.py` moved the six original households out
of the analytics database, once. It maps each installation's
LeafTransactiveNode GNodeId to the TerminalAsset GNodeId, drops the
coordinates, writes customers and the installer with change records
naming the seed, mints their labels, and runs a row-level check.

## Checks

`./ci.sh` runs lint, format check, pyright and the tests.
