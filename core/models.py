from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


class User(models.Model):
    email = models.EmailField(unique=True)

    last_name = models.CharField(max_length=150)
    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True)

    password_hash = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(part for part in parts if part)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_active", "deleted_at", "updated_at"])


class Role(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.slug


class UserRole(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="unique_user_role",
            )
        ]

    def __str__(self):
        return f"{self.user.email} — {self.role.slug}"


class Resource(models.Model):
    code = models.SlugField(unique=True)
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.code


class Action(models.Model):
    code = models.SlugField(unique=True)
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.code


class PermissionRule(models.Model):
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="permission_rules",
    )
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="permission_rules",
    )
    action = models.ForeignKey(
        Action,
        on_delete=models.CASCADE,
        related_name="permission_rules",
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "resource", "action"],
                name="unique_permission_rule",
            )
        ]

    def __str__(self):
        return f"{self.role.slug}: {self.resource.code}:{self.action.code}"