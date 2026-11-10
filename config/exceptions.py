from rest_framework.views import exception_handler

ERROR_MESSAGES = {
    "not_authenticated": (
        "Потрібна авторизація. Увійдіть в акаунт і передайте access токен "
        "у заголовку Authorization: Bearer <token>"
    ),
    "authentication_failed": "Не вдалося підтвердити особу. Увійдіть в акаунт знову",
    "no_active_account": "Невірний username або пароль",
    "token_not_valid": (
        "Токен недійсний або термін його дії закінчився. "
        "Оновіть токен або увійдіть знову"
    ),
    "permission_denied": "Недостатньо прав для виконання цієї дії. Потрібні права адміністратора",
}


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None or not isinstance(response.data, dict):
        return response

    detail = response.data.get("detail")
    if detail is not None:
        code = getattr(detail, "code", None)
        response.data = {"error": ERROR_MESSAGES.get(code, str(detail))}
    return response
