from firebase_admin import auth
from app import initialize_firebase 

admin_email = "food4kids@uwblueprint.org"

def update_all_users_role(role_name: str):
    """
    Iterates through all Firebase users and sets a custom 'role' claim.
    Always ensures the admin only has the role 'admin'
    """
    initialize_firebase()
    print(f"Starting update: Setting all non admin users to role: {role_name}")
    
    # List all users (paginated)
    page = auth.list_users()
    count = 0

    while page:
        for user in page.users:
            try:
                if user.email == admin_email:
                    auth.set_custom_user_claims(user.uid, {'role': "admin"})
                else:
                    # This overwrites existing claims, so be careful if you have other claims!
                    auth.set_custom_user_claims(user.uid, {'role': role_name})
                
                print(f"Updated UID: {user.uid} ({user.email})")
                count += 1
            except Exception as e:
                print(f"Failed to update {user.uid}: {e}")

        # Get the next page of users
        page = page.get_next_page()

    print(f"\nSuccessfully updated {count} users.")

if __name__ == "__main__":
    # Change to new desired role
    # NOTE: This overwrites preexisting roles so be careful!
    new_role = "driver"
    update_all_users_role(new_role)
