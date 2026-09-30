from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RegistrationForm
from .models import Article, Publisher


# ---------------------------------------------------------
# ROLE CHECKING
# ---------------------------------------------------------

def is_editor(user):
    """Return True if the user is an editor."""
    return (
        user.is_authenticated
        and (
            getattr(user, "role", "").lower() == "editor"
            or user.groups.filter(name="Editor").exists()
        )
    )


def is_journalist(user):
    """Return True if the user is a journalist."""
    return (
        user.is_authenticated
        and (
            getattr(user, "role", "").lower() == "journalist"
            or user.groups.filter(name="Journalist").exists()
        )
    )


def is_reader(user):
    """Return True if the user is a reader."""
    return (
        user.is_authenticated
        and (
            getattr(user, "role", "").lower() == "reader"
            or user.groups.filter(name="Reader").exists()
        )
    )


# ---------------------------------------------------------
# ARTICLE LIST
# ---------------------------------------------------------

@login_required
def article_list(request):
    """Display approved articles and a journalist's own articles."""

    articles = Article.objects.filter(
        approved=True
    ).order_by("-created_at")

    my_articles = Article.objects.none()

    if is_journalist(request.user):
        my_articles = Article.objects.filter(
            author=request.user
        ).order_by("-created_at")

    pending_articles = Article.objects.none()
    if is_editor(request.user):
        pending_articles = Article.objects.filter(
            approved=False
        ).order_by("-created_at")

    return render(
        request,
        "news/article_list.html",
        {
            "articles": articles,
            "my_articles": my_articles,
            "pending_articles": pending_articles,
        },
    )


# ---------------------------------------------------------
# REGISTRATION
# ---------------------------------------------------------

def register(request):
    """Create a user account and sign the new user in."""

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


# ---------------------------------------------------------
# ARTICLE DETAIL
# ---------------------------------------------------------

@login_required
def article_detail(request, article_id):
    """Display an approved article or the journalist's own article."""

    article = get_object_or_404(
        Article,
        id=article_id,
    )

    # Approved articles can be viewed by logged-in users.
    if article.approved:
        return render(
            request,
            "news/article_detail.html",
            {"article": article},
        )

    # A journalist can view their own pending article.
    if is_journalist(request.user) and article.author == request.user:
        return render(
            request,
            "news/article_detail.html",
            {"article": article},
        )

    return JsonResponse(
        {
            "error": "This article has not been approved."
        },
        status=403,
    )


# ---------------------------------------------------------
# JOURNALIST - CREATE ARTICLE
# ---------------------------------------------------------

@login_required
def article_create(request):
    """Allow a journalist to create an article."""

    if not is_journalist(request.user):
        return JsonResponse(
            {
                "error": "Only journalists can create articles."
            },
            status=403,
        )

    publishers = Publisher.objects.all()

    if request.method == "POST":

        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        publisher_id = request.POST.get("publisher")

        if not title or not content:
            return render(
                request,
                "news/article_form.html",
                {
                    "error": "Title and content are required.",
                    "publishers": publishers,
                },
            )

        publisher = None

        if publisher_id:
            publisher = get_object_or_404(
                Publisher,
                id=publisher_id,
            )

        Article.objects.create(
            title=title,
            content=content,
            author=request.user,
            publisher=publisher,
            approved=False,
        )

        return redirect("article_list")

    return render(
        request,
        "news/article_form.html",
        {
            "publishers": publishers,
        },
    )


# ---------------------------------------------------------
# JOURNALIST - EDIT ARTICLE
# ---------------------------------------------------------

@login_required
def article_edit(request, article_id):
    """Allow a journalist to edit their own article."""

    if not is_journalist(request.user):
        return JsonResponse(
            {
                "error": "Only journalists can edit articles."
            },
            status=403,
        )

    article = get_object_or_404(
        Article,
        id=article_id,
        author=request.user,
    )

    publishers = Publisher.objects.all()

    if request.method == "POST":

        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        publisher_id = request.POST.get("publisher")

        if not title or not content:
            return render(
                request,
                "news/article_form.html",
                {
                    "article": article,
                    "error": "Title and content are required.",
                    "publishers": publishers,
                },
            )

        article.title = title
        article.content = content

        if publisher_id:
            article.publisher = get_object_or_404(
                Publisher,
                id=publisher_id,
            )
        else:
            article.publisher = None

        # Editing sends the article back for approval.
        article.approved = False

        article.save()

        return redirect("article_list")

    return render(
        request,
        "news/article_form.html",
        {
            "article": article,
            "publishers": publishers,
        },
    )


# ---------------------------------------------------------
# JOURNALIST - DELETE ARTICLE
# ---------------------------------------------------------

@login_required
def article_delete(request, article_id):
    """Allow a journalist to delete their own article."""

    if not is_journalist(request.user):
        return JsonResponse(
            {
                "error": "Only journalists can delete articles."
            },
            status=403,
        )

    article = get_object_or_404(
        Article,
        id=article_id,
        author=request.user,
    )

    if request.method == "POST":
        article.delete()
        return redirect("article_list")

    return render(
        request,
        "news/article_confirm_delete.html",
        {
            "article": article,
        },
    )


# ---------------------------------------------------------
# APPROVE ARTICLE
# ---------------------------------------------------------

@login_required
def approve_article(request, article_id):
    """
    Allow an editor to approve an article.

    Once approved, email subscribers to the journalist
    and publisher.
    """

    if not is_editor(request.user):
        return JsonResponse(
            {
                "error": "Only editors can approve articles."
            },
            status=403,
        )

    if request.method != "POST":
        return JsonResponse(
            {"error": "Use POST to approve an article."},
            status=405,
        )

    article = get_object_or_404(
        Article,
        id=article_id,
    )

    article.approved = True
    article.save()

    subscriber_emails = set()

    # -----------------------------------------------------
    # Subscribers to the journalist
    # -----------------------------------------------------

    journalist_subscribers = (
        article.author.reader_subscribers.all()
    )

    for subscriber in journalist_subscribers:
        if subscriber.email:
            subscriber_emails.add(subscriber.email)

    # -----------------------------------------------------
    # Subscribers to the publisher
    # -----------------------------------------------------

    if article.publisher:
        publisher_subscribers = (
            article.publisher.subscribed_readers.all()
        )

        for subscriber in publisher_subscribers:
            if subscriber.email:
                subscriber_emails.add(subscriber.email)

    # -----------------------------------------------------
    # Send email notification
    # -----------------------------------------------------

    if subscriber_emails:
        send_mail(
            subject=f"Approved article: {article.title}",
            message=(
                "The following article has been approved:\n\n"
                f"Title: {article.title}\n\n"
                f"{article.content}"
            ),
            from_email=None,
            recipient_list=list(subscriber_emails),
            fail_silently=True,
        )

    return redirect("article_list")