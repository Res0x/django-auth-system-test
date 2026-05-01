from functools import wraps

from django.http import JsonResponse
from django.shortcuts import render

from core.services import has_permission


def is_api_request(request):
    return request.path.startswith("/api/")


def unauthorized(request):
    if is_api_request(request):
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    return render(request, "errors/401.html", status=401)


def forbidden(request):
    if is_api_request(request):
        return JsonResponse({"detail": "Forbidden"}, status=403)

    return render(request, "errors/403.html", status=403)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.current_user:
            return unauthorized(request)

        return view_func(request, *args, **kwargs)

    return wrapper


def permission_required(resource_code, action_code):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.current_user:
                return unauthorized(request)

            if not has_permission(request.current_user, resource_code, action_code):
                return forbidden(request)

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator