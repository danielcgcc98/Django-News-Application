"""Forms used by the Django news application."""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Article, Newsletter, Publisher, User


class RegistrationForm(UserCreationForm):
    """Form used to register readers, journalists, and editors."""

    role = forms.ChoiceField(
        label="Role",
        choices=User.ROLE_CHOICES,
        initial="Reader",
    )

    class Meta:
        """Configure fields displayed by the registration form."""

        model = User
        fields = (
            "username",
            "email",
            "role",
            "password1",
            "password2",
        )


class ArticleForm(forms.ModelForm):
    """Form used by journalists and editors to create or edit articles."""

    approve_independent = forms.BooleanField(
        required=False,
        label="Publish immediately as an independent article",
        help_text=(
            "Use this only when no publisher is selected. Publisher articles "
            "remain pending editor approval."
        ),
    )

    class Meta:
        """Configure article form fields and labels."""

        model = Article
        fields = ("title", "content", "publisher")
        labels = {
            "title": "Article title",
            "content": "Article content",
            "publisher": "Publisher (optional)",
        }
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 12, "placeholder": "Write your article here..."}
            ),
        }

    def __init__(self, *args, **kwargs):
        """Add a clear independent-article option to the publisher choices."""
        super().__init__(*args, **kwargs)
        self.fields["publisher"].required = False
        self.fields["publisher"].empty_label = "Independent article (no publisher)"
        if self.instance.pk and self.instance.publisher_id is None:
            self.fields["approve_independent"].initial = self.instance.approved

    def clean(self):
        """Prevent an article from being both publisher-linked and immediately approved."""
        cleaned_data = super().clean()
        publisher = cleaned_data.get("publisher")
        approve_independent = cleaned_data.get("approve_independent")
        if publisher and approve_independent:
            raise forms.ValidationError(
                "An article can only be published immediately when it is independent."
            )
        return cleaned_data


class NewsletterForm(forms.ModelForm):
    """Form used by journalists and editors to manage newsletters."""

    class Meta:
        """Configure newsletter fields and presentation."""

        model = Newsletter
        fields = ("title", "description", "articles")
        labels = {
            "title": "Newsletter title",
            "description": "Newsletter description",
            "articles": "Approved articles",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 8}),
            "articles": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        """Limit newsletter article choices to approved articles only."""
        super().__init__(*args, **kwargs)
        self.fields["articles"].queryset = (
            Article.objects
            .filter(approved=True)
            .select_related("author", "publisher")
            .order_by("-created_at")
        )


class PublisherForm(forms.ModelForm):
    """Form used by editors to create and manage publishers and their staff."""

    class Meta:
        """Configure publisher fields and assignment controls."""

        model = Publisher
        fields = ("name", "editors", "journalists")
        labels = {
            "name": "Publisher name",
            "editors": "Assigned editors",
            "journalists": "Assigned journalists",
        }
        widgets = {
            "editors": forms.CheckboxSelectMultiple(),
            "journalists": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        """Restrict assignment choices to users with the matching role."""
        super().__init__(*args, **kwargs)
        self.fields["editors"].queryset = User.objects.filter(
            role__iexact="Editor"
        ).order_by("username")
        self.fields["journalists"].queryset = User.objects.filter(
            role__iexact="Journalist"
        ).order_by("username")
