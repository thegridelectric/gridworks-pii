"""The store's operations. Each one is a single transaction that writes the
rows and the change record together and commits.

The caller supplies `who`: the operator whose name goes on the change
record. Refusals are exceptions named for the fact they report.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from gwpii.db.models import (
    ChangeSql,
    CustomerSql,
    InstallerSql,
    PartnerLabelSchemeSql,
    PartnerLabelSql,
)
from gwpii.labels import format_label, fresh_draw_list
from gwpii.records import CustomerRecord, InstallerRecord, PartnerLabelRecord


class CustomerExists(Exception):
    """A customer record already exists for this TerminalAsset GNodeId."""


class CustomerMissing(Exception):
    """No customer record exists for this TerminalAsset GNodeId."""


class InstallerMissing(Exception):
    """The installer id on the record names no installer."""


class SchemeExists(Exception):
    """This partner already has a label scheme."""


class SchemeMissing(Exception):
    """This partner has no label scheme to mint from."""


class SchemeExhausted(Exception):
    """Every number in the partner's scheme has been issued."""


class LabelExists(Exception):
    """This house already has a label from this partner."""


def record_change(
    session: Session,
    who: str,
    table_name: str,
    key: str,
    before: dict | None,
    after: dict | None,
) -> None:
    session.add(
        ChangeSql(who=who, table_name=table_name, key=key, before=before, after=after)
    )


def add_scheme(
    session: Session, who: str, partner: str, prefix: str, digits: int
) -> None:
    if session.get(PartnerLabelSchemeSql, partner) is not None:
        raise SchemeExists(partner)
    session.add(
        PartnerLabelSchemeSql(
            partner=partner,
            prefix=prefix,
            digits=digits,
            unissued=fresh_draw_list(digits),
        )
    )
    record_change(
        session,
        who,
        PartnerLabelSchemeSql.__tablename__,
        partner,
        None,
        {"partner": partner, "prefix": prefix, "digits": digits},
    )
    session.commit()


def mint_label(session: Session, who: str, partner: str, ta_g_node_id: str) -> str:
    """Draw the next label for this house from the partner's scheme and record
    it. Part of the caller's transaction: no commit here."""
    scheme = session.execute(
        select(PartnerLabelSchemeSql)
        .where(PartnerLabelSchemeSql.partner == partner)
        .with_for_update()
    ).scalar_one_or_none()
    if scheme is None:
        raise SchemeMissing(partner)
    if session.get(PartnerLabelSql, (ta_g_node_id, partner)) is not None:
        raise LabelExists(f"{partner} {ta_g_node_id}")
    if not scheme.unissued:
        raise SchemeExhausted(partner)
    number, *rest = scheme.unissued
    scheme.unissued = rest
    label = format_label(scheme.prefix, scheme.digits, number)
    row = PartnerLabelSql(
        ta_g_node_id=ta_g_node_id,
        partner=partner,
        label=label,
        issued=datetime.now(UTC).date(),
    )
    session.add(row)
    record_change(
        session,
        who,
        PartnerLabelSql.__tablename__,
        f"{partner}/{label}",
        None,
        PartnerLabelRecord(
            ta_g_node_id=ta_g_node_id, partner=partner, label=label, issued=row.issued
        ).model_dump(mode="json"),
    )
    return label


def customer_exists(session: Session, ta_g_node_id: str) -> bool:
    return session.get(CustomerSql, ta_g_node_id) is not None


def add_customer(
    session: Session, who: str, record: CustomerRecord, partner: str
) -> str:
    """Write the customer and mint their label from the partner's scheme.
    Returns the label. Refused when a record already exists for the GNodeId."""
    if customer_exists(session, record.ta_g_node_id):
        raise CustomerExists(record.ta_g_node_id)
    if (
        record.installer_id is not None
        and session.get(InstallerSql, record.installer_id) is None
    ):
        raise InstallerMissing(record.installer_id)
    session.add(CustomerSql(**record.model_dump()))
    record_change(
        session,
        who,
        CustomerSql.__tablename__,
        record.ta_g_node_id,
        None,
        record.model_dump(mode="json"),
    )
    label = mint_label(session, who, partner, record.ta_g_node_id)
    session.commit()
    return label


def add_installer(session: Session, who: str, record: InstallerRecord) -> None:
    session.add(InstallerSql(**record.model_dump()))
    record_change(
        session,
        who,
        InstallerSql.__tablename__,
        record.id,
        None,
        record.model_dump(mode="json"),
    )
    session.commit()


def get_customer(session: Session, ta_g_node_id: str) -> CustomerRecord:
    row = session.get(CustomerSql, ta_g_node_id)
    if row is None:
        raise CustomerMissing(ta_g_node_id)
    return CustomerRecord.model_validate(row, from_attributes=True)


def get_labels(session: Session, ta_g_node_id: str) -> list[PartnerLabelRecord]:
    rows = session.execute(
        select(PartnerLabelSql).where(PartnerLabelSql.ta_g_node_id == ta_g_node_id)
    ).scalars()
    return [PartnerLabelRecord.model_validate(r, from_attributes=True) for r in rows]


def all_customer_ids(session: Session) -> list[str]:
    return list(
        session.execute(
            select(CustomerSql.ta_g_node_id).order_by(CustomerSql.ta_g_node_id)
        ).scalars()
    )


def all_change_afters(session: Session) -> list[dict | None]:
    return list(session.execute(select(ChangeSql.after)).scalars())
