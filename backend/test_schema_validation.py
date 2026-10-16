import pytest
from pydantic import ValidationError

from schemas import UserLogin, UserRegister


def test_registration_accepts_valid_input():
    user = UserRegister(
        email="valid.user@example.com",
        password="SecurePassword123!",
    )

    assert str(user.email) == "valid.user@example.com"
    assert len(user.password) >= 12


def test_registration_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserRegister(
            email="not-an-email",
            password="SecurePassword123!",
        )


def test_registration_rejects_short_password():
    with pytest.raises(ValidationError):
        UserRegister(
            email="valid.user@example.com",
            password="Short123!",
        )


def test_registration_rejects_password_over_128_characters():
    with pytest.raises(ValidationError):
        UserRegister(
            email="valid.user@example.com",
            password="A" * 129,
        )


def test_login_rejects_empty_password():
    with pytest.raises(ValidationError):
        UserLogin(
            email="valid.user@example.com",
            password="",
        )
