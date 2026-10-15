"""The record shapes the CLI takes in and the store hands back.

Pydantic validates what an operator types before any row is written. These
are not sema words and never will be: they do not travel.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


def check_g_node_id(v: str) -> str:
    """A GNodeId is a lowercase canonical UUID string."""
    canonical = str(UUID(v))
    if canonical != v:
        raise ValueError(
            f"GNodeId must be the canonical lowercase UUID form: {canonical}"
        )
    return v


class CustomerRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    ta_g_node_id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    street: str
    city: str
    state: str
    zip: str
    country: str
    second_contact_name: str | None = None
    second_contact_email: EmailStr | None = None
    second_contact_phone: str | None = None
    installer_id: str | None = None

    @field_validator("ta_g_node_id")
    @classmethod
    def ta_is_g_node_id(cls, v: str) -> str:
        return check_g_node_id(v)

    @field_validator("installer_id")
    @classmethod
    def installer_is_uuid(cls, v: str | None) -> str | None:
        return None if v is None else check_g_node_id(v)


class InstallerRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str
    name: str
    contact_name: str
    email: EmailStr
    phone: str

    @field_validator("id")
    @classmethod
    def id_is_uuid(cls, v: str) -> str:
        return check_g_node_id(v)


class PartnerLabelRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ta_g_node_id: str
    partner: str
    label: str
    issued: date
