import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from routes.models import MountainRange, Route, StartingPoint

PASSWORD = "Hiker-Pass-2027"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def plain_user(db):
    return User.objects.create_user(
        username="hiker", email="hiker@example.com", password=PASSWORD
    )


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="guide",
        email="guide@example.com",
        password=PASSWORD,
        is_staff=True,
    )


@pytest.fixture
def user_client(plain_user):
    client = APIClient()
    client.force_authenticate(user=plain_user)
    return client


@pytest.fixture
def staff_client(staff_user):
    client = APIClient()
    client.force_authenticate(user=staff_user)
    return client


@pytest.fixture
def mountain_range(db):
    return MountainRange.objects.create(
        name="Чорногора", description="Найвищий масив Українських Карпат"
    )


@pytest.fixture
def starting_point(db):
    return StartingPoint.objects.create(
        name="Ворохта", description="Селище в Івано-Франківській області"
    )


@pytest.fixture
def route(db, mountain_range, starting_point):
    return Route.objects.create(
        name="Говерла з Заросляка",
        description="Класичний підйом на найвищу вершину України",
        distance_km=12.5,
        elevation_gain_m=1050,
        difficulty="medium",
        duration_type="one_day",
        mountain_range=mountain_range,
        starting_point=starting_point,
    )
