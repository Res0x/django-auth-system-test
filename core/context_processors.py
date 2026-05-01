def current_user(request):
    return {
        "current_user": getattr(request, "current_user", None),
    }