import logging, time
logger = logging.getLogger("booksite_functions.middleware")


class RequestLoggingMiddleware:
    def __init__(self, get_responce):
        self.get_responce = get_responce

    def __call__(self, request):
        start = time.monotonic()
        responce = self.get_responce(request)
        elapsed = (time.monotonic() - start) * 1000
        user = getattr(request, "user", "anonymous")
        logger.info("[%s] %s %s -> %s (%.1f ms)", user, request.method, request.get_full_path(), responce.status_code, elapsed)
        return responce


class RolePermissionMiddleware:
    EXCLUDED = ['/account/', '/admin/', '/login/', '/register/', '/__debug__/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(path) for path in self.EXCLUDED):
            return self.get_response(request)

        user = getattr(request, "user", None)
        request.can_edit = bool(user and user.is_authenticated and getattr(user, "is_editor", False))
        return self.get_response(request)