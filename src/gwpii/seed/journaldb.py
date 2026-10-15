"""The one-time move of the six existing households out of journaldb.

journaldb's `installations.g_node_id` is the house's LeafTransactiveNode
GNodeId, not the TerminalAsset's. `TA_BY_LTN` maps one to the other, read
from each house's generated hardware layout (`MyLeafTransactiveNodeGNode`
and `MyTerminalAssetGNode`) and checked against the Grid Node Registry
(`g-node-by-alias/hw1.isone.me.versant.keene.<house>.ta`, 2026-10-15).
Latitude and longitude in the address blob are dropped, never copied.
"""

from __future__ import annotations

from typing import NamedTuple

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from gwpii import store
from gwpii.records import CustomerRecord, InstallerRecord

TA_BY_LTN: dict[str, str] = {
    "4da8659f-d455-45f2-ac63-16817c1a6322": "7e152072-c91b-49d2-9ebd-f4fe1b684d06",  # beech
    "d78d1f39-a46c-422a-9ffb-9184feda5920": "51f0618e-78f1-4411-b8b5-ac223f8e8e6d",  # elm
    "db350a9b-ad7e-4da3-9365-6daa752de09e": "d68f5ccd-d69b-4a0e-a849-13ab9b9063e4",  # fir
    "793ca985-8745-4d48-a7ca-850b92dacbf4": "1f4d04ee-6ac8-4ebf-a494-3a0b40557ac2",  # maple
    "b759f5bb-b70c-4052-8587-85e43d6a2290": "0a39d45d-af42-4721-8cdc-51deeed4b80c",  # oak
    "fde9fa11-2235-4af3-8d05-ea196587d733": "9f84ef0e-ca5d-4d7d-bd0f-f8ee99feae61",  # spruce
}


class JournalHouse(NamedTuple):
    """One journaldb installation joined to its customer and installer blobs.

    `ltn_g_node_id` is `installations.g_node_id`; `address`,
    `primary_contact`, `secondary_contact` are the JSONB blobs as stored;
    `installer_id` and `installer_info` come from `installers` (the info
    blob is a bare string naming the business)."""

    display_name: str
    ltn_g_node_id: str
    address: dict
    primary_contact: dict
    secondary_contact: dict | None
    installer_id: str | None
    installer_info: str | None


def read_houses(journal: Connection) -> list[JournalHouse]:
    rows = journal.execute(
        text(
            "select i.display_name, i.g_node_id::text, i.address, "
            "c.primary_contact, c.secondary_contact, i.installer_id::text, n.info "
            "from gridworks.installations i "
            "join gridworks.customers c on c.id = i.customer_id "
            "left join gridworks.installers n on n.id = i.installer_id "
            "order by i.display_name"
        )
    ).all()
    return [JournalHouse(*r) for r in rows]


def contact_name(contact: dict) -> str | None:
    parts = [contact.get("first_name"), contact.get("last_name")]
    name = " ".join(p for p in parts if p)
    return name or None


def customer_from(house: JournalHouse) -> CustomerRecord:
    ta = TA_BY_LTN[house.ltn_g_node_id]
    p = house.primary_contact
    s = house.secondary_contact or {}
    a = house.address
    return CustomerRecord(
        ta_g_node_id=ta,
        first_name=p["first_name"],
        last_name=p["last_name"],
        email=p.get("email") or None,
        phone=p.get("phone") or None,
        street=a["street"],
        city=a["city"],
        state=a["state"],
        zip=a["zip"],
        country=a["country"],
        second_contact_name=contact_name(s),
        second_contact_email=s.get("email") or None,
        second_contact_phone=s.get("phone") or None,
        installer_id=house.installer_id,
    )


def installers_from(houses: list[JournalHouse]) -> list[InstallerRecord]:
    seen: dict[str, InstallerRecord] = {}
    for h in houses:
        if h.installer_id and h.installer_id not in seen:
            seen[h.installer_id] = InstallerRecord(
                id=h.installer_id, name=h.installer_info or ""
            )
    return list(seen.values())


class SeedResult(NamedTuple):
    """What the seed wrote: house display names with the label each got."""

    labels: dict[str, str]
    installers: int


def seed(session: Session, journal: Connection, who: str, partner: str) -> SeedResult:
    """Write every journaldb house into the store. Refuses to run on a store
    that already has a customer; the seed is once."""
    houses = read_houses(journal)
    unknown = [h.ltn_g_node_id for h in houses if h.ltn_g_node_id not in TA_BY_LTN]
    if unknown:
        raise KeyError(f"journaldb houses with no TA mapping: {unknown}")
    for h in houses:
        if store.customer_exists(session, TA_BY_LTN[h.ltn_g_node_id]):
            raise store.CustomerExists(h.display_name)
    installers = installers_from(houses)
    for rec in installers:
        store.add_installer(session, who, rec)
    labels = {
        h.display_name: store.add_customer(session, who, customer_from(h), partner)
        for h in houses
    }
    return SeedResult(labels=labels, installers=len(installers))


def check(session: Session, expected: int) -> list[str]:
    """Row-level check after the seed: every customer has a label and no
    change record mentions a coordinate. Returns the problems found."""
    problems: list[str] = []
    customers = store.all_customer_ids(session)
    if len(customers) != expected:
        problems.append(f"{len(customers)} customers, expected {expected}")
    for ta in customers:
        if not store.get_labels(session, ta):
            problems.append(f"{ta} has no label")
    for after in store.all_change_afters(session):
        if after and ({"latitude", "longitude"} & set(after)):
            problems.append("a change record carries coordinates")
    return problems
