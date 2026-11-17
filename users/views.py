import logging

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import RegisterSerializer, UserSerializer

logger = logging.getLogger("users")


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Реєстрація нового користувача",
        description=(
            "Створює новий обліковий запис із перевіркою складності пароля "
            "та унікальності username і email."
        ),
        auth=[],
        request=RegisterSerializer,
        examples=[
            OpenApiExample(
                "Приклад реєстрації",
                value={
                    "username": "hiker",
                    "first_name": "Дарʼя",
                    "last_name": "Синявська",
                    "email": "hiker@example.com",
                    "password": "Strong-Password-2027",
                    "password_confirmation": "Strong-Password-2027",
                },
                request_only=True,
            )
        ],
        responses={
            201: UserSerializer,
            400: OpenApiResponse(description="Помилка валідації даних реєстрації"),
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info("Зареєстровано нового користувача: id=%s", user.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        logger.warning(
            "Невдала спроба реєстрації (невалідні поля: %s)",
            list(serializer.errors.keys()),
        )
        return Response(
            {"error": "Невалідні дані", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


@extend_schema(
    tags=["Auth"],
    summary="Вхід користувача (отримання JWT токенів)",
    description=(
        "Перевіряє username і пароль та повертає пару токенів: access "
        "(передається в заголовку Authorization: Bearer) і refresh "
        "(використовується для оновлення access токена)."
    ),
    auth=[],
)
class LoginView(TokenObtainPairView):
    """Отримання access та refresh токенів"""


@extend_schema(
    tags=["Auth"],
    summary="Оновлення access токена",
    description="Приймає refresh токен і повертає новий access токен.",
    auth=[],
)
class RefreshView(TokenRefreshView):
    """Оновлення access токена за refresh токеном"""


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        summary="Отримати профіль поточного користувача",
        description="Повертає дані авторизованого користувача за JWT access токеном.",
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description="Не передано або недійсний JWT токен"),
        },
    )
    def get(self, request):
        logger.debug("Запит профілю користувача: id=%s", request.user.id)
        return Response(UserSerializer(request.user).data)
