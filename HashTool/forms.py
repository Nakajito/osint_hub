from django import forms

ALGO_CHOICES = [
    ("md5", "md5"),
    ("sha1", "sha1"),
    ("sha224", "sha224"),
    ("sha256", "sha256"),
    ("sha384", "sha384"),
    ("sha512", "sha512"),
]


class GenerateForm(forms.Form):
    text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}), required=False, label="Texto"
    )
    file = forms.FileField(required=False, label="Archivo")
    algorithm = forms.ChoiceField(
        choices=ALGO_CHOICES, initial="sha256", label="Algoritmo"
    )


class VerifyForm(forms.Form):
    text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}), required=False, label="Texto"
    )
    file = forms.FileField(required=False, label="Archivo")
    algorithm = forms.ChoiceField(
        choices=ALGO_CHOICES, initial="sha256", label="Algoritmo"
    )
    hash_value = forms.CharField(required=True, label="Hash a verificar")
