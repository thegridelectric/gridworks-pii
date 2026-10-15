"""The `gwpii` console script: the operator's write surface for the store.

Runs on the operator's laptop against an ssh tunnel to the store's loopback
Postgres. `add-customer` is run in the same sitting as `gnregistrar
create`, with the GNodeId copied from the registrar's output. Prompts are
interactive: the record is typed, never passed on the command line.
"""

from __future__ import annotations

import argparse
import sys

from pydantic import ValidationError

from gwpii import store
from gwpii.db.session import open_session
from gwpii.records import CustomerRecord
from gwpii.settings import load_settings

CUSTOMER_PROMPTS: list[tuple[str, str, bool]] = [
    ("first_name", "First name", True),
    ("last_name", "Last name", True),
    ("email", "Email", True),
    ("phone", "Phone", True),
    ("street", "Street", True),
    ("city", "City", True),
    ("state", "State", True),
    ("zip", "ZIP", True),
    ("country", "Country", True),
    ("second_contact_name", "Second contact name (blank for none)", False),
    ("second_contact_email", "Second contact email (blank for none)", False),
    ("second_contact_phone", "Second contact phone (blank for none)", False),
    ("installer_id", "Installer id (blank for none)", False),
]


def prompt_customer(ta_g_node_id: str) -> CustomerRecord:
    fields: dict[str, str | None] = {"ta_g_node_id": ta_g_node_id}
    for name, label, required in CUSTOMER_PROMPTS:
        value = input(f"{label}: ").strip()
        if not value and required:
            raise SystemExit(f"{label} is required")
        fields[name] = value or None
    return CustomerRecord.model_validate(fields)


def cmd_add_scheme(args: argparse.Namespace) -> None:
    settings = load_settings()
    with open_session() as session:
        store.add_scheme(
            session, settings.operator, args.partner, args.prefix, args.digits
        )
    print(f"scheme for {args.partner}: {args.prefix} + {args.digits} digits")


def cmd_add_customer(args: argparse.Namespace) -> None:
    settings = load_settings()
    with open_session() as session:
        if store.customer_exists(session, args.ta_g_node_id):
            raise SystemExit(
                f"a customer record already exists for {args.ta_g_node_id}"
            )
        try:
            record = prompt_customer(args.ta_g_node_id)
        except ValidationError as e:
            raise SystemExit(str(e)) from e
        try:
            label = store.add_customer(session, settings.operator, record, args.partner)
        except store.CustomerExists:
            raise SystemExit(
                f"a customer record already exists for {args.ta_g_node_id}"
            )
        except (store.SchemeMissing, store.InstallerMissing) as e:
            raise SystemExit(f"{type(e).__name__}: {e}")
    print(f"{args.partner} label for {record.first_name} {record.last_name}: {label}")


def cmd_show(args: argparse.Namespace) -> None:
    with open_session() as session:
        try:
            record = store.get_customer(session, args.ta_g_node_id)
        except store.CustomerMissing:
            raise SystemExit(f"no customer record for {args.ta_g_node_id}")
        labels = store.get_labels(session, args.ta_g_node_id)
    for name, value in record.model_dump().items():
        print(f"{name}: {value if value is not None else ''}")
    for lab in labels:
        print(f"label {lab.partner}: {lab.label} (issued {lab.issued})")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gwpii", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add-scheme", help="register a partner's label scheme")
    p.add_argument("partner")
    p.add_argument("--prefix", required=True, help="e.g. HH-")
    p.add_argument(
        "--digits", required=True, type=int, help="random digits after the prefix"
    )
    p.set_defaults(func=cmd_add_scheme)

    p = sub.add_parser(
        "add-customer", help="enter a customer record and mint their label"
    )
    p.add_argument("ta_g_node_id", help="the house's TerminalAsset GNodeId")
    p.add_argument("--partner", required=True, help="whose scheme mints the label")
    p.set_defaults(func=cmd_add_customer)

    p = sub.add_parser("show", help="print a customer record and its labels")
    p.add_argument("ta_g_node_id")
    p.set_defaults(func=cmd_show)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    args.func(args)
