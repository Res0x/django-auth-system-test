from core.models import PermissionRule, User


SESSION_USER_ID = "custom_user_id"


def authenticate_user(email, password):
    email = email.strip().lower()

    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return None

    if not user.check_password(password):
        return None

    return user


def login_user(request, user):
    request.session.flush()
    request.session[SESSION_USER_ID] = user.id


def logout_user(request):
    request.session.flush()


def get_current_user(request):
    user_id = request.session.get(SESSION_USER_ID)

    if not user_id:
        return None

    try:
        return User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        request.session.flush()
        return None


def has_permission(user, resource_code, action_code):
    if not user or not user.is_active:
        return False

    return PermissionRule.objects.filter(
        role__user_roles__user=user,
        resource__code=resource_code,
        action__code=action_code,
        is_active=True,
    ).exists()