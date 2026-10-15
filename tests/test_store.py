"""A customer record round-trips, a second record for the same TA GNodeId is
refused, and labels are drawn without replacement."""

import random

import pytest
from sqlalchemy import select

from gwpii import store
from gwpii.db.models import ChangeSql, PartnerLabelSchemeSql
from gwpii.labels import format_label, fresh_draw_list
from gwpii.records import CustomerRecord

BEECH = "7e152072-c91b-49d2-9ebd-f4fe1b684d06"
OTHER = "0b6f1e0c-8f0b-4f1e-9d7c-2a3b4c5d6e7f"
WHO = "test-operator"


def customer(ta_g_node_id: str = BEECH) -> CustomerRecord:
    return CustomerRecord(
        ta_g_node_id=ta_g_node_id,
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        phone="207-555-0100",
        street="1 Main St",
        city="Millinocket",
        state="ME",
        zip="04462",
        country="US",
    )


def test_customer_round_trips_with_label_and_change_records(session):
    store.add_scheme(session, WHO, "ridgeline", "HH-", 3)
    label = store.add_customer(session, WHO, customer(), "ridgeline")

    assert label.startswith("HH-") and len(label) == 6
    assert store.get_customer(session, BEECH) == customer()
    labels = store.get_labels(session, BEECH)
    assert [(lab.partner, lab.label) for lab in labels] == [("ridgeline", label)]

    changes = session.execute(select(ChangeSql).order_by(ChangeSql.id)).scalars().all()
    assert [(c.table_name, c.key, c.who) for c in changes] == [
        ("partner_label_schemes", "ridgeline", WHO),
        ("customers", BEECH, WHO),
        ("partner_labels", f"ridgeline/{label}", WHO),
    ]
    assert changes[1].before is None
    assert changes[1].after["ta_g_node_id"] == BEECH
    assert "latitude" not in changes[1].after and "longitude" not in changes[1].after


def test_customer_without_email_round_trips(session):
    store.add_scheme(session, WHO, "ridgeline", "HH-", 3)
    rec = customer().model_copy(update={"email": None})
    store.add_customer(session, WHO, rec, "ridgeline")
    assert store.get_customer(session, BEECH).email is None


def test_second_add_customer_for_same_ta_is_refused(session):
    store.add_scheme(session, WHO, "ridgeline", "HH-", 3)
    store.add_customer(session, WHO, customer(), "ridgeline")
    with pytest.raises(store.CustomerExists):
        store.add_customer(session, WHO, customer(), "ridgeline")
    assert len(store.get_labels(session, BEECH)) == 1


def test_add_customer_without_scheme_writes_nothing(session):
    with pytest.raises(store.SchemeMissing):
        store.add_customer(session, WHO, customer(), "ridgeline")
    session.rollback()
    with pytest.raises(store.CustomerMissing):
        store.get_customer(session, BEECH)


def test_labels_are_drawn_without_replacement(session):
    store.add_scheme(session, WHO, "ridgeline", "HH-", 3)
    a = store.add_customer(session, WHO, customer(BEECH), "ridgeline")
    b = store.add_customer(session, WHO, customer(OTHER), "ridgeline")
    assert a != b
    scheme = session.get(PartnerLabelSchemeSql, "ridgeline")
    assert scheme is not None
    assert len(scheme.unissued) == 998
    issued = {int(a[3:]), int(b[3:])}
    assert issued.isdisjoint(scheme.unissued)


def test_one_label_per_partner_per_house(session):
    store.add_scheme(session, WHO, "ridgeline", "HH-", 3)
    store.add_customer(session, WHO, customer(), "ridgeline")
    with pytest.raises(store.LabelExists):
        store.mint_label(session, WHO, "ridgeline", BEECH)


def test_draw_list_covers_every_number_once():
    numbers = fresh_draw_list(3, random.Random(0))
    assert sorted(numbers) == list(range(1000))
    assert format_label("HH-", 3, 7) == "HH-007"


def test_ta_g_node_id_must_be_canonical_uuid():
    with pytest.raises(ValueError):
        customer(BEECH.upper())
    with pytest.raises(ValueError):
        customer("beech")
