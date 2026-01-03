from django import forms
from django.core.validators import validate_ipv46_address


class IPLookupForm(forms.Form):
    ip = forms.CharField(
        label="Dirección IP",
        max_length=45,
        widget=forms.TextInput(attrs={"placeholder": "8.8.8.8", "autocomplete": "off"}),
    )

    def clean_ip(self):
        ip = self.cleaned_data.get("ip")
        try:
            validate_ipv46_address(ip)
        except forms.ValidationError:
            raise forms.ValidationError(
                "Introduce una dirección IP válida IPv4 o IPv6."
            )
        return ip
