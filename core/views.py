import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from core.decorators import login_required, permission_required
from core.forms import LoginForm, ProfileForm, RegisterForm
from core.models import Action, PermissionRule, Resource, Role, User
from core.services import authenticate_user, login_user, logout_user


DOCUMENTS = [
    {"id": 1, "title": "Договор поставки", "status": "draft"},
    {"id": 2, "title": "Акт выполненных работ", "status": "signed"},
]

REPORTS = [
    {"id": 1, "title": "Отчет по продажам", "period": "2026-Q1"},
    {"id": 2, "title": "Отчет по клиентам", "period": "2026-Q1"},
]

PAYMENTS = [
    {"id": 1, "title": "Счет №1001", "amount": 15000},
    {"id": 2, "title": "Счет №1002", "amount": 23000},
]


def home_view(request):
    return render(request, "home.html")


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.current_user:
        return redirect("home")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = User(
            email=form.cleaned_data["email"],
            last_name=form.cleaned_data["last_name"],
            first_name=form.cleaned_data["first_name"],
            middle_name=form.cleaned_data["middle_name"],
        )
        user.set_password(form.cleaned_data["password"])
        user.save()

        login_user(request, user)

        messages.success(request, "Регистрация выполнена.")
        return redirect("home")

    return render(request, "register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.current_user:
        return redirect("home")

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = authenticate_user(
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )

        if user is None:
            form.add_error(None, "Неверный email или пароль.")
        else:
            login_user(request, user)
            messages.success(request, "Вы вошли в систему.")
            return redirect("home")

    return render(request, "login.html", {"form": form})


@require_http_methods(["POST"])
def logout_view(request):
    logout_user(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect("home")


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    user = request.current_user

    initial = {
        "last_name": user.last_name,
        "first_name": user.first_name,
        "middle_name": user.middle_name,
        "email": user.email,
    }

    form = ProfileForm(request.POST or None, initial=initial, user=user)

    if request.method == "POST":
        if request.POST.get("action") == "delete":
            user.soft_delete()
            logout_user(request)

            messages.warning(request, "Аккаунт деактивирован.")
            return redirect("home")

        if form.is_valid():
            user.last_name = form.cleaned_data["last_name"]
            user.first_name = form.cleaned_data["first_name"]
            user.middle_name = form.cleaned_data["middle_name"]
            user.email = form.cleaned_data["email"]
            user.save()

            messages.success(request, "Профиль обновлен.")
            return redirect("profile")

    return render(request, "profile.html", {"form": form})


@permission_required("documents", "read")
def documents_view(request):
    return render(
        request,
        "business_list.html",
        {
            "title": "Документы",
            "items": DOCUMENTS,
        },
    )


@permission_required("reports", "read")
def reports_view(request):
    return render(
        request,
        "business_list.html",
        {
            "title": "Отчеты",
            "items": REPORTS,
        },
    )


@permission_required("payments", "read")
def payments_view(request):
    return render(
        request,
        "business_list.html",
        {
            "title": "Платежи",
            "items": PAYMENTS,
        },
    )


@permission_required("access-rules", "manage")
@require_http_methods(["GET", "POST"])
def rules_page_view(request):
    if request.method == "POST":
        form_action = request.POST.get("form_action")

        if form_action == "create":
            role_id = request.POST.get("role_id")
            resource_id = request.POST.get("resource_id")
            action_id = request.POST.get("action_id")

            PermissionRule.objects.update_or_create(
                role_id=role_id,
                resource_id=resource_id,
                action_id=action_id,
                defaults={"is_active": True},
            )

            messages.success(request, "Правило сохранено.")
            return redirect("rules_page")

        if form_action == "toggle":
            rule_id = request.POST.get("rule_id")
            rule = PermissionRule.objects.get(id=rule_id)
            rule.is_active = not rule.is_active
            rule.save(update_fields=["is_active"])

            messages.success(request, "Статус правила изменен.")
            return redirect("rules_page")

    context = {
        "roles": Role.objects.all(),
        "resources": Resource.objects.all(),
        "actions": Action.objects.all(),
        "rules": PermissionRule.objects.select_related("role", "resource", "action"),
    }

    return render(request, "rules.html", context)


def parse_body(request):
    if request.content_type == "application/json":
        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    return request.POST


def serialize_rule(rule):
    return {
        "id": rule.id,
        "role": rule.role.slug,
        "resource": rule.resource.code,
        "action": rule.action.code,
        "is_active": rule.is_active,
    }


@permission_required("access-rules", "manage")
@require_http_methods(["GET", "POST"])
def rules_api_view(request):
    if request.method == "GET":
        rules = PermissionRule.objects.select_related("role", "resource", "action")

        return JsonResponse({
            "items": [serialize_rule(rule) for rule in rules]
        })

    data = parse_body(request)

    if data is None:
        return JsonResponse({"detail": "Invalid JSON."}, status=400)

    rule_id = data.get("rule_id")

    if rule_id:
        try:
            rule = PermissionRule.objects.get(id=rule_id)
        except PermissionRule.DoesNotExist:
            return JsonResponse({"detail": "Rule not found."}, status=404)

        is_active = str(data.get("is_active", "true")).lower() in [
            "true",
            "1",
            "yes",
            "on",
        ]

        rule.is_active = is_active
        rule.save(update_fields=["is_active"])

        return JsonResponse({"item": serialize_rule(rule)})

    role_id = data.get("role_id")
    resource_id = data.get("resource_id")
    action_id = data.get("action_id")

    if not role_id or not resource_id or not action_id:
        return JsonResponse(
            {"detail": "role_id, resource_id and action_id are required."},
            status=400,
        )

    rule, created = PermissionRule.objects.update_or_create(
        role_id=role_id,
        resource_id=resource_id,
        action_id=action_id,
        defaults={"is_active": True},
    )

    return JsonResponse(
        {
            "created": created,
            "item": serialize_rule(rule),
        },
        status=201 if created else 200,
    )