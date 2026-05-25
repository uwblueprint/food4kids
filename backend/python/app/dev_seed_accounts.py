"""
Provision local test accounts (Firebase + database) for manual API/UI testing.

Creates email-verified accounts with known passwords and the right role custom
claims, plus matching DB rows, so they can log in AND be authorized:

    admin@food4kids.dev    / Password123!    (role=admin)
    driver@food4kids.dev   / Password123!    (role=driver)

Run AFTER seeding the database (`python -m app.seed_database` clears all tables):

    docker compose exec backend python -m app.dev_seed_accounts

Idempotent — safe to re-run. LOCAL DEVELOPMENT ONLY; never point this at a
shared/production Firebase project.
"""

import contextlib

from firebase_admin import auth as fb_auth
from sqlalchemy import create_engine
from sqlmodel import Session, select

from app import initialize_firebase
from app.models.admin import Admin
from app.models.driver import Driver
from app.models.user import User

# Mirrors app/seed_database.py — the dev database inside docker compose.
DATABASE_URL = "postgresql://postgres:postgres@f4k_db:5432/f4k"
PASSWORD = "Password123!"

ACCOUNTS = [
    {"email": "admin@food4kids.dev", "name": "Dev Admin", "role": "admin"},
    {"email": "driver@food4kids.dev", "name": "Dev Driver", "role": "driver"},
]
TEST_PHONE = "+12125551234"


def _ensure_firebase_user(email: str, password: str, role: str) -> str:
    """Create or update a Firebase user: known password, verified email, role claim."""
    try:
        user = fb_auth.get_user_by_email(email)
        fb_auth.update_user(user.uid, password=password, email_verified=True)
    except fb_auth.UserNotFoundError:
        user = fb_auth.create_user(email=email, password=password, email_verified=True)
    fb_auth.set_custom_user_claims(user.uid, {"role": role})
    return str(user.uid)


def main() -> None:
    # ValueError if the default Firebase app is already initialized.
    with contextlib.suppress(ValueError):
        initialize_firebase()

    engine = create_engine(DATABASE_URL, echo=False)
    with Session(engine) as session:
        for acct in ACCOUNTS:
            uid = _ensure_firebase_user(acct["email"], PASSWORD, acct["role"])

            # Upsert the DB user by email; login matches on email, ownership on auth_id.
            user = session.exec(select(User).where(User.email == acct["email"])).first()
            if user is None:
                user = User(
                    name=acct["name"],
                    email=acct["email"],
                    auth_id=uid,
                    role=acct["role"],
                )
            else:
                user.auth_id = uid
                user.role = acct["role"]
            session.add(user)
            session.commit()
            session.refresh(user)

            if acct["role"] == "driver":
                driver = session.exec(
                    select(Driver).where(Driver.user_id == user.user_id)
                ).first()
                if driver is None:
                    session.add(
                        Driver(
                            user_id=user.user_id,
                            phone=TEST_PHONE,
                            address="123 Dev St, Toronto, ON",
                            license_plate="DEV123",
                            car_make_model="Test Car",
                        )
                    )
                    session.commit()
            else:  # admin
                admin = session.exec(
                    select(Admin).where(Admin.user_id == user.user_id)
                ).first()
                if admin is None:
                    session.add(Admin(user_id=user.user_id, admin_phone=TEST_PHONE))
                    session.commit()

            print(f"  {acct['role']:<6} {acct['email']}  (uid={uid})")

    print(f"\nDone. Log in with password: {PASSWORD}")


if __name__ == "__main__":
    main()
