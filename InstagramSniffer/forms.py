from django import forms
import re


class InstagramUsernameForm(forms.Form):
    username = forms.CharField(
        label="Nombre de usuario de Instagram",
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "ej: usuario123 (sin @)",
                "type": "text",
            }
        ),
    )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if username.startswith("@"):
            username = username[1:]

        if not re.match(r"^[A-Za-z0-9_.]{1,30}$", username):
            raise forms.ValidationError(
                "Nombre de usuario inválido. Usa letras, números, '_' o '.' (1-30 caracteres)."
            )
        return username


class InstagramPostUrlForm(forms.Form):
    post_url = forms.URLField(
        label="URL de publicación de Instagram",
        max_length=200,
        required=True,
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "https://www.instagram.com/usuario/p/ABC123/",
                "type": "url",
            }
        ),
    )

    def clean_post_url(self):
        url = self.cleaned_data.get("post_url", "").strip().rstrip("/")
        if not re.search(r"instagram\.com/.+/(p|reel)/.+", url):
            raise forms.ValidationError(
                "URL inválida. Debe ser del formato: https://www.instagram.com/usuario/p/CODIGO/ o .../reel/CODIGO/"
            )
        return url
