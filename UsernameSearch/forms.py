from django import forms
import re


class UsernameSearchForm(forms.Form):
    """Form to accept a username for Sherlock searches."""

    username = forms.CharField(
        label="Nombre de usuario",
        max_length=64,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "ej: user (sin @)",
                "type": "text",
            }
        ),
    )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        # Remove leading @ if provided
        if username.startswith("@"):
            username = username[1:]

        # Basic validation: allow letters, numbers, dots, underscores and hyphens
        if not re.match(r"^[A-Za-z0-9_.-]{2,64}$", username):
            raise forms.ValidationError(
                "Nombre de usuario inválido. Usa letras, números, '_', '-' o '.' (2-64 caracteres)."
            )

        self.username = username
        return username
