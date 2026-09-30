from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Publisher, Article, Newsletter


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for the custom news application user."""
    list_display = (
        'username',
        'email',
        'role',
        'is_staff',
        'is_active',
    )

    list_filter = (
        'role',
        'is_staff',
        'is_active',
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            'News Application Information',
            {
                'fields': (
                    'role',
                    'subscribed_publishers',
                    'subscribed_journalists',
                )
            }
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'News Application Information',
            {
                'fields': (
                    'role',
                    'subscribed_publishers',
                    'subscribed_journalists',
                )
            }
        ),
    )


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Admin configuration for publishers and their staff."""
    list_display = (
        'id',
        'name',
    )

    filter_horizontal = (
        'editors',
        'journalists',
    )


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin configuration for news articles."""
    list_display = (
        'id',
        'title',
        'author',
        'publisher',
        'approved',
        'created_at',
    )

    list_filter = (
        'approved',
        'publisher',
        'created_at',
    )

    search_fields = (
        'title',
        'content',
    )


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Admin configuration for newsletters."""
    list_display = (
        'id',
        'title',
        'author',
        'created_at',
    )

    search_fields = (
        'title',
        'content',
    )

    filter_horizontal = (
        'articles',
    )