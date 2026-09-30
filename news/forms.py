"""Forms used by the news application."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

from .models import User


class RegistrationForm(UserCreationForm):
    """Form used to create a new news application user."""

    role = forms.ChoiceField(choices=User.ROLE_CHOICES, initial="Reader")

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")

    def save(self, commit=True):
        """Create the user and assign the selected role group."""
        user = super().save(commit=commit)
        if commit:
            group, _ = Group.objects.get_or_create(name=user.role)
            user.groups.add(group)
        return user
