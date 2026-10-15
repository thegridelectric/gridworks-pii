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

## Checks

`./ci.sh` runs lint, format check, pyright and the tests.
