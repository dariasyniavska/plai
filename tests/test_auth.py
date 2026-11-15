import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db

PASSWORD = "Hiker-Pass-2027"


@pytest.fixture
def register_data():
    return {
        "username": "daria",
        "first_name": "Дарʼя",
        "last_name": "Синявська",
        "email": "daria@example.com",
        "password": PASSWORD,
        "password_confirmation": PASSWORD,
    }


def register(client, data):
    return client.post(reverse("register"), data, format="json")


def login(client, username, password):
    return client.post(
        reverse("login"), {"username": username, "password": password}, format="json"
    )


def test_register_creates_user_with_hashed_password(api_client, register_data):
    response = register(api_client, register_data)

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "daria"
    assert "password" not in data
    assert "password_confirmation" not in data

    user = User.objects.get(username="daria")
    assert user.password != PASSWORD
    assert user.check_password(PASSWORD)


def test_register_passwords_must_match(api_client, register_data):
    register_data["password_confirmation"] = "Another-Pass-2027"

    response = register(api_client, register_data)

    assert response.status_code == 400
    assert "password_confirmation" in response.json()["details"]
    assert not User.objects.filter(username="daria").exists()


def test_register_rejects_invalid_email(api_client, register_data):
    register_data["email"] = "not-an-email"

    response = register(api_client, register_data)

    assert response.status_code == 400
    assert "email" in response.json()["details"]


def test_register_rejects_weak_password(api_client, register_data):
    register_data["password"] = "12345678"
    register_data["password_confirmation"] = "12345678"

    response = register(api_client, register_data)

    assert response.status_code == 400
    assert "password" in response.json()["details"]


def test_register_rejects_too_short_password(api_client, register_data):
    register_data["password"] = "Ab1"
    register_data["password_confirmation"] = "Ab1"

    response = register(api_client, register_data)

    assert response.status_code == 400
    assert "password" in response.json()["details"]


def test_register_rejects_too_long_username(api_client, register_data):
    register_data["username"] = "a" * 151

    response = register(api_client, register_data)

    assert response.status_code == 400
    assert "username" in response.json()["details"]


def test_register_rejects_existing_username(api_client, register_data, plain_user):
    register_data["username"] = plain_user.username

    response = register(api_client, register_data)

    assert response.status_code == 400
    assert "username" in response.json()["details"]


def test_register_rejects_existing_email(api_client, register_data, plain_user):
    register_data["email"] = plain_user.email

    response = register(api_client, register_data)

    assert response.status_code == 400
    assert "email" in response.json()["details"]


def test_register_requires_all_mandatory_fields(api_client):
    response = register(api_client, {})

    assert response.status_code == 400
    details = response.json()["details"]
    for field in ("username", "email", "password", "password_confirmation"):
        assert field in details


def test_login_returns_access_and_refresh_tokens(api_client, plain_user):
    response = login(api_client, "hiker", PASSWORD)

    assert response.status_code == 200
    data = response.json()
    assert "access" in data
    assert "refresh" in data


def test_login_with_wrong_password_returns_401(api_client, plain_user):
    response = login(api_client, "hiker", "wrong-password")

    assert response.status_code == 401
    assert response.json() == {"error": "Невірний username або пароль"}


def test_refresh_returns_new_access_token(api_client, plain_user):
    refresh = login(api_client, "hiker", PASSWORD).json()["refresh"]

    response = api_client.post(
        reverse("token-refresh"), {"refresh": refresh}, format="json"
    )

    assert response.status_code == 200
    assert "access" in response.json()


def test_refresh_with_invalid_token_returns_401(api_client):
    response = api_client.post(
        reverse("token-refresh"), {"refresh": "not-a-real-token"}, format="json"
    )

    assert response.status_code == 401
    assert response.json()["error"].startswith("Токен недійсний")


def test_me_requires_authentication(api_client):
    response = api_client.get(reverse("me"))

    assert response.status_code == 401


def test_me_rejects_invalid_token(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer broken-token")

    response = api_client.get(reverse("me"))

    assert response.status_code == 401
    assert response.json()["error"].startswith("Токен недійсний")


def test_me_returns_current_user_for_valid_token(api_client, plain_user):
    access = login(api_client, "hiker", PASSWORD).json()["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = api_client.get(reverse("me"))

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "hiker"
    assert data["is_staff"] is False


def test_me_shows_staff_flag_for_admin(staff_client):
    response = staff_client.get(reverse("me"))

    assert response.status_code == 200
    assert response.json()["is_staff"] is True
