from django import forms
import re


class PhoneSearchForm(forms.Form):
    """Form for phone number search in format: COUNTRY_CODE PHONE_NUMBER"""

    query = forms.CharField(
        label="Búsqueda",
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "521 1234567890 (formato: código país + número)",
                "type": "text",
            }
        ),
    )

    def clean_query(self):
        query = self.cleaned_data["query"]

        # Split the input
        parts = query.strip().split()

        # Check if format is valid (at least 2 parts: CODE and PHONE)
        if len(parts) < 2:
            raise forms.ValidationError(
                "Formato inválido. Usa: CÓDIGO_PAÍS NÚMERO (ej: 521 5535664668)"
            )

        # Extract country code and phone
        country_code = parts[0]
        phone = "".join(parts[1:])  # Join remaining parts in case there are spaces

        # Validate country code
        country_code_clean = re.sub(r"[^0-9]", "", country_code)
        if not (1 <= int(country_code_clean) <= 999):
            raise forms.ValidationError("Código de país inválido (1-999).")

        # Validate phone number
        phone_clean = re.sub(r"[^0-9]", "", phone)
        if len(phone_clean) < 6:
            raise forms.ValidationError(
                "Número telefónico demasiado corto (mínimo 6 dígitos)."
            )

        # Store parsed values for retrieval
        self.country_code = country_code_clean
        self.phone = phone_clean

        return query
