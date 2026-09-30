"""REST framework serializers for the news application."""

from rest_framework import serializers

from .models import Article, Newsletter, Publisher, User


class UserSerializer(serializers.ModelSerializer):
    """Serialize public user information for the REST API."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize publisher information and assigned staff members."""

    class Meta:
        model = Publisher
        fields = ["id", "name", "editors", "journalists"]


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize news articles for API responses and updates."""

    class Meta:
        model = Article
        fields = ["id", "title", "content", "author", "publisher", "approved", "created_at"]


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialize newsletters and their related articles."""

    class Meta:
        model = Newsletter
        fields = ["id", "title", "content", "author", "articles", "created_at"]
