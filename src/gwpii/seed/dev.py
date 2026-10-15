"""Bogus households for a development store.

Deterministic from an integer seed, so a dev database, a test and a
teammate's laptop all hold the same made-up people. The TA GNodeIds are
uuid5 under a fixed namespace: stable, and never a real house's id.
Nothing here is a real person; the names are drawn from short word lists.
"""

from __future__ import annotations

import random
import uuid

from sqlalchemy.orm import Session

from gwpii import store
from gwpii.records import CustomerRecord, InstallerRecord

NAMESPACE = uuid.UUID("3b2c1d0e-0000-4000-8000-00000000d0d0")
FIRST = [
    "Ada",
    "Grace",
    "Linus",
    "Edsger",
    "Barbara",
    "Ken",
    "Dennis",
    "Radia",
    "Frances",
    "Alan",
]
LAST = [
    "Lovelace",
    "Hopper",
    "Torvalds",
    "Dijkstra",
    "Liskov",
    "Thompson",
    "Ritchie",
    "Perlman",
    "Allen",
    "Turing",
]
STREETS = [
    "Penobscot Ave",
    "Katahdin Ave",
    "Aroostook Ave",
    "Granite St",
    "Spring St",
    "Summer St",
]
TOWNS = [("Millinocket", "04462"), ("East Millinocket", "04430"), ("Medway", "04460")]


def dev_installer() -> InstallerRecord:
    return InstallerRecord(
        id=str(uuid.uuid5(NAMESPACE, "installer")),
        name="Dev Heating Co",
        contact_name="Pat Fixit",
        email="pat@example.com",
        phone="207-555-0199",
    )


def dev_customer(i: int, rng: random.Random, installer_id: str) -> CustomerRecord:
    town, zip_code = rng.choice(TOWNS)
    first, last = rng.choice(FIRST), rng.choice(LAST)
    has_second = rng.random() < 0.5
    return CustomerRecord(
        ta_g_node_id=str(uuid.uuid5(NAMESPACE, f"house-{i}")),
        first_name=first,
        last_name=last,
        email=f"{first.lower()}.{last.lower()}{i}@example.com"
        if rng.random() < 0.7
        else None,
        phone=f"207-555-{rng.randint(0, 199):04d}",
        street=f"{rng.randint(1, 400)} {rng.choice(STREETS)}",
        city=town,
        state="ME",
        zip=zip_code,
        country="US",
        second_contact_name=f"{rng.choice(FIRST)} {last}" if has_second else None,
        second_contact_phone=f"207-555-{rng.randint(0, 199):04d}"
        if has_second
        else None,
        installer_id=installer_id,
    )


def seed_dev(
    session: Session, who: str, partner: str, count: int, seed: int = 0
) -> dict[str, str]:
    """Register the partner's scheme if missing, add the dev installer and
    `count` households. Skips households already present, so re-runs add
    nothing. Returns TA GNodeId to label for the ones written."""
    rng = random.Random(seed)
    if session.get(store.PartnerLabelSchemeSql, partner) is None:
        store.add_scheme(session, who, partner, "HH-", 3)
    installer = dev_installer()
    if session.get(store.InstallerSql, installer.id) is None:
        store.add_installer(session, who, installer)
    written: dict[str, str] = {}
    for i in range(count):
        rec = dev_customer(i, rng, installer.id)
        if store.customer_exists(session, rec.ta_g_node_id):
            continue
        written[rec.ta_g_node_id] = store.add_customer(session, who, rec, partner)
    return written
