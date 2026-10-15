"""Fill a development store with bogus households.

    uv run python scripts/seed_dev.py --db-url postgresql+psycopg://pii:piipass@localhost:5441/pii --count 12

Takes the database URL on the command line on purpose: it never reads
`.env`, so it cannot be pointed at the real store by accident. The dev
compose file in this repo runs a Postgres on 5441 with those credentials.
"""

import argparse

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from gwpii.seed.dev import seed_dev


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-url", required=True)
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--partner", default="ridgeline")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    with Session(create_engine(args.db_url), expire_on_commit=False) as session:
        written = seed_dev(session, "seed-dev", args.partner, args.count, args.seed)
    for ta, label in written.items():
        print(f"{ta}: {label}")
    print(f"{len(written)} households written")


if __name__ == "__main__":
    main()
