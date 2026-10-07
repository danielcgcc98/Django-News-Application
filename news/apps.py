"""Application configuration for the news app."""

from django.apps import AppConfig


class NewsConfig(AppConfig):
    """Configure the News Django application."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "news"

    def ready(self):
        """Register post-migrate signal handlers."""
        from . import signals  # noqa: F401
