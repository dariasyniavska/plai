import pytest
from django.urls import reverse

from routes.models import MountainRange

pytestmark = pytest.mark.django_db

NEW_RANGE = {
    "name": "Ґорґани",
    "description": "Скелястий масив у Східних Карпат",
}
CHANGE = {"description": "Новий опис масиву"}


def range_url(pk):
    return reverse("range-detail", args=[pk])


def test_anyone_can_list_ranges(api_client, mountain_range):
    response = api_client.get(reverse("range-list"))

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Чорногора"


def test_anyone_can_get_range(api_client, mountain_range):
    response = api_client.get(range_url(mountain_range.pk))

    assert response.status_code == 200
    assert response.json()["name"] == mountain_range.name


def test_get_missing_range_returns_404(api_client):
    response = api_client.get(range_url(9999))

    assert response.status_code == 404
    assert response.json() == {"error": "Гірський масив не знайдено"}


def test_create_range_without_token_returns_401(api_client):
    response = api_client.post(reverse("range-list"), NEW_RANGE, format="json")

    assert response.status_code == 401
    assert response.json()["error"].startswith("Потрібна авторизація")
    assert MountainRange.objects.count() == 0


def test_create_range_as_regular_user_returns_403(user_client):
    response = user_client.post(reverse("range-list"), NEW_RANGE, format="json")

    assert response.status_code == 403
    assert response.json()["error"].startswith("Недостатньо прав")
    assert MountainRange.objects.count() == 0


def test_create_range_as_staff_returns_201(staff_client):
    response = staff_client.post(reverse("range-list"), NEW_RANGE, format="json")

    assert response.status_code == 201
    assert response.json()["name"] == NEW_RANGE["name"]
    assert MountainRange.objects.filter(name=NEW_RANGE["name"]).exists()


def test_create_range_with_invalid_data_returns_400(staff_client):
    payload = {"description": "Масив без назви"}

    response = staff_client.post(reverse("range-list"), payload, format="json")

    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "Невалідні дані"
    assert "name" in data["details"]
    assert MountainRange.objects.count() == 0


def test_update_range_without_token_returns_401(api_client, mountain_range):
    url = range_url(mountain_range.pk)

    response = api_client.patch(url, CHANGE, format="json")

    assert response.status_code == 401
    mountain_range.refresh_from_db()
    assert mountain_range.description != CHANGE["description"]


def test_update_range_as_regular_user_returns_403(user_client, mountain_range):
    url = range_url(mountain_range.pk)

    response = user_client.patch(url, CHANGE, format="json")

    assert response.status_code == 403
    mountain_range.refresh_from_db()
    assert mountain_range.description != CHANGE["description"]


def test_update_range_as_staff_changes_description(staff_client, mountain_range):
    url = range_url(mountain_range.pk)

    response = staff_client.patch(url, CHANGE, format="json")

    assert response.status_code == 200
    assert response.json()["description"] == CHANGE["description"]
    mountain_range.refresh_from_db()
    assert mountain_range.description == CHANGE["description"]


def test_update_missing_range_returns_404(staff_client):
    response = staff_client.patch(range_url(9999), CHANGE, format="json")

    assert response.status_code == 404
    assert response.json() == {"error": "Гірський масив не знайдено"}


def test_update_range_with_empty_name_returns_400(staff_client, mountain_range):
    url = range_url(mountain_range.pk)

    response = staff_client.patch(url, {"name": ""}, format="json")

    assert response.status_code == 400
    assert "name" in response.json()["details"]


def test_delete_range_without_token_returns_401(api_client, mountain_range):
    response = api_client.delete(range_url(mountain_range.pk))

    assert response.status_code == 401
    assert MountainRange.objects.filter(pk=mountain_range.pk).exists()


def test_delete_range_as_regular_user_returns_403(user_client, mountain_range):
    response = user_client.delete(range_url(mountain_range.pk))

    assert response.status_code == 403
    assert MountainRange.objects.filter(pk=mountain_range.pk).exists()


def test_delete_range_as_staff_returns_204(staff_client, mountain_range):
    pk = mountain_range.pk

    response = staff_client.delete(range_url(pk))

    assert response.status_code == 204
    assert not MountainRange.objects.filter(pk=pk).exists()


def test_delete_missing_range_returns_404(staff_client):
    response = staff_client.delete(range_url(9999))

    assert response.status_code == 404
    assert response.json() == {"error": "Гірський масив не знайдено"}


def test_delete_range_with_routes_returns_409(staff_client, mountain_range, route):
    response = staff_client.delete(range_url(mountain_range.pk))

    assert response.status_code == 409
    assert "пов'язані маршрути" in response.json()["error"]
    assert MountainRange.objects.filter(pk=mountain_range.pk).exists()


def test_list_routes_of_range(api_client, mountain_range, route):
    url = f"/api/v1/mountain-ranges/{mountain_range.pk}/routes/"

    response = api_client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == route.name


def test_list_routes_of_missing_range_returns_404(api_client):
    response = api_client.get("/api/v1/mountain-ranges/9999/routes/")

    assert response.status_code == 404
    assert response.json() == {"error": "Гірський масив не знайдено"}
