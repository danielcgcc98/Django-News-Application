"""REST API views for the news application."""

import logging

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, Newsletter, Publisher
from .serializers import (
    ArticleSerializer,
    NewsletterSerializer,
    PublisherSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def get_user_role(user):
    """Return a user role in lowercase form."""
    return getattr(user, "role", "").lower()


class ArticleListCreateAPIView(APIView):
    """List approved articles or create an article as a journalist."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Handle an authenticated GET request."""
        articles = Article.objects.filter(
            approved=True
        ).order_by("-created_at")
        return Response(ArticleSerializer(articles, many=True).data)

    def post(self, request):
        """Handle an authenticated POST request."""
        if get_user_role(request.user) != "journalist":
            return Response(
                {"detail": "Only journalists can create articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            article = serializer.save(author=request.user, approved=False)
            return Response(
                ArticleSerializer(article).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class SubscribedArticlesAPIView(APIView):
    """Return approved articles from the reader's subscriptions."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return approved articles that match the reader's subscriptions."""
        if get_user_role(request.user) != "reader":
            return Response(
                {"detail": "Only readers can access subscribed articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        articles = (
            Article.objects.filter(
                approved=True,
                publisher__in=request.user.subscribed_publishers.all(),
            )
            | Article.objects.filter(
                approved=True,
                author__in=request.user.subscribed_journalists.all(),
            )
        )

        articles = articles.distinct().order_by("-created_at")
        return Response(ArticleSerializer(articles, many=True).data)


class JournalistSubscriptionAPIView(APIView):
    """Allow readers to subscribe to or unsubscribe from journalists."""

    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """Handle a journalist subscription request."""
        if get_user_role(request.user) != "reader":
            return Response(
                {"detail": "Only readers can subscribe to journalists."},
                status=status.HTTP_403_FORBIDDEN,
            )

        journalist = User.objects.filter(
            id=user_id,
            role__iexact="Journalist",
        ).first()

        if journalist is None:
            return Response(
                {"detail": "Journalist not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        request.user.subscribed_journalists.add(journalist)
        return Response(
            {"detail": "Successfully subscribed to journalist."},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, user_id):
        """Handle a journalist unsubscribe request."""
        if get_user_role(request.user) != "reader":
            return Response(
                {"detail": "Only readers can unsubscribe from journalists."},
                status=status.HTTP_403_FORBIDDEN,
            )

        journalist = User.objects.filter(
            id=user_id,
            role__iexact="Journalist",
        ).first()

        if journalist is None:
            return Response(
                {"detail": "Journalist not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        request.user.subscribed_journalists.remove(journalist)
        return Response(
            {"detail": "Successfully unsubscribed from journalist."},
            status=status.HTTP_200_OK,
        )


class PublisherSubscriptionAPIView(APIView):
    """Allow readers to subscribe to or unsubscribe from publishers."""

    permission_classes = [IsAuthenticated]

    def post(self, request, publisher_id):
        """Handle a publisher subscription request."""
        if get_user_role(request.user) != "reader":
            return Response(
                {"detail": "Only readers can subscribe to publishers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        publisher = Publisher.objects.filter(id=publisher_id).first()
        if publisher is None:
            return Response(
                {"detail": "Publisher not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        request.user.subscribed_publishers.add(publisher)
        return Response(
            {"detail": "Successfully subscribed to publisher."},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, publisher_id):
        """Handle a publisher unsubscribe request."""
        if get_user_role(request.user) != "reader":
            return Response(
                {"detail": "Only readers can unsubscribe from publishers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        publisher = Publisher.objects.filter(id=publisher_id).first()
        if publisher is None:
            return Response(
                {"detail": "Publisher not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        request.user.subscribed_publishers.remove(publisher)
        return Response(
            {"detail": "Successfully unsubscribed from publisher."},
            status=status.HTTP_200_OK,
        )


class ArticleDetailAPIView(APIView):
    """Retrieve, update or delete one article."""

    permission_classes = [IsAuthenticated]

    def get_article(self, article_id):
        """Return an article by primary key or None."""
        return Article.objects.filter(id=article_id).first()

    def get(self, request, article_id):
        """Retrieve an article for an authenticated user."""
        article = self.get_article(article_id)
        if article is None:
            return Response(
                {"detail": "Article not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not article.approved and get_user_role(request.user) == "reader":
            return Response(
                {"detail": "Article has not been approved."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(ArticleSerializer(article).data)

    def put(self, request, article_id):
        """Update an article when the user has the required role."""
        article = self.get_article(article_id)
        if article is None:
            return Response(
                {"detail": "Article not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        role = get_user_role(request.user)
        if role not in {"editor", "journalist"}:
            return Response(
                {"detail": "Only editors and journalists can update articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if role == "journalist" and article.author_id != request.user.id:
            return Response(
                {"detail": "Journalists can only update their own articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ArticleSerializer(
            article,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            updated = serializer.save()
            if role == "journalist":
                updated.approved = False
                updated.save(update_fields=["approved"])
            return Response(ArticleSerializer(updated).data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, article_id):
        """Delete an article when the user has the required role."""
        article = self.get_article(article_id)
        if article is None:
            return Response(
                {"detail": "Article not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        role = get_user_role(request.user)
        if role not in {"editor", "journalist"}:
            return Response(
                {"detail": "Only editors and journalists can delete articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if role == "journalist" and article.author_id != request.user.id:
            return Response(
                {"detail": "Journalists can only delete their own articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NewsletterListCreateAPIView(APIView):
    """List newsletters or create one as a journalist/editor."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return available newsletters."""
        newsletters = Newsletter.objects.all().order_by("-created_at")
        return Response(NewsletterSerializer(newsletters, many=True).data)

    def post(self, request):
        """Create a newsletter when the requester is a journalist or editor."""
        if get_user_role(request.user) not in {"journalist", "editor"}:
            return Response(
                {"detail": "Only journalists and editors can create newsletters."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = NewsletterSerializer(data=request.data)
        if serializer.is_valid():
            newsletter = serializer.save(author=request.user)
            return Response(
                NewsletterSerializer(newsletter).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class NewsletterDetailAPIView(APIView):
    """Retrieve, update or delete a newsletter."""

    permission_classes = [IsAuthenticated]

    def get_newsletter(self, newsletter_id):
        """Return a newsletter by primary key or None."""
        return Newsletter.objects.filter(id=newsletter_id).first()

    def get(self, request, newsletter_id):
        """Retrieve a newsletter for an authenticated user."""
        newsletter = self.get_newsletter(newsletter_id)
        if newsletter is None:
            return Response(
                {"detail": "Newsletter not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(NewsletterSerializer(newsletter).data)

    def put(self, request, newsletter_id):
        """Update a newsletter when the user has the required role."""
        newsletter = self.get_newsletter(newsletter_id)
        if newsletter is None:
            return Response(
                {"detail": "Newsletter not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        role = get_user_role(request.user)
        if role not in {"journalist", "editor"}:
            return Response(
                {"detail": "Only journalists and editors can update newsletters."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if role == "journalist" and newsletter.author_id != request.user.id:
            return Response(
                {"detail": "Journalists can only update their own newsletters."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = NewsletterSerializer(
            newsletter,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            return Response(NewsletterSerializer(serializer.save()).data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, newsletter_id):
        """Delete a newsletter when the user has the required role."""
        newsletter = self.get_newsletter(newsletter_id)
        if newsletter is None:
            return Response(
                {"detail": "Newsletter not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        role = get_user_role(request.user)
        if role not in {"journalist", "editor"}:
            return Response(
                {"detail": "Only journalists and editors can delete newsletters."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if role == "journalist" and newsletter.author_id != request.user.id:
            return Response(
                {"detail": "Journalists can only delete their own newsletters."},
                status=status.HTTP_403_FORBIDDEN,
            )

        newsletter.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApprovedArticleLogAPIView(APIView):
    """Receive the internal POST used to log an approved article."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Log an approval event submitted by an editor."""
        if get_user_role(request.user) != "editor":
            return Response(
                {"detail": "Only editors can log approved articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # This endpoint is an approval event log, not an article creator.
        logger.info(
            "Approved article logged: article_id=%s title=%s author=%s",
            request.data.get("article_id"),
            request.data.get("title"),
            request.data.get("author"),
        )

        return Response(
            {
                "detail": "Approved article event logged.",
                "article_id": request.data.get("article_id"),
                "title": request.data.get("title"),
                "approved": True,
            },
            status=status.HTTP_201_CREATED,
        )
