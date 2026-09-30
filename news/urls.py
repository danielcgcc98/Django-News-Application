from django.urls import path
from . import views
from . import api_views


urlpatterns = [

    # ---------------------------------------------------------
    # NORMAL WEBSITE PAGES
    # ---------------------------------------------------------

    path(
        "accounts/register/",
        views.register,
        name="register",
    ),

    path(
        "",
        views.article_list,
        name="article_list"
    ),

    path(
        "article/<int:article_id>/",
        views.article_detail,
        name="article_detail"
    ),

    # ---------------------------------------------------------
    # JOURNALIST ARTICLE MANAGEMENT
    # ---------------------------------------------------------

    path(
        "article/create/",
        views.article_create,
        name="article_create"
    ),

    path(
        "article/<int:article_id>/edit/",
        views.article_edit,
        name="article_edit"
    ),

    path(
        "article/<int:article_id>/delete/",
        views.article_delete,
        name="article_delete"
    ),

    # ---------------------------------------------------------
    # EDITOR APPROVAL
    # ---------------------------------------------------------

    path(
        "article/<int:article_id>/approve/",
        views.approve_article,
        name="approve_article"
    ),

    # ---------------------------------------------------------
    # ARTICLE API
    # ---------------------------------------------------------

    path(
        "api/articles/",
        api_views.ArticleListCreateAPIView.as_view(),
        name="api_articles"
    ),

    path(
        "api/articles/subscribed/",
        api_views.SubscribedArticlesAPIView.as_view(),
        name="api_subscribed_articles"
    ),

    path(
        "api/articles/<int:article_id>/",
        api_views.ArticleDetailAPIView.as_view(),
        name="api_article_detail"
    ),

    # ---------------------------------------------------------
    # JOURNALIST SUBSCRIPTION API
    # ---------------------------------------------------------

    path(
        "api/subscribe/journalist/<int:user_id>/",
        api_views.JournalistSubscriptionAPIView.as_view(),
        name="api_subscribe_journalist"
    ),

    # ---------------------------------------------------------
    # PUBLISHER SUBSCRIPTION API
    # ---------------------------------------------------------

    path(
        "api/subscribe/publisher/<int:publisher_id>/",
        api_views.PublisherSubscriptionAPIView.as_view(),
        name="api_subscribe_publisher"
    ),

    # ---------------------------------------------------------
    # NEWSLETTER API
    # ---------------------------------------------------------

    path(
        "api/newsletters/",
        api_views.NewsletterListCreateAPIView.as_view(),
        name="api_newsletters"
    ),

    path(
        "api/newsletters/<int:newsletter_id>/",
        api_views.NewsletterDetailAPIView.as_view(),
        name="api_newsletter_detail"
    ),
]