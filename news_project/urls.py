"""Root URL configuration for the Django News project."""

from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [

    # Django admin
    path("admin/", admin.site.urls),

    # News application
    path("", include("news.urls")),

    # Django login/logout
    path("accounts/", include("django.contrib.auth.urls")),

    # API token authentication
    path("api/token/", obtain_auth_token, name="api_token"),
]