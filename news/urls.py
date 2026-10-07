"""URL routes for the news website and REST API."""

from django.urls import path

from . import api_views, views


urlpatterns = [
    path("accounts/register/", views.register, name="register"),
    path("", views.article_list, name="article_list"),
    path(
        "article/<int:article_id>/",
        views.article_detail,
        name="article_detail",
    ),
    path("article/create/", views.article_create, name="article_create"),
    path(
        "article/<int:article_id>/edit/",
        views.article_edit,
        name="article_edit",
    ),
    path(
        "article/<int:article_id>/delete/",
        views.article_delete,
        name="article_delete",
    ),
    path(
        "article/<int:article_id>/approve/",
        views.approve_article,
        name="approve_article",
    ),

    path("newsletters/", views.newsletter_list, name="newsletter_list"),

    path("publishers/", views.publisher_list, name="publisher_list"),
    path("publisher/create/", views.publisher_create, name="publisher_create"),
    path(
        "publisher/<int:publisher_id>/edit/",
        views.publisher_edit,
        name="publisher_edit",
    ),
    path(
        "publisher/<int:publisher_id>/delete/",
        views.publisher_delete,
        name="publisher_delete",
    ),
    path(
        "subscriptions/",
        views.subscription_manager,
        name="subscription_manager",
    ),

    path(
        "newsletter/<int:newsletter_id>/",
        views.newsletter_detail,
        name="newsletter_detail",
    ),
    path(
        "newsletter/create/",
        views.newsletter_create,
        name="newsletter_create",
    ),
    path(
        "newsletter/<int:newsletter_id>/edit/",
        views.newsletter_edit,
        name="newsletter_edit",
    ),
    path(
        "newsletter/<int:newsletter_id>/delete/",
        views.newsletter_delete,
        name="newsletter_delete",
    ),

    path(
        "api/articles/",
        api_views.ArticleListCreateAPIView.as_view(),
        name="api_articles",
    ),
    path(
        "api/articles/subscribed/",
        api_views.SubscribedArticlesAPIView.as_view(),
        name="api_subscribed_articles",
    ),
    path(
        "api/articles/<int:article_id>/",
        api_views.ArticleDetailAPIView.as_view(),
        name="api_article_detail",
    ),
    path(
        "api/subscribe/journalist/<int:user_id>/",
        api_views.JournalistSubscriptionAPIView.as_view(),
        name="api_subscribe_journalist",
    ),
    path(
        "api/subscribe/publisher/<int:publisher_id>/",
        api_views.PublisherSubscriptionAPIView.as_view(),
        name="api_subscribe_publisher",
    ),
    path(
        "api/newsletters/",
        api_views.NewsletterListCreateAPIView.as_view(),
        name="api_newsletters",
    ),
    path(
        "api/newsletters/<int:newsletter_id>/",
        api_views.NewsletterDetailAPIView.as_view(),
        name="api_newsletter_detail",
    ),
    path(
        "api/approved/",
        api_views.ApprovedArticleLogAPIView.as_view(),
        name="api_approved",
    ),
]
