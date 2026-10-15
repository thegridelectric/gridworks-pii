"""The journaldb seed maps the six houses onto the store, and the dev seed
fills a store deterministically."""

import json

import pytest
from sqlalchemy import text

from gwpii import store
from gwpii.seed.dev import seed_dev
from gwpii.seed.journaldb import TA_BY_LTN, check, seed

WHO = "seed-test"
LTN_IDS = list(TA_BY_LTN)
HOUSES = ["beech", "elm", "fir", "maple", "oak", "spruce"]
INSTALLER = "a87d4323-0000-4000-8000-000000000001"


def make_fake_journaldb(conn) -> None:
    conn.execute(text("drop schema if exists gridworks cascade"))
    conn.execute(text("create schema gridworks"))
    conn.execute(
        text(
            "create table gridworks.customers (id uuid primary key, primary_contact jsonb, secondary_contact jsonb);"
            "create table gridworks.installers (id uuid primary key, info jsonb);"
            "create table gridworks.installations (id uuid primary key, g_node_id uuid, display_name varchar,"
            " customer_id uuid, installer_id uuid, address jsonb)"
        )
    )
    conn.execute(
        text("insert into gridworks.installers values (:id, :info)"),
        {"id": INSTALLER, "info": json.dumps("Fake Heating LLC")},
    )
    for i, (house, ltn) in enumerate(zip(HOUSES, LTN_IDS, strict=True)):
        cust = f"c0000000-0000-4000-8000-00000000000{i}"
        primary = {
            "first_name": "Pat",
            "last_name": house.title(),
            "phone": f"207-555-010{i}",
            "email": None,
        }
        secondary = (
            {"first_name": "Sam", "last_name": None, "phone": None, "email": None}
            if i % 2
            else None
        )
        address = {
            "street": f"{i} Elm St",
            "city": "Millinocket",
            "state": "ME",
            "zip": "04462",
            "country": "US",
            "latitude": 45.65,
            "longitude": -68.71,
        }
        conn.execute(
            text("insert into gridworks.customers values (:id, :p, :s)"),
            {
                "id": cust,
                "p": json.dumps(primary),
                "s": json.dumps(secondary) if secondary else None,
            },
        )
        conn.execute(
            text(
                "insert into gridworks.installations values (:id, :g, :n, :c, :inst, :a)"
            ),
            {
                "id": f"a0000000-0000-4000-8000-00000000000{i}",
                "g": ltn,
                "n": house,
                "c": cust,
                "inst": INSTALLER,
                "a": json.dumps(address),
            },
        )
    conn.commit()


def test_journaldb_seed_moves_six_houses_without_coordinates(session, engine):
    store.add_scheme(session, WHO, "ridgeline", "HH-", 3)
    with engine.connect() as jc:
        make_fake_journaldb(jc)
        result = seed(session, jc, WHO, "ridgeline")
    assert sorted(result.labels) == HOUSES
    assert result.installers == 1
    assert check(session, 6) == []

    beech = store.get_customer(session, TA_BY_LTN[LTN_IDS[0]])
    assert (beech.last_name, beech.email, beech.street, beech.installer_id) == (
        "Beech",
        None,
        "0 Elm St",
        INSTALLER,
    )
    assert beech.second_contact_name is None
    elm = store.get_customer(session, TA_BY_LTN[LTN_IDS[1]])
    assert elm.second_contact_name == "Sam"
    assert not hasattr(beech, "latitude")

    with engine.connect() as jc, pytest.raises(store.CustomerExists):
        seed(session, jc, WHO, "ridgeline")


def test_check_reports_missing_label(session):
    store.add_scheme(session, WHO, "ridgeline", "HH-", 3)
    seed_dev(session, WHO, "ridgeline", 2)
    session.execute(text("delete from pii.partner_labels"))
    session.commit()
    assert len(check(session, 2)) == 2


def test_dev_seed_is_deterministic_and_idempotent(session):
    first = seed_dev(session, WHO, "ridgeline", 5, seed=7)
    assert len(first) == 5
    again = seed_dev(session, WHO, "ridgeline", 5, seed=7)
    assert again == {}
    ids = store.all_customer_ids(session)
    assert len(ids) == 5
    for ta in ids:
        rec = store.get_customer(session, ta)
        assert rec.state == "ME" and rec.installer_id is not None
        assert rec.email is None or rec.email.endswith("@example.com")
