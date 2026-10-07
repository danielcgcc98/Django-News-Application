"""Django admin configuration for the news application models."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Article, Newsletter, Publisher, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Configure the Django admin for custom users."""
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        (
            "News Application Information",
            {
                "fields": (
                    "role",
                    "subscribed_publishers",
                    "subscribed_journalists",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "News Application Information",
            {
                "fields": (
                    "role",
                    "subscribed_publishers",
                    "subscribed_journalists",
                )
            },
        ),
    )


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Configure publisher management in Django admin."""
    list_display = ("id", "name")
    filter_horizontal = ("editors", "journalists")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Configure article management in Django admin."""
    list_display = (
        "id",
        "title",
        "author",
        "publisher",
        "approved",
        "created_at",
    )
    list_filter = ("approved", "publisher", "created_at")
    search_fields = ("title", "content")


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Configure newsletter management in Django admin."""
    list_display = ("id", "title", "author", "created_at")
    search_fields = ("title", "description")
    filter_horizontal = ("articles",)
