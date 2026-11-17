import logging

from django.db.models import ProtectedError
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MountainRange, Route, StartingPoint
from .permissions import IsAdminOrReadOnly
from .serializers import (
    MountainRangeSerializer,
    RouteSerializer,
    StartingPointSerializer,
)

logger = logging.getLogger("routes")


class BaseListView(APIView):
    model = None
    serializer_class = None
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        items = self.model.objects.all()
        logger.debug(
            "Отримано список %s (кількість: %d)", self.model.__name__, items.count()
        )
        serializer = self.serializer_class(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            logger.info(
                "Створено %s (id=%s) користувачем id=%s",
                self.model.__name__,
                obj.id,
                request.user.id,
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        logger.warning(
            "Помилка валідації при створенні %s (поля: %s)",
            self.model.__name__,
            list(serializer.errors.keys()),
        )
        return Response(
            {"error": "Невалідні дані", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class BaseDetailView(APIView):
    model = None
    serializer_class = None
    resource_name = ""
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self, pk):
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            logger.warning("%s з id=%s не знайдено", self.resource_name, pk)
            return Response(
                {"error": f"{self.resource_name} не знайдено"},
                status=status.HTTP_404_NOT_FOUND,
            )
        logger.debug("Отримано деталі %s (id=%s)", self.model.__name__, pk)
        serializer = self.serializer_class(obj)
        return Response(serializer.data)

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            logger.warning(
                "Спроба оновлення неіснуючого ресурсу: %s (id=%s)",
                self.resource_name,
                pk,
            )
            return Response(
                {"error": f"{self.resource_name} не знайдено"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.serializer_class(obj, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            logger.info(
                "Оновлено %s (id=%s) користувачем id=%s",
                self.model.__name__,
                pk,
                request.user.id,
            )
            return Response(serializer.data)

        logger.warning(
            "Помилка валідації при оновленні %s (id=%s, поля: %s)",
            self.model.__name__,
            pk,
            list(serializer.errors.keys()),
        )
        return Response(
            {"error": "Невалідні дані", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            logger.warning(
                "Спроба видалення неіснуючого ресурсу: %s (id=%s)",
                self.resource_name,
                pk,
            )
            return Response(
                {"error": f"{self.resource_name} не знайдено"},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            obj.delete()
            logger.info(
                "Видалено %s (id=%s) користувачем id=%s",
                self.model.__name__,
                pk,
                request.user.id,
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            logger.warning(
                "Конфлікт видалення %s (id=%s): існують пов'язані маршрути",
                self.resource_name,
                pk,
            )
            return Response(
                {
                    "error": (
                        f"Неможливо видалити {self.resource_name.lower()}, "
                        "оскільки існують пов'язані маршрути"
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )


@extend_schema_view(
    get=extend_schema(
        tags=["Mountain Ranges"],
        summary="Отримати список гірських масивів",
        description="Публічний ендпоінт. Повертає перелік усіх гірських масивів.",
        responses={200: MountainRangeSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Mountain Ranges"],
        summary="Створити новий гірський масив",
        description="Доступно лише авторизованим адміністраторам (is_staff=True).",
        request=MountainRangeSerializer,
        examples=[
            OpenApiExample(
                "Приклад створення гірського масиву",
                value={
                    "name": "Чорногора",
                    "description": "Найвищий гірський масив Українських Карпат",
                },
                request_only=True,
            )
        ],
        responses={
            201: MountainRangeSerializer,
            400: OpenApiResponse(description="Невалідні дані запиту"),
            401: OpenApiResponse(description="Потрібна JWT-автентифікація"),
            403: OpenApiResponse(description="Потрібні права адміністратора"),
        },
    ),
)
class MountainRangeList(BaseListView):
    model = MountainRange
    serializer_class = MountainRangeSerializer


@extend_schema_view(
    get=extend_schema(
        tags=["Mountain Ranges"],
        summary="Отримати деталі гірського масиву",
        responses={
            200: MountainRangeSerializer,
            404: OpenApiResponse(description="Гірський масив не знайдено"),
        },
    ),
    patch=extend_schema(
        tags=["Mountain Ranges"],
        summary="Частково оновити гірський масив",
        description="Доступно лише адміністраторам.",
        request=MountainRangeSerializer,
        responses={
            200: MountainRangeSerializer,
            400: OpenApiResponse(description="Невалідні дані"),
            401: OpenApiResponse(description="Потрібна JWT-автентифікація"),
            403: OpenApiResponse(description="Потрібні права адміністратора"),
            404: OpenApiResponse(description="Гірський масив не знайдено"),
        },
    ),
    delete=extend_schema(
        tags=["Mountain Ranges"],
        summary="Видалити гірський масив",
        description="Видаляє масив, якщо до нього не прив'язані маршрути.",
        responses={
            204: OpenApiResponse(description="Гірський масив видалено"),
            401: OpenApiResponse(description="Потрібна JWT-автентифікація"),
            403: OpenApiResponse(description="Потрібні права адміністратора"),
            404: OpenApiResponse(description="Гірський масив не знайдено"),
            409: OpenApiResponse(description="Конфлікт: існують пов'язані маршрути"),
        },
    ),
)
class MountainRangeDetail(BaseDetailView):
    model = MountainRange
    serializer_class = MountainRangeSerializer
    resource_name = "Гірський масив"


class MountainRangeRoutesList(APIView):
    @extend_schema(
        tags=["Mountain Ranges"],
        summary="Отримати маршрути гірського масиву",
        responses={
            200: RouteSerializer(many=True),
            404: OpenApiResponse(description="Гірський масив не знайдено"),
        },
    )
    def get(self, request, pk):
        if not MountainRange.objects.filter(pk=pk).exists():
            logger.warning("Запит маршрутів для неіснуючого масиву id=%s", pk)
            return Response(
                {"error": "Гірський масив не знайдено"},
                status=status.HTTP_404_NOT_FOUND,
            )

        routes = Route.objects.filter(mountain_range_id=pk)
        logger.debug(
            "Отримано маршрути масиву id=%s (кількість: %d)", pk, routes.count()
        )
        serializer = RouteSerializer(routes, many=True)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        tags=["Starting Points"],
        summary="Отримати список стартових точок",
        responses={200: StartingPointSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Starting Points"],
        summary="Створити нову стартову точку",
        description="Доступно лише адміністраторам.",
        request=StartingPointSerializer,
        responses={
            201: StartingPointSerializer,
            400: OpenApiResponse(description="Невалідні дані"),
            401: OpenApiResponse(description="Потрібна JWT-автентифікація"),
            403: OpenApiResponse(description="Потрібні права адміністратора"),
        },
    ),
)
class StartingPointList(BaseListView):
    model = StartingPoint
    serializer_class = StartingPointSerializer


@extend_schema_view(
    get=extend_schema(
        tags=["Starting Points"],
        summary="Отримати деталі стартової точки",
        responses={
            200: StartingPointSerializer,
            404: OpenApiResponse(description="Стартову точку не знайдено"),
        },
    ),
    patch=extend_schema(
        tags=["Starting Points"],
        summary="Частково оновити стартову точку",
        description="Доступно лише адміністраторам.",
        request=StartingPointSerializer,
        responses={
            200: StartingPointSerializer,
            400: OpenApiResponse(description="Невалідні дані"),
            401: OpenApiResponse(description="Потрібна JWT-автентифікація"),
            403: OpenApiResponse(description="Потрібні права адміністратора"),
            404: OpenApiResponse(description="Стартову точку не знайдено"),
        },
    ),
    delete=extend_schema(
        tags=["Starting Points"],
        summary="Видалити стартову точку",
        description="Видаляє стартову точку, якщо до неї не прив'язані маршрути.",
        responses={
            204: OpenApiResponse(description="Стартову точку видалено"),
            401: OpenApiResponse(description="Потрібна JWT-автентифікація"),
            403: OpenApiResponse(description="Потрібні права адміністратора"),
            404: OpenApiResponse(description="Стартову точку не знайдено"),
            409: OpenApiResponse(description="Конфлікт: існують пов'язані маршрути"),
        },
    ),
)
class StartingPointDetail(BaseDetailView):
    model = StartingPoint
    serializer_class = StartingPointSerializer
    resource_name = "Стартова точка"


class StartingPointRoutesList(APIView):
    @extend_schema(
        tags=["Starting Points"],
        summary="Отримати маршрути стартової точки",
        responses={
            200: RouteSerializer(many=True),
            404: OpenApiResponse(description="Стартовий пункт не знайдено"),
        },
    )
    def get(self, request, pk):
        if not StartingPoint.objects.filter(pk=pk).exists():
            logger.warning("Запит маршрутів для неіснуючої стартової точки id=%s", pk)
            return Response(
                {"error": "Стартовий пункт не знайдено"},
                status=status.HTTP_404_NOT_FOUND,
            )

        routes = Route.objects.filter(starting_point_id=pk)
        logger.debug(
            "Отримано маршрути стартової точки id=%s (кількість: %d)",
            pk,
            routes.count(),
        )
        serializer = RouteSerializer(routes, many=True)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        tags=["Routes"],
        summary="Отримати список усіх туристичних маршрутів",
        description="Публічний ендпоінт. Доступний усім користувачам без токена.",
        responses={200: RouteSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Routes"],
        summary="Створити новий туристичний маршрут",
        description=(
            "Доступно лише авторизованим адміністраторам (is_staff=True). "
            "Поле gear приймає список назв рекомендованого спорядження."
        ),
        request=RouteSerializer,
        examples=[
            OpenApiExample(
                "Приклад створення маршруту",
                value={
                    "name": "Говерла з Заросляка",
                    "description": "Класичний підйом на найвищу вершину України",
                    "distance_km": 12.5,
                    "elevation_gain_m": 1050,
                    "difficulty": "medium",
                    "duration_type": "one_day",
                    "gear": ["трекінгове взуття", "дощовик"],
                    "mountain_range": 1,
                    "starting_point": 1,
                },
                request_only=True,
            )
        ],
        responses={
            201: RouteSerializer,
            400: OpenApiResponse(description="Невалідні дані запиту"),
            401: OpenApiResponse(description="Потрібна JWT-автентифікація"),
            403: OpenApiResponse(description="Потрібні права адміністратора"),
        },
    ),
)
class RouteList(BaseListView):
    model = Route
    serializer_class = RouteSerializer


@extend_schema_view(
    get=extend_schema(
        tags=["Routes"],
        summary="Отримати деталі туристичного маршруту",
        responses={
            200: RouteSerializer,
            404: OpenApiResponse(description="Маршрут не знайдено"),
        },
    ),
    patch=extend_schema(
        tags=["Routes"],
        summary="Частково оновити туристичний маршрут",
        description="Доступно лише адміністраторам. Дозволяє змінити окремі поля.",
        request=RouteSerializer,
        examples=[
            OpenApiExample(
                "Оновлення складності маршруту",
                value={"difficulty": "hard"},
                request_only=True,
            )
        ],
        responses={
            200: RouteSerializer,
            400: OpenApiResponse(description="Невалідні дані"),
            401: OpenApiResponse(description="Потрібна JWT-автентифікація"),
            403: OpenApiResponse(description="Потрібні права адміністратора"),
            404: OpenApiResponse(description="Маршрут не знайдено"),
        },
    ),
    delete=extend_schema(
        tags=["Routes"],
        summary="Видалити туристичний маршрут",
        description="Доступно лише адміністраторам.",
        responses={
            204: OpenApiResponse(description="Маршрут видалено"),
            401: OpenApiResponse(description="Потрібна JWT-автентифікація"),
            403: OpenApiResponse(description="Потрібні права адміністратора"),
            404: OpenApiResponse(description="Маршрут не знайдено"),
        },
    ),
)
class RouteDetail(BaseDetailView):
    model = Route
    serializer_class = RouteSerializer
    resource_name = "Маршрут"
