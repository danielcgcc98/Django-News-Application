"""REST framework serializers for the news application."""

from rest_framework import serializers

from .models import Article, Newsletter, Publisher, User


class UserSerializer(serializers.ModelSerializer):
    """Serialize user profile data needed by the API."""

    class Meta:
        """Configure serialized User fields."""
        model = User
        fields = ["id", "username", "email", "role"]


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize publisher details and assigned staff."""

    class Meta:
        """Configure serialized Publisher fields."""
        model = Publisher
        fields = ["id", "name", "editors", "journalists"]


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize article content and publication state."""

    class Meta:
        """Configure serialized Article fields."""
        model = Article
        fields = ["id", "title", "content", "author", "publisher", "approved", "created_at"]
        read_only_fields = ["id", "author", "approved", "created_at"]


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialize newsletters while allowing only approved articles."""

    class Meta:
        """Configure serialized Newsletter fields."""
        model = Newsletter
        fields = ["id", "title", "description", "author", "articles", "created_at"]
        read_only_fields = ["id", "author", "created_at"]

    def validate_articles(self, articles):
        """Reject newsletter selections containing unapproved articles."""
        unapproved = [article.title for article in articles if not article.approved]
        if unapproved:
            raise serializers.ValidationError(
                "Only approved articles can be added to a newsletter."
            )
        return articles
