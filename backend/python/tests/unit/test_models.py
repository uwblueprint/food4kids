from app.models.driver import DriverBase

"""
Sample python test.
For more information on pytest, visit:
https://docs.pytest.org/en/6.2.x/reference.html
"""


def test_create_driver_base() -> None:
    driver_data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+12345678901",
        "address": "123 Main St",
        "license_plate": "ABC123",
        "car_make_model": "Toyota Camry",
    }

    driver = DriverBase(**driver_data)
    assert driver.name == "Jane Doe"
    assert driver.email == "jane@example.com"
    assert driver.phone == "+12345678901"
    assert driver.address == "123 Main St"
    assert driver.license_plate == "ABC123"
    assert driver.car_make_model == "Toyota Camry"
    assert driver.active is True
    assert driver.notes == ""
