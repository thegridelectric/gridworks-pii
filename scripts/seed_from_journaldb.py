"""Run the one-time seed: journaldb's six households into the pii store.

    GWPII_SEED_JOURNAL_URL=<the gw_analyst read login> uv run python scripts/seed_from_journaldb.py --partner ridgeline

Reads journaldb with the URL in `GWPII_SEED_JOURNAL_URL` (a SELECT-only
login; never the journalkeeper's) and writes the store named by the usual
`.env` (`GWPII_DB_URL` over the tunnel). Prints each house's new label and
the row-level check. Refuses a store that already has a customer.
"""

import argparse
import os
import sys
from datetime import UTC, datetime

from sqlalchemy import create_engine

from gwpii.db.session import open_session
from gwpii.seed.journaldb import check, seed
from gwpii.settings import load_settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--partner", required=True, help="whose scheme mints the labels"
    )
    args = parser.parse_args()
    url = os.environ.get("GWPII_SEED_JOURNAL_URL")
    if not url:
        sys.exit("set GWPII_SEED_JOURNAL_URL to the journaldb read login")
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    who = f"seed-from-journaldb-{datetime.now(UTC).date()}-{load_settings().operator}"
    journal = create_engine(url)
    with journal.connect() as jc, open_session() as session:
        result = seed(session, jc, who, args.partner)
        for house, label in result.labels.items():
            print(f"{house}: {label}")
        print(f"installers: {result.installers}")
        problems = check(session, len(result.labels))
    if problems:
        sys.exit("CHECK FAILED: " + "; ".join(problems))
    print(
        f"check passed: {len(result.labels)} customers, each labelled, no coordinates"
    )


if __name__ == "__main__":
    main()
