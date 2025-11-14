import trio
import httpx
import logging
import importlib
import pkgutil
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from .forms import PhoneSearchForm

logger = logging.getLogger(__name__)


def import_ignorant_modules():
    """Import all ignorant modules dynamically."""

    def import_submodules(package, recursive=True):
        if isinstance(package, str):
            package = importlib.import_module(package)
        results = {}
        for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
            full_name = package.__name__ + "." + name
            results[full_name] = importlib.import_module(full_name)
            if recursive and is_pkg:
                results.update(import_submodules(full_name))
        return results

    modules = import_submodules("ignorant.modules")

    # Extract functions
    websites = []
    for module_name in modules:
        if len(module_name.split(".")) > 3:
            modu = modules[module_name]
            site = module_name.split(".")[-1]
            if site in modu.__dict__:
                websites.append(modu.__dict__[site])

    return websites


async def search_phone_async(phone, country_code):
    """Execute phone search using ignorant modules asynchronously."""
    websites = import_ignorant_modules()
    results = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for website in websites:
                try:
                    await website(phone, country_code, client, results)
                except Exception as e:
                    logger.warning(f"Error with {website.__name__}: {e}")
                    # Add error entry
                    results.append(
                        {
                            "name": website.__name__,
                            "domain": f"{website.__name__}.com",
                            "rateLimit": True,
                            "exists": False,
                        }
                    )
    except Exception as e:
        logger.error(f"Error during phone search: {e}")
        raise

    return results


def search_phone(request):
    """Display phone search form and process searches."""
    if request.method == "POST":
        form = PhoneSearchForm(request.POST)
        if form.is_valid():
            # Extract parsed values from form
            phone = form.phone
            country_code = form.country_code

            try:
                # Run async search
                results = trio.run(search_phone_async, phone, country_code)

                # Store in session
                request.session["phone_search_results"] = results
                request.session["phone_search_phone"] = phone
                request.session["phone_search_country"] = country_code

                return redirect(reverse("phonesearch:results"))
            except Exception as e:
                logger.exception(f"Error searching phone {phone}: {e}")
                messages.error(
                    request, f"Error durante la búsqueda: {str(e)}. Intenta nuevamente."
                )
                return redirect(reverse("phonesearch:search"))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = PhoneSearchForm()

    return render(request, "phonesearch/search.html", {"form": form})


def show_results(request):
    """Display phone search results stored in session."""
    results = request.session.get("phone_search_results", [])
    phone = request.session.get("phone_search_phone", "-")
    country = request.session.get("phone_search_country", "-")

    logger.info(
        f"show_results called - results: {len(results)}, phone: {phone}, country: {country}"
    )

    # Parse results for template display
    found_count = sum(1 for r in results if r.get("exists"))
    rate_limited = any(r.get("rateLimit") for r in results)

    # Ensure results is not None
    if not results:
        logger.warning("No results found in session")
        messages.warning(request, "No se encontraron resultados en la sesión.")

    return render(
        request,
        "phonesearch/results.html",
        {
            "results": results,
            "phone": phone,
            "country": country,
            "found_count": found_count,
            "rate_limited": rate_limited,
        },
    )
