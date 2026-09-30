"""Database models for the news application."""

from django.contrib.auth.models import AbstractUser, Group
from django.db import models


class User(AbstractUser):
    """Custom user model with news application roles and subscriptions."""

    ROLE_CHOICES = [
        ("Reader", "Reader"),
        ("Journalist", "Journalist"),
        ("Editor", "Editor"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="Reader")

    subscribed_publishers = models.ManyToManyField(
        "Publisher",
        blank=True,
        related_name="subscribed_readers",
    )

    subscribed_journalists = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="reader_subscribers",
        limit_choices_to={"role": "Journalist"},
    )

    def save(self, *args, **kwargs):
        """Save the user and keep their role group synchronized."""
        super().save(*args, **kwargs)
        group, _ = Group.objects.get_or_create(name=self.role)
        self.groups.set([group])


class Publisher(models.Model):
    """A publication that can have editors, journalists and subscribers."""

    name = models.CharField(max_length=200)

    editors = models.ManyToManyField(
        User,
        blank=True,
        related_name="publisher_editor_roles",
        limit_choices_to={"role": "Editor"},
    )

    journalists = models.ManyToManyField(
        User,
        blank=True,
        related_name="publisher_journalist_roles",
        limit_choices_to={"role": "Journalist"},
    )

    def __str__(self):
        return self.name


class Article(models.Model):
    """A news article written by a journalist and optionally linked to a publisher."""

    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="articles")
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="articles",
    )
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    """A curated collection of articles published by a journalist or editor."""

    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="newsletters")
    articles = models.ManyToManyField(Article, blank=True, related_name="newsletters")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
