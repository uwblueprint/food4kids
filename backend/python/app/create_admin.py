#!/usr/bin/env python3
"""Create an F4K admin account and email the person the link that finishes it.

Run by a Blueprint developer with database access; there is deliberately no
in-app way to mint an admin. Usage:

    python -m app.create_admin --email jane@food4kids.ca --name "Jane Doe"

``--phone`` is accepted too, and optional.

It inserts three rows — ``users`` (role=admin, ``auth_id`` still NULL),
``admin_info``, and a ``user_invites`` row — and sends the same
``account-creation`` email drivers get, carrying

    {FRONTEND_BASE_URL}/create-password/{user_invite_id}

all in one transaction: if the email cannot be sent, the rows are rolled back
and nothing is created. The link is never printed. The recipient opens it and
sets their own password; ``POST /auth/register`` then creates the Firebase
user, stamps the ``role: admin`` custom claim, and writes ``auth_id`` back.
Both halves matter: authorization reads the Firebase claim, so a
``users.role = 'admin'`` row on its own grants nothing until the link is used.

Needs the mailer credentials (``MAILER_USER``, ``MAILER_CLIENT_ID``,
``MAILER_CLIENT_SECRET``, ``MAILER_REFRESH_TOKEN``) alongside the database
settings; the compose backend gets them from the root ``.env``.

This script never sees or prints a password, and — unlike ``seed_database`` —
it deletes nothing.
"""

import argparse
import asyncio
import sys
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

import app.models as models
from app.config import settings
from app.dependencies.services import get_email_dispatcher
from app.models.admin import Admin
from app.models.user import User
from app.models.user_invite import UserInvite
from app.services.implementations.email_dispatcher import EmailDispatcher
from app.utilities.utils import build_invite_url

# Kept in sync with UserInviteBase.expires_at's default (48 hours); it is what
# the email and the operator message both quote.
INVITE_VALID_HOURS = 48

MAILER_SETTINGS = (
    "mailer_user",
    "mailer_client_id",
    "mailer_client_secret",
    "mailer_refresh_token",
)


class EmailAlreadyRegisteredError(Exception):
    """``users.email`` is unique — this address already belongs to someone."""


async def create_admin_account(
    session: AsyncSession,
    email_dispatcher: EmailDispatcher,
    *,
    email: str,
    first_name: str,
    last_name: str,
    phone: str | None = None,
) -> UserInvite:
    """Insert the admin user, its ``admin_info`` row, and its invite, then email it.

    Flushes but does not commit, so the caller owns the transaction and a
    failure anywhere — the email not sending included — leaves no partial
    account behind. Sending inside the transaction is what makes that true:
    an invite that exists but was never delivered is unreachable, since the
    link is not printed.

    :raises EmailAlreadyRegisteredError: the address is already taken. Checked
        up front for a readable message; the unique index is still the real
        guarantee if two runs race.
    """
    existing = await session.scalar(select(User.user_id).where(User.email == email))
    if existing is not None:
        raise EmailAlreadyRegisteredError(
            f"{email} already belongs to user {existing}. "
            "Admin accounts are keyed by email, so pick a different address or "
            "delete the existing user first."
        )

    # Build all three rows before adding any of them: constructing them is what
    # runs the validators (a bad email, an unparseable phone), and doing that
    # up front means a rejected input never reaches the session at all. The
    # user_id is a client-side uuid4, so the children can reference it without
    # a flush first.
    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        auth_id=None,
        role="admin",
    )
    admin = Admin(user_id=user.user_id, admin_phone=phone)
    invite = UserInvite(user_id=user.user_id)

    # The user row has to land before the two that carry an FK to it.
    session.add(user)
    await session.flush()
    session.add(admin)
    session.add(invite)
    await session.flush()

    await email_dispatcher.dispatch(
        email_type="account-creation",
        to=email,
        context={
            "Name_To_Replace": f"{first_name} {last_name}",
            "Sign_Up_URL": build_invite_url(invite.user_invite_id),
            "Hours_Till_Expiry": INVITE_VALID_HOURS,
        },
    )

    return invite


def split_name(name: str) -> tuple[str, str]:
    """Split ``--name`` into the first/last name the ``users`` table requires.

    Both columns are NOT NULL with ``min_length=1``, so a single-word name is
    rejected rather than stored with an invented blank half.
    """
    parts = name.split()
    if len(parts) < 2:
        raise ValueError(
            f"--name must include a first and last name (got {name!r}). "
            'Quote the whole thing, e.g. --name "Jane Doe".'
        )
    return parts[0], " ".join(parts[1:])


async def _run(email: str, name: str, phone: str | None) -> UUID:
    """Open a session against the configured database and create the account."""
    first_name, last_name = split_name(name)

    # The Gmail client only discovers missing credentials when it tries to
    # send, as an OAuth error; name the settings up front instead.
    missing = [key for key in MAILER_SETTINGS if not getattr(settings, key)]
    if missing:
        raise RuntimeError(
            "The invite is sent by email, which needs "
            + ", ".join(key.upper() for key in missing)
            + " set in the environment."
        )

    # Reuse the app's own engine setup rather than building a URL here: it is
    # what handles a managed-Postgres connection string (Neon's sslmode/
    # channel_binding params, which asyncpg rejects as connect() kwargs).
    models.init_database()
    session_maker = models.async_session_maker_instance
    if session_maker is None or models.async_engine is None:
        raise RuntimeError("Database initialization did not produce a session maker.")

    # Outside production that engine echoes every statement, which would bury
    # the confirmation the operator actually needs.
    models.async_engine.sync_engine.echo = False

    try:
        async with session_maker() as session, session.begin():
            invite = await create_admin_account(
                session,
                get_email_dispatcher(),
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
            )
            return invite.user_invite_id
    finally:
        if models.async_engine is not None:
            await models.async_engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.create_admin",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--email", required=True, help="The admin's email address.")
    parser.add_argument(
        "--name", required=True, help='Full name, e.g. --name "Jane Doe".'
    )
    parser.add_argument(
        "--phone",
        default=None,
        help=(
            "Optional contact phone, normalized to RFC 3966 on the way in. "
            "Omit it if you don't have one — the account is created without."
        ),
    )
    args = parser.parse_args(argv)

    try:
        user_invite_id = asyncio.run(_run(args.email, args.name, args.phone))
    # ValidationError subclasses ValueError, so it has to be caught first or the
    # branch is dead. It reports a bad --email or --phone, and pydantic's own
    # rendering names the offending field — worth keeping over a one-liner.
    except ValidationError as e:
        print(f"error: invalid input\n{e}", file=sys.stderr)
        return 1
    except (EmailAlreadyRegisteredError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    # Missing mailer settings, or the send itself failing. Either way the
    # transaction rolled back, so there is nothing to clean up before retrying.
    except RuntimeError as e:
        print(f"error: {e}\nNo account was created.", file=sys.stderr)
        return 1

    print(
        f"Created admin account for {args.email} and emailed them the link to "
        f"set their password (invite {user_invite_id})."
    )
    print(
        f"The link is single-use and expires in {INVITE_VALID_HOURS} hours. "
        "If it lapses, delete the unfinished user and run this again."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
