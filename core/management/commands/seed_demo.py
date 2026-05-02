from django.core.management.base import BaseCommand

from core.models import Action, PermissionRule, Resource, Role, User, UserRole


class Command(BaseCommand):
    help = "Create demo users, roles, resources, actions and permission rules."

    def handle(self, *args, **options):
        read_action, _ = Action.objects.get_or_create(
            code="read",
            defaults={"title": "Чтение"},
        )

        manage_action, _ = Action.objects.get_or_create(
            code="manage",
            defaults={"title": "Управление"},
        )

        documents, _ = Resource.objects.get_or_create(
            code="documents",
            defaults={"title": "Документы"},
        )

        reports, _ = Resource.objects.get_or_create(
            code="reports",
            defaults={"title": "Отчеты"},
        )

        payments, _ = Resource.objects.get_or_create(
            code="payments",
            defaults={"title": "Платежи"},
        )

        access_rules, _ = Resource.objects.get_or_create(
            code="access-rules",
            defaults={"title": "Правила доступа"},
        )

        admin_role, _ = Role.objects.get_or_create(
            slug="admin",
            defaults={"title": "Администратор"},
        )

        manager_role, _ = Role.objects.get_or_create(
            slug="manager",
            defaults={"title": "Менеджер"},
        )

        reader_role, _ = Role.objects.get_or_create(
            slug="reader",
            defaults={"title": "Читатель"},
        )

        admin = self.create_user(
            email="admin@example.com",
            password="Admin123!",
            last_name="Админов",
            first_name="Админ",
        )

        manager = self.create_user(
            email="manager@example.com",
            password="Manager123!",
            last_name="Менеджеров",
            first_name="Максим",
        )

        reader = self.create_user(
            email="reader@example.com",
            password="Reader123!",
            last_name="Читателей",
            first_name="Роман",
        )

        inactive = self.create_user(
            email="inactive@example.com",
            password="Inactive123!",
            last_name="Удаленный",
            first_name="Пользователь",
        )
        inactive.is_active = False
        inactive.save(update_fields=["is_active"])

        UserRole.objects.get_or_create(user=admin, role=admin_role)
        UserRole.objects.get_or_create(user=manager, role=manager_role)
        UserRole.objects.get_or_create(user=reader, role=reader_role)

        self.allow(admin_role, documents, read_action)
        self.allow(admin_role, reports, read_action)
        self.allow(admin_role, payments, read_action)
        self.allow(admin_role, access_rules, manage_action)

        self.allow(manager_role, documents, read_action)
        self.allow(manager_role, reports, read_action)

        self.allow(reader_role, documents, read_action)

        self.stdout.write(self.style.SUCCESS("Demo data created."))

    def create_user(self, email, password, last_name, first_name):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "last_name": last_name,
                "first_name": first_name,
                "middle_name": "",
                "is_active": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()

        return user

    def allow(self, role, resource, action):
        PermissionRule.objects.update_or_create(
            role=role,
            resource=resource,
            action=action,
            defaults={"is_active": True},
        )