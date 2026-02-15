import os

from firebase_admin import auth

from app import initialize_firebase
from app.models.enum import RoleEnum

admin_email = os.getenv("ADMIN_EMAIL")


def update_all_users_role(role_name: str) -> None:
    """
    Iterates through all Firebase users and sets a custom 'role' claim.
    Always ensures the admin only has the role 'admin'
    """
    print(f"Starting update: Setting all non admin users to role: {role_name}")

    # List all users (paginated)
    page = auth.list_users()
    count = 0

    while page:
        for user in page.users:
            try:
                if user.email == admin_email:
                    auth.set_custom_user_claims(user.uid, {"role": "admin"})
                else:
                    # This overwrites existing claims, so be careful if you have other claims!
                    auth.set_custom_user_claims(user.uid, {"role": role_name})

                print(f"Updated UID: {user.uid} ({user.email})")
                count += 1
            except Exception as e:
                print(f"Failed to update {user.uid}: {e}")

        # Get the next page of users
        page = page.get_next_page()

    print(f"\nSuccessfully updated {count} users.")


def update_user_role(user_email: str, role: str) -> None:
    """
    Update the firebase role of a user given their email
    NOTE: This assumes that your local db has the correct roles set
    """
    try:
        print(f"Updating {user_email} to have {role} role")
        user = auth.get_user_by_email(user_email)
        auth.set_custom_user_claims(user.uid, {"role": role})
    except auth.UserNotFoundError:
        print(f"Error: No user found with email {user_email}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    initialize_firebase()
    # This should only be used to tweak firebase to match your local db
    your_email = ""  # Update as necessary
    update_user_role(your_email, RoleEnum.DRIVER)
