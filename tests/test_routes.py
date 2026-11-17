import pytest
from django.urls import reverse

from routes.models import Route

pytestmark = pytest.mark.django_db


@pytest.fixture
def route_payload(mountain_range, starting_point):
    return {
        "name": "Шпиці",
        "description": "Мальовничий масив у Чорногорі",
        "distance_km": 12.5,
        "elevation_gain_m": 1050,
        "difficulty": "easy",
        "duration_type": "one_day",
        "gear": ["трекінгове взуття", "дощовик"],
        "mountain_range": mountain_range.pk,
        "starting_point": starting_point.pk,
    }


def route_url(pk):
    return reverse("route-detail", args=[pk])


def test_anyone_can_list_routes(api_client, route):
    response = api_client.get(reverse("route-list"))

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == route.name
    assert data[0]["gear"] == []


def test_get_missing_route_returns_404(api_client):
    response = api_client.get(route_url(9999))

    assert response.status_code == 404
    assert response.json() == {"error": "Маршрут не знайдено"}


def test_create_route_without_token_returns_401(api_client, route_payload):
    response = api_client.post(reverse("route-list"), route_payload, format="json")

    assert response.status_code == 401
    assert Route.objects.count() == 0


def test_create_route_as_regular_user_returns_403(user_client, route_payload):
    response = user_client.post(reverse("route-list"), route_payload, format="json")

    assert response.status_code == 403
    assert Route.objects.count() == 0


def test_staff_can_create_route_with_gear(staff_client, route_payload):
    response = staff_client.post(reverse("route-list"), route_payload, format="json")

    assert response.status_code == 201
    data = response.json()
    assert sorted(data["gear"]) == sorted(route_payload["gear"])
    assert Route.objects.filter(name=route_payload["name"]).exists()


def test_create_route_with_invalid_difficulty_returns_400(staff_client, route_payload):
    route_payload["difficulty"] = "impossible"

    response = staff_client.post(reverse("route-list"), route_payload, format="json")

    assert response.status_code == 400
    assert "difficulty" in response.json()["details"]


def test_create_route_with_missing_range_returns_400(staff_client, route_payload):
    route_payload["mountain_range"] = 9999

    response = staff_client.post(reverse("route-list"), route_payload, format="json")

    assert response.status_code == 400
    assert "mountain_range" in response.json()["details"]


def test_staff_can_update_route_gear(staff_client, route):
    payload = {"gear": ["компас", "ліхтарик"]}

    response = staff_client.patch(route_url(route.pk), payload, format="json")

    assert response.status_code == 200
    assert sorted(response.json()["gear"]) == ["компас", "ліхтарик"]


def test_staff_can_change_route_difficulty(staff_client, route):
    response = staff_client.patch(
        route_url(route.pk), {"difficulty": "hard"}, format="json"
    )

    assert response.status_code == 200
    route.refresh_from_db()
    assert route.difficulty == "hard"


def test_staff_can_delete_route(staff_client, route):
    pk = route.pk

    response = staff_client.delete(route_url(pk))

    assert response.status_code == 204
    assert not Route.objects.filter(pk=pk).exists()


def test_regular_user_cannot_delete_route(user_client, route):
    response = user_client.delete(route_url(route.pk))

    assert response.status_code == 403
    assert Route.objects.filter(pk=route.pk).exists()
