"""Website views for the Django News application."""

import logging

import requests
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework.authtoken.models import Token

from .forms import ArticleForm, NewsletterForm, PublisherForm, RegistrationForm
from .models import Article, Newsletter, Publisher

logger = logging.getLogger(__name__)
User = get_user_model()


def role_name(user):
    """Return the authenticated user's role in lowercase form."""
    return getattr(user, "role", "").lower()


def is_editor(user):
    """Return True when the user has Editor role membership."""
    return user.is_authenticated and (
        role_name(user) == "editor"
        or user.groups.filter(name="Editor").exists()
    )


def is_journalist(user):
    """Return True when the user has Journalist role membership."""
    return user.is_authenticated and (
        role_name(user) == "journalist"
        or user.groups.filter(name="Journalist").exists()
    )


def is_reader(user):
    """Return True when the user has Reader role membership."""
    return user.is_authenticated and (
        role_name(user) == "reader"
        or user.groups.filter(name="Reader").exists()
    )


@login_required
def article_list(request):
    """Display approved articles and role-specific management dashboards."""
    articles = Article.objects.filter(approved=True).order_by("-created_at")
    my_articles = Article.objects.none()
    pending_articles = Article.objects.none()
    all_articles_for_editor = Article.objects.none()

    if is_journalist(request.user):
        my_articles = Article.objects.filter(author=request.user).order_by("-created_at")

    if is_editor(request.user):
        pending_articles = Article.objects.filter(approved=False).order_by("-created_at")
        all_articles_for_editor = Article.objects.all().order_by("-created_at")

    return render(
        request,
        "news/article_list.html",
        {
            "articles": articles,
            "my_articles": my_articles,
            "pending_articles": pending_articles,
            "all_articles_for_editor": all_articles_for_editor,
        },
    )


def register(request):
    """Create an account and sign the new user in."""
    if request.user.is_authenticated:
        return redirect("article_list")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("article_list")
    else:
        form = RegistrationForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
def article_detail(request, article_id):
    """Display an article when the current user is permitted to see it."""
    article = get_object_or_404(Article, id=article_id)
    if article.approved:
        return render(request, "news/article_detail.html", {"article": article})
    if is_journalist(request.user) and article.author == request.user:
        return render(request, "news/article_detail.html", {"article": article})
    if is_editor(request.user):
        return render(request, "news/article_detail.html", {"article": article})
    return JsonResponse({"error": "This article has not been approved."}, status=403)


@login_required
def article_create(request):
    """Allow journalists to create new publisher-linked or independent articles."""
    if not is_journalist(request.user):
        return JsonResponse({"error": "Only journalists can create articles."}, status=403)

    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.approved = (
                form.cleaned_data["approve_independent"]
                and article.publisher is None
            )
            article.save()
            return redirect("article_list")
    else:
        form = ArticleForm()

    return render(request, "news/article_form.html", {"form": form, "mode": "create"})


@login_required
def article_edit(request, article_id):
    """Allow journalists to edit their own articles and editors to edit any article."""
    if not is_journalist(request.user) and not is_editor(request.user):
        return JsonResponse(
            {"error": "Only journalists and editors can edit articles."}, status=403
        )

    if is_journalist(request.user) and not is_editor(request.user):
        article = get_object_or_404(Article, id=article_id, author=request.user)
    else:
        article = get_object_or_404(Article, id=article_id)

    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            article = form.save(commit=False)
            if is_journalist(request.user) and not is_editor(request.user):
                article.approved = (
                    form.cleaned_data["approve_independent"]
                    and article.publisher is None
                )
            article.save()
            return redirect("article_list")
    else:
        form = ArticleForm(instance=article)

    return render(
        request,
        "news/article_form.html",
        {"form": form, "article": article, "mode": "edit"},
    )


@login_required
def article_delete(request, article_id):
    """Allow journalists to delete their own articles and editors to delete any article."""
    if not is_journalist(request.user) and not is_editor(request.user):
        return JsonResponse(
            {"error": "Only journalists and editors can delete articles."}, status=403
        )

    if is_journalist(request.user) and not is_editor(request.user):
        article = get_object_or_404(Article, id=article_id, author=request.user)
    else:
        article = get_object_or_404(Article, id=article_id)

    if request.method == "POST":
        article.delete()
        return redirect("article_list")

    return render(request, "news/article_confirm_delete.html", {"article": article})


@login_required
def approve_article(request, article_id):
    """Approve an article, notify subscribers, and record the approval event."""
    if not is_editor(request.user):
        return JsonResponse({"error": "Only editors can approve articles."}, status=403)
    if request.method != "POST":
        return JsonResponse({"error": "Use POST to approve an article."}, status=405)

    article = get_object_or_404(Article, id=article_id)
    if article.approved:
        return redirect("article_list")

    article.approved = True
    article.save(update_fields=["approved"])

    subscriber_emails = set()
    for subscriber in article.author.reader_subscribers.all():
        if subscriber.email:
            subscriber_emails.add(subscriber.email)
    if article.publisher:
        for subscriber in article.publisher.subscribed_readers.all():
            if subscriber.email:
                subscriber_emails.add(subscriber.email)

    if subscriber_emails:
        send_mail(
            subject=f"Approved article: {article.title}",
            message=(
                "The following article has been approved:\n\n"
                f"Title: {article.title}\n\n{article.content}"
            ),
            from_email=None,
            recipient_list=list(subscriber_emails),
            fail_silently=True,
        )

    token, _ = Token.objects.get_or_create(user=request.user)
    approval_url = request.build_absolute_uri("/api/approved/")
    try:
        response = requests.post(
            approval_url,
            json={
                "article_id": article.id,
                "title": article.title,
                "author": article.author.username,
                "publisher": article.publisher.name if article.publisher else None,
                "approved": article.approved,
            },
            headers={"Authorization": f"Token {token.key}"},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Approval API logging failed: %s", exc)

    return redirect("article_list")


@login_required
def newsletter_list(request):
    """Display newsletters and management controls to authenticated users."""
    newsletters = (
        Newsletter.objects.select_related("author")
        .prefetch_related("articles")
        .order_by("-created_at")
    )
    return render(request, "news/newsletter_list.html", {"newsletters": newsletters})


@login_required
def newsletter_detail(request, newsletter_id):
    """Display one newsletter and controls for users allowed to manage it."""
    newsletter = get_object_or_404(
        Newsletter.objects.prefetch_related("articles"), id=newsletter_id
    )
    can_manage = is_editor(request.user) or (
        is_journalist(request.user) and newsletter.author_id == request.user.id
    )
    return render(
        request,
        "news/newsletter_detail.html",
        {"newsletter": newsletter, "can_manage": can_manage},
    )


@login_required
def newsletter_create(request):
    """Allow journalists and editors to create newsletters from approved articles."""
    if not is_journalist(request.user) and not is_editor(request.user):
        return JsonResponse(
            {"error": "Only journalists and editors can create newsletters."}, status=403
        )
    form = NewsletterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        newsletter = form.save(commit=False)
        newsletter.author = request.user
        newsletter.save()
        form.save_m2m()
        return redirect("newsletter_list")
    return render(request, "news/newsletter_form.html", {"form": form, "mode": "create"})


@login_required
def newsletter_edit(request, newsletter_id):
    """Allow journalists to edit their own newsletters and editors to edit any newsletter."""
    if not is_journalist(request.user) and not is_editor(request.user):
        return JsonResponse(
            {"error": "Only journalists and editors can edit newsletters."}, status=403
        )
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    if is_journalist(request.user) and not is_editor(request.user):
        if newsletter.author_id != request.user.id:
            return JsonResponse({"error": "You can only edit your own newsletters."}, status=403)
    form = NewsletterForm(request.POST or None, instance=newsletter)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("newsletter_detail", newsletter_id=newsletter.id)
    return render(
        request,
        "news/newsletter_form.html",
        {"form": form, "newsletter": newsletter, "mode": "edit"},
    )


@login_required
def newsletter_delete(request, newsletter_id):
    """Allow journalists to delete their own newsletters and editors to delete any newsletter."""
    if not is_journalist(request.user) and not is_editor(request.user):
        return JsonResponse(
            {"error": "Only journalists and editors can delete newsletters."}, status=403
        )
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    if is_journalist(request.user) and not is_editor(request.user):
        if newsletter.author_id != request.user.id:
            return JsonResponse({"error": "You can only delete your own newsletters."}, status=403)
    if request.method == "POST":
        newsletter.delete()
        return redirect("newsletter_list")
    return render(
        request,
        "news/newsletter_confirm_delete.html",
        {"newsletter": newsletter},
    )


@login_required
def publisher_list(request):
    """Display all publishers and their assigned journalists and editors."""
    publishers = Publisher.objects.prefetch_related("editors", "journalists").order_by("name")
    return render(request, "news/publisher_list.html", {"publishers": publishers})


@login_required
def publisher_create(request):
    """Allow editors to create publishers and assign their staff."""
    if not is_editor(request.user):
        return JsonResponse({"error": "Only editors can create publishers."}, status=403)
    form = PublisherForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        publisher = form.save()
        publisher.editors.add(request.user)
        return redirect("publisher_list")
    return render(request, "news/publisher_form.html", {"form": form, "mode": "create"})


@login_required
def publisher_edit(request, publisher_id):
    """Allow editors to edit a publisher and manage assigned staff."""
    if not is_editor(request.user):
        return JsonResponse({"error": "Only editors can edit publishers."}, status=403)
    publisher = get_object_or_404(Publisher, id=publisher_id)
    form = PublisherForm(request.POST or None, instance=publisher)
    if request.method == "POST" and form.is_valid():
        publisher = form.save()
        publisher.editors.add(request.user)
        return redirect("publisher_list")
    return render(
        request,
        "news/publisher_form.html",
        {"form": form, "publisher": publisher, "mode": "edit"},
    )


@login_required
def publisher_delete(request, publisher_id):
    """Allow editors to delete publishers after confirmation."""
    if not is_editor(request.user):
        return JsonResponse({"error": "Only editors can delete publishers."}, status=403)
    publisher = get_object_or_404(Publisher, id=publisher_id)
    if request.method == "POST":
        publisher.delete()
        return redirect("publisher_list")
    return render(request, "news/publisher_confirm_delete.html", {"publisher": publisher})


@login_required
def subscription_manager(request):
    """Let readers manage journalist and publisher subscriptions through the website."""
    if not is_reader(request.user):
        return JsonResponse({"error": "Only readers can manage subscriptions."}, status=403)

    if request.method == "POST":
        subscription_type = request.POST.get("subscription_type")
        object_id = request.POST.get("object_id")
        action = request.POST.get("action")

        if subscription_type == "journalist":
            target = get_object_or_404(User, id=object_id, role__iexact="Journalist")
            relation = request.user.subscribed_journalists
        elif subscription_type == "publisher":
            target = get_object_or_404(Publisher, id=object_id)
            relation = request.user.subscribed_publishers
        else:
            return JsonResponse({"error": "Invalid subscription type."}, status=400)

        if action == "subscribe":
            relation.add(target)
        elif action == "unsubscribe":
            relation.remove(target)
        else:
            return JsonResponse({"error": "Invalid subscription action."}, status=400)
        return redirect("subscription_manager")

    journalists = User.objects.filter(role__iexact="Journalist").order_by("username")
    publishers = Publisher.objects.order_by("name")
    return render(
        request,
        "news/subscriptions.html",
        {
            "journalists": journalists,
            "publishers": publishers,
            "subscribed_journalists": set(request.user.subscribed_journalists.values_list("id", flat=True)),
            "subscribed_publishers": set(request.user.subscribed_publishers.values_list("id", flat=True)),
        },
    )
