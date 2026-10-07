"""Application startup hooks for role groups and permissions."""

from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver


ROLE_PERMISSIONS = {
    "Reader": {
        "article": {"view"},
        "newsletter": {"view"},
    },
    "Editor": {
        "article": {"view", "change", "delete"},
        "newsletter": {"view", "change", "delete"},
    },
    "Journalist": {
        "article": {"add", "view", "change", "delete"},
        "newsletter": {"add", "view", "change", "delete"},
    },
}


@receiver(post_migrate)
def configure_role_groups(sender, **kwargs):
    """Create role groups and assign the required model permissions."""
    if sender.name != "news":
        return

    for role_name, model_permissions in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=role_name)
        permissions = []

        for model_name, actions in model_permissions.items():
            for action in actions:
                permission = Permission.objects.filter(
                    content_type__app_label="news",
                    content_type__model=model_name,
                    codename=f"{action}_{model_name}",
                ).first()
                if permission:
                    permissions.append(permission)

        group.permissions.set(permissions)
