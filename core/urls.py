from django.urls import path

from core import views


urlpatterns = [
    path("", views.home_view, name="home"),

    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),

    path("business/documents/", views.documents_view, name="documents"),
    path("business/reports/", views.reports_view, name="reports"),
    path("business/payments/", views.payments_view, name="payments"),

    path("rules/", views.rules_page_view, name="rules_page"),

    path("api/rules/", views.rules_api_view, name="rules_api"),
]