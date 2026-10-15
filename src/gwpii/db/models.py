"""SQLAlchemy models for the `pii` schema.

`customers.ta_g_node_id` is the TerminalAsset GNodeId and the primary key.
It is an opaque identifier here: no foreign key references it, in this
database or any other. The installer reference is the one foreign key in
the schema, and it stays inside it.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

SCHEMA = "pii"


class Base(DeclarativeBase):
    metadata = MetaData(schema=SCHEMA)


class CustomerSql(Base):
    """The household behind a house, keyed by the house's TerminalAsset GNodeId."""

    __tablename__ = "customers"

    ta_g_node_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)
    street: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    zip: Mapped[str] = mapped_column(String)
    country: Mapped[str] = mapped_column(String)
    second_contact_name: Mapped[str | None] = mapped_column(String, nullable=True)
    second_contact_email: Mapped[str | None] = mapped_column(String, nullable=True)
    second_contact_phone: Mapped[str | None] = mapped_column(String, nullable=True)
    installer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("installers.id"), nullable=True
    )
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InstallerSql(Base):
    """The business that installed a house's heating system."""

    __tablename__ = "installers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String)
    contact_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PartnerLabelSql(Base):
    """The name a partner knows a house by: the only bridge between a
    partner's world and a public GNode alias, as sensitive as the address."""

    __tablename__ = "partner_labels"
    __table_args__ = (UniqueConstraint("partner", "label"),)

    ta_g_node_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    partner: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str] = mapped_column(String)
    issued: Mapped[date] = mapped_column(Date)


class PartnerLabelSchemeSql(Base):
    """How a partner's labels are formed, with the shuffled draw list of
    numbers not yet issued. A number leaves the list when issued and never
    returns."""

    __tablename__ = "partner_label_schemes"

    partner: Mapped[str] = mapped_column(String, primary_key=True)
    prefix: Mapped[str] = mapped_column(String)
    digits: Mapped[int] = mapped_column(Integer)
    unissued: Mapped[list[int]] = mapped_column(JSONB)


class ChangeSql(Base):
    """Append-only record of every write: who, when, which table and key,
    the row before and after. Audit and deletability rest on this table."""

    __tablename__ = "changes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    who: Mapped[str] = mapped_column(String)
    table_name: Mapped[str] = mapped_column(String)
    key: Mapped[str] = mapped_column(String)
    before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
