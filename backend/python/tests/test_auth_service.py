"""Tests for AuthService — token generation, renewal, driver_id, and admin_id propagation."""

from logging import getLogger
from types import SimpleNamespace
from unittest.mock import MagicMock

import jwt
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.models.driver import DriverCreate
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.services.implementations.admin_service import AdminService
from app.services.implementations.auth_service import AuthService
from app.services.implementations.driver_service import DriverService
from app.services.implementations.user_service import UserService


class TestAuthServiceDriverId:
    @pytest.mark.asyncio
    async def test_generate_token_includes_driver_id_for_driver(
        self, test_session: AsyncSession
    ) -> None:
        user = User(
            first_name="Test",
            last_name="Driver",
            email="testdriver@example.com",
            role="driver",
            auth_id="auth-driver-123",
        )
        test_session.add(user)
        await test_session.flush()

        driver_service = DriverService(getLogger(__name__))
        driver = await driver_service.create_driver(
            test_session,
            DriverCreate(
                user_id=user.user_id,
                phone="+12125551234",
                license_plate="ABC123",
                car_make_model="Toyota Camry",
                address="123 Main St, City, State 12345",
            ),
        )
        await test_session.commit()

        user_service = UserService(getLogger(__name__))
        admin_service = AdminService(getLogger(__name__))
        auth_service = AuthService(getLogger(__name__), user_service, driver_service, admin_service)

        token_response = SimpleNamespace(
            access_token="fake-access-token", refresh_token="fake-refresh-token"
        )
        auth_service.firebase_rest_client = MagicMock()
        auth_service.firebase_rest_client.sign_in_with_password.return_value = (
            token_response
        )

        auth_response, _ = await auth_service.generate_token(
            test_session, "testdriver@example.com", "Password123!", remember_me=False
        )

        assert auth_response.driver_id == driver.driver_id
        assert auth_response.admin_id is None

    @pytest.mark.asyncio
    async def test_generate_token_driver_id_none_for_admin(
        self, test_session: AsyncSession
    ) -> None:
        user = User(
            first_name="Test",
            last_name="Admin",
            email="testadmin@example.com",
            role="admin",
            auth_id="auth-admin-123",
        )
        test_session.add(user)
        admin = Admin(
            user_id=user.user_id,
            admin_phone="+12125551234",
            receive_email_notifications=True,
        )
        test_session.add(admin)
        await test_session.commit()

        user_service = UserService(getLogger(__name__))
        driver_service = DriverService(getLogger(__name__))
        admin_service = AdminService(getLogger(__name__))
        auth_service = AuthService(getLogger(__name__), user_service, driver_service, admin_service)

        token_response = SimpleNamespace(
            access_token="fake-access-token", refresh_token="fake-refresh-token"
        )
        auth_service.firebase_rest_client = MagicMock()
        auth_service.firebase_rest_client.sign_in_with_password.return_value = (
            token_response
        )

        auth_response, _ = await auth_service.generate_token(
            test_session, "testadmin@example.com", "Password123!", remember_me=False
        )

        assert auth_response.driver_id is None
        assert auth_response.admin_id == admin.admin_id

    @pytest.mark.asyncio
    async def test_renew_token_includes_driver_id_for_driver(
        self, test_session: AsyncSession
    ) -> None:
        user = User(
            first_name="Test",
            last_name="Driver",
            email="testdriver@example.com",
            role="driver",
            auth_id="auth-driver-456",
        )
        test_session.add(user)
        await test_session.flush()

        driver_service = DriverService(getLogger(__name__))
        driver = await driver_service.create_driver(
            test_session,
            DriverCreate(
                user_id=user.user_id,
                phone="+12125555678",
                license_plate="XYZ789",
                car_make_model="Honda Civic",
                address="456 Oak St, City, State 12345",
            ),
        )
        await test_session.commit()

        user_service = UserService(getLogger(__name__))
        admin_service = AdminService(getLogger(__name__))
        auth_service = AuthService(getLogger(__name__), user_service, driver_service, admin_service)

        access_token = jwt.encode({"sub": "auth-driver-456"}, "k" * 32, "HS256")
        token_response = TokenResponse(
            access_token=access_token, refresh_token="new-refresh-token"
        )
        auth_service.firebase_rest_client = MagicMock()
        auth_service.firebase_rest_client.refresh_token.return_value = token_response

        auth_response, _ = await auth_service.renew_token(
            test_session, "stub-refresh-token", remember_me=True
        )

        assert auth_response.driver_id == driver.driver_id
        assert auth_response.admin_id is None
        assert auth_response.remember_me is True

    @pytest.mark.asyncio
    async def test_renew_token_driver_id_none_for_admin(
        self, test_session: AsyncSession
    ) -> None:
        user = User(
            first_name="Test",
            last_name="Admin",
            email="testadmin@example.com",
            role="admin",
            auth_id="auth-admin-456",
        )
        test_session.add(user)
        admin = Admin(
            user_id=user.user_id,
            admin_phone="+12125551234",
            receive_email_notifications=True,
        )
        test_session.add(admin)
        await test_session.commit()

        user_service = UserService(getLogger(__name__))
        driver_service = DriverService(getLogger(__name__))
        admin_service = AdminService(getLogger(__name__))
        auth_service = AuthService(getLogger(__name__), user_service, driver_service, admin_service)

        access_token = jwt.encode({"sub": "auth-admin-456"}, "k" * 32, "HS256")
        token_response = TokenResponse(
            access_token=access_token, refresh_token="new-refresh-token"
        )
        auth_service.firebase_rest_client = MagicMock()
        auth_service.firebase_rest_client.refresh_token.return_value = token_response

        auth_response, _ = await auth_service.renew_token(
            test_session, "stub-refresh-token", remember_me=False
        )

        assert auth_response.driver_id is None
        assert auth_response.admin_id == admin.admin_id
