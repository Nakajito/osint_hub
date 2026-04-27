import logging
import ipaddress
import httpx
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from .forms import IPLookupForm

logger = logging.getLogger(__name__)


def _is_safe_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return not (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved)
    except ValueError:
        return False


def _build_api_url(ip: str) -> str:
    template = getattr(settings, "IP_GUIDE_API_TEMPLATE", "https://ip.guide/{ip}")
    api_key = getattr(settings, "IP_GUIDE_API_KEY", None)
    try:
        if "{api_key}" in template:
            return template.format(ip=ip, api_key=api_key or "")
        return template.format(ip=ip)
    except Exception:
        return template.replace("{ip}", ip)


def ip_search(request):
    if request.method == "POST":
        form = IPLookupForm(request.POST)
        if form.is_valid():
            ip = form.cleaned_data["ip"]
            if not _is_safe_ip(ip):
                messages.error(request, "Dirección IP no permitida.")
                return render(request, "iplookup/search.html", {"form": form})
            api_url = _build_api_url(ip)

            try:
                resp = httpx.get(api_url, timeout=15.0)
                # Try to decode JSON, fall back to text
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text, "status_code": resp.status_code}

                request.session["iplookup_results"] = data
                request.session["iplookup_ip"] = ip
                return redirect(reverse("iplookup:results"))
            except Exception as e:
                logger.exception(f"Error querying IP API for {ip}: {e}")
                messages.error(
                    request,
                    "Ocurrió un error al consultar el servicio de geolocalización. Intenta de nuevo.",
                )
                return redirect(reverse("iplookup:search"))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = IPLookupForm()

    return render(request, "iplookup/search.html", {"form": form})


def results(request):
    raw = request.session.get("iplookup_results")
    ip = request.session.get("iplookup_ip", "-")

    if not raw:
        messages.warning(request, "No se encontraron resultados en la sesión.")
        return render(request, "iplookup/results.html", {"data": None, "ip": ip})

    # Normalizar la estructura para la plantilla
    if isinstance(raw, dict):
        location = raw.get("location", {}) or {}
        network = raw.get("network", {}) or {}
        asn = network.get("autonomous_system", {}) or {}

        parsed = {
            "ip": raw.get("ip", ip),
            "location": {
                "city": location.get("city"),
                "country": location.get("country"),
                "timezone": location.get("timezone"),
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
            },
            "network": {
                "cidr": network.get("cidr"),
                "hosts": network.get("hosts"),
            },
            "asn": {
                "asn": asn.get("asn"),
                "name": asn.get("name"),
                "organization": asn.get("organization"),
                "country": asn.get("country"),
                "rir": asn.get("rir"),
            },
            "raw": raw,
        }
    else:
        parsed = {"ip": ip, "raw": raw, "location": {}, "network": {}, "asn": {}}

    return render(request, "iplookup/results.html", {"data": parsed})
