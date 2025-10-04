from app.models.enum import RoleEnum
from app.models.user import User

"""
Sample python test.
For more information on pytest, visit:
https://docs.pytest.org/en/6.2.x/reference.html
"""


def test_create_user() -> None:
    user_data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "auth_id": "abc",
        "role": RoleEnum.ADMIN,
    }

    user = User(**user_data)
    assert user.first_name == "Jane"
    assert user.last_name == "Doe"
    assert user.auth_id == "abc"
    assert user.role == RoleEnum.ADMIN
