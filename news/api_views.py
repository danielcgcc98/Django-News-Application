from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Article, User, Publisher, Newsletter
from .serializers import (
    ArticleSerializer,
    NewsletterSerializer,
)


def get_user_role(user):
    """
    Return the user's role in lowercase.
    """
    return getattr(user, "role", "").lower()


# ---------------------------------------------------------
# ARTICLE LIST / CREATE
# ---------------------------------------------------------

class ArticleListCreateAPIView(APIView):
    """
    GET  /api/articles/
    POST /api/articles/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return all approved articles.
        """

        articles = Article.objects.filter(
            approved=True
        ).order_by("-created_at")

        serializer = ArticleSerializer(
            articles,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):
        """
        Create an article.

        Only journalists can create articles.
        """

        if get_user_role(request.user) != "journalist":
            return Response(
                {
                    "detail": "Only journalists can create articles."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ArticleSerializer(
            data=request.data
        )

        if serializer.is_valid():
            article = serializer.save(
                author=request.user
            )

            return Response(
                ArticleSerializer(article).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ---------------------------------------------------------
# SUBSCRIBED ARTICLES
# ---------------------------------------------------------

class SubscribedArticlesAPIView(APIView):
    """
    GET /api/articles/subscribed/

    Return approved articles from the publishers
    and journalists that the reader follows.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        if get_user_role(user) != "reader":
            return Response(
                {
                    "detail": (
                        "Only readers can access subscribed articles."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        subscribed_publishers = (
            user.subscribed_publishers.all()
        )

        subscribed_journalists = (
            user.subscribed_journalists.all()
        )

        articles = Article.objects.filter(
            approved=True
        ).filter(
            publisher__in=subscribed_publishers
        ) | Article.objects.filter(
            approved=True,
            author__in=subscribed_journalists
        )

        articles = articles.distinct().order_by(
            "-created_at"
        )

        serializer = ArticleSerializer(
            articles,
            many=True
        )

        return Response(serializer.data)


# ---------------------------------------------------------
# JOURNALIST SUBSCRIPTION
# ---------------------------------------------------------

class JournalistSubscriptionAPIView(APIView):
    """
    POST   /api/subscribe/journalist/<user_id>/
    DELETE /api/subscribe/journalist/<user_id>/

    Readers can subscribe to or unsubscribe from journalists.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """
        Subscribe the reader to a journalist.
        """

        if get_user_role(request.user) != "reader":
            return Response(
                {
                    "detail": (
                        "Only readers can subscribe to journalists."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        journalist = User.objects.filter(
            id=user_id,
            role__iexact="Journalist"
        ).first()

        if journalist is None:
            return Response(
                {
                    "detail": "Journalist not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        request.user.subscribed_journalists.add(
            journalist
        )

        return Response(
            {
                "detail": (
                    "Successfully subscribed to journalist."
                )
            },
            status=status.HTTP_200_OK
        )

    def delete(self, request, user_id):
        """
        Unsubscribe the reader from a journalist.
        """

        if get_user_role(request.user) != "reader":
            return Response(
                {
                    "detail": (
                        "Only readers can unsubscribe from journalists."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        journalist = User.objects.filter(
            id=user_id,
            role__iexact="Journalist"
        ).first()

        if journalist is None:
            return Response(
                {
                    "detail": "Journalist not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        request.user.subscribed_journalists.remove(
            journalist
        )

        return Response(
            {
                "detail": (
                    "Successfully unsubscribed from journalist."
                )
            },
            status=status.HTTP_200_OK
        )


# ---------------------------------------------------------
# PUBLISHER SUBSCRIPTION
# ---------------------------------------------------------

class PublisherSubscriptionAPIView(APIView):
    """
    POST   /api/subscribe/publisher/<publisher_id>/
    DELETE /api/subscribe/publisher/<publisher_id>/

    Readers can subscribe to or unsubscribe from publishers.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, publisher_id):
        """
        Subscribe the reader to a publisher.
        """

        if get_user_role(request.user) != "reader":
            return Response(
                {
                    "detail": (
                        "Only readers can subscribe to publishers."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        publisher = Publisher.objects.filter(
            id=publisher_id
        ).first()

        if publisher is None:
            return Response(
                {
                    "detail": "Publisher not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        request.user.subscribed_publishers.add(
            publisher
        )

        return Response(
            {
                "detail": (
                    "Successfully subscribed to publisher."
                )
            },
            status=status.HTTP_200_OK
        )

    def delete(self, request, publisher_id):
        """
        Unsubscribe the reader from a publisher.
        """

        if get_user_role(request.user) != "reader":
            return Response(
                {
                    "detail": (
                        "Only readers can unsubscribe from publishers."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        publisher = Publisher.objects.filter(
            id=publisher_id
        ).first()

        if publisher is None:
            return Response(
                {
                    "detail": "Publisher not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        request.user.subscribed_publishers.remove(
            publisher
        )

        return Response(
            {
                "detail": (
                    "Successfully unsubscribed from publisher."
                )
            },
            status=status.HTTP_200_OK
        )


# ---------------------------------------------------------
# NEWSLETTER LIST / CREATE
# ---------------------------------------------------------

class NewsletterListCreateAPIView(APIView):
    """
    GET  /api/newsletters/
    POST /api/newsletters/

    Readers can view newsletters.
    Journalists and editors can create newsletters.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return all newsletters.
        """

        newsletters = Newsletter.objects.all().order_by(
            "-created_at"
        )

        serializer = NewsletterSerializer(
            newsletters,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):
        """
        Create a newsletter.

        Journalists and editors can create newsletters.
        """

        role = get_user_role(request.user)

        if role not in ["journalist", "editor"]:
            return Response(
                {
                    "detail": (
                        "Only journalists and editors can "
                        "create newsletters."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = NewsletterSerializer(
            data=request.data
        )

        if serializer.is_valid():
            newsletter = serializer.save(
                author=request.user
            )

            return Response(
                NewsletterSerializer(newsletter).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ---------------------------------------------------------
# NEWSLETTER DETAIL / UPDATE / DELETE
# ---------------------------------------------------------

class NewsletterDetailAPIView(APIView):
    """
    GET    /api/newsletters/<id>/
    PUT    /api/newsletters/<id>/
    DELETE /api/newsletters/<id>/

    Readers can view newsletters.
    Journalists and editors can update/delete newsletters.
    """

    permission_classes = [IsAuthenticated]

    def get_newsletter(self, newsletter_id):
        """
        Return a newsletter or None if it does not exist.
        """

        try:
            return Newsletter.objects.get(
                id=newsletter_id
            )
        except Newsletter.DoesNotExist:
            return None

    def get(self, request, newsletter_id):
        """
        Return one newsletter.
        """

        newsletter = self.get_newsletter(
            newsletter_id
        )

        if newsletter is None:
            return Response(
                {
                    "detail": "Newsletter not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = NewsletterSerializer(
            newsletter
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def put(self, request, newsletter_id):
        """
        Update a newsletter.

        Only journalists and editors can update newsletters.
        """

        newsletter = self.get_newsletter(
            newsletter_id
        )

        if newsletter is None:
            return Response(
                {
                    "detail": "Newsletter not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        role = get_user_role(request.user)

        if role not in ["journalist", "editor"]:
            return Response(
                {
                    "detail": (
                        "Only journalists and editors can "
                        "update newsletters."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = NewsletterSerializer(
            newsletter,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, newsletter_id):
        """
        Delete a newsletter.

        Only journalists and editors can delete newsletters.
        """

        newsletter = self.get_newsletter(
            newsletter_id
        )

        if newsletter is None:
            return Response(
                {
                    "detail": "Newsletter not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        role = get_user_role(request.user)

        if role not in ["journalist", "editor"]:
            return Response(
                {
                    "detail": (
                        "Only journalists and editors can "
                        "delete newsletters."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        newsletter.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


# ---------------------------------------------------------
# SINGLE ARTICLE / UPDATE / DELETE
# ---------------------------------------------------------

class ArticleDetailAPIView(APIView):
    """
    GET    /api/articles/<id>/
    PUT    /api/articles/<id>/
    DELETE /api/articles/<id>/
    """

    permission_classes = [IsAuthenticated]

    def get_article(self, article_id):
        """
        Return an article or None if it does not exist.
        """

        try:
            return Article.objects.get(
                id=article_id
            )
        except Article.DoesNotExist:
            return None

    def get(self, request, article_id):
        """
        Return one article.
        """

        article = self.get_article(article_id)

        if article is None:
            return Response(
                {
                    "detail": "Article not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Readers can only view approved articles.
        if not article.approved:
            if get_user_role(request.user) == "reader":
                return Response(
                    {
                        "detail": (
                            "Article has not been approved."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = ArticleSerializer(
            article
        )

        return Response(
            serializer.data
        )

    def put(self, request, article_id):
        """
        Update an article.

        Only editors and journalists can update articles.
        """

        article = self.get_article(article_id)

        if article is None:
            return Response(
                {
                    "detail": "Article not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        role = get_user_role(request.user)

        if role not in [
            "editor",
            "journalist"
        ]:
            return Response(
                {
                    "detail": (
                        "Only editors and journalists "
                        "can update articles."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ArticleSerializer(
            article,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, article_id):
        """
        Delete an article.

        Only editors and journalists can delete articles.
        """

        article = self.get_article(article_id)

        if article is None:
            return Response(
                {
                    "detail": "Article not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        role = get_user_role(request.user)

        if role not in [
            "editor",
            "journalist"
        ]:
            return Response(
                {
                    "detail": (
                        "Only editors and journalists "
                        "can delete articles."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        article.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )