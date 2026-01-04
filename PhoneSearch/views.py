import logging
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from .forms import PhoneSearchForm
from .tasks import search_phone_task, test_celery
from celery.result import AsyncResult

logger = logging.getLogger(__name__)


def search_phone(request):
    """Mostrar formulario de búsqueda y procesar búsquedas."""
    if request.method == "POST":
        form = PhoneSearchForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data.get("phone")
            country_code = form.cleaned_data.get("country_code", "")

            try:
                # Iniciar task asíncrono con Celery
                logger.info(f"Iniciando Celery task para: {phone}")
                task = search_phone_task.delay(phone, country_code)

                # Guardar información en sesión
                request.session["phone_search_task_id"] = task.id
                request.session["phone_search_phone"] = phone
                request.session["phone_search_country"] = country_code
                request.session["phone_search_status"] = "processing"

                messages.info(
                    request,
                    "✅ Búsqueda iniciada. Los resultados estarán disponibles en unos momentos. "
                    "Puedes continuar navegando y volver más tarde.",
                )
                return redirect(reverse("phonesearch:check_results"))

            except Exception as e:
                logger.exception(f"Error iniciando búsqueda: {e}")
                messages.error(
                    request,
                    "❌ Error al iniciar la búsqueda. Por favor, intenta nuevamente.",
                )
                return redirect(reverse("phonesearch:search"))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PhoneSearchForm()

    return render(request, "phonesearch/search.html", {"form": form})


def check_results(request):
    """Verificar si los resultados están listos."""
    task_id = request.session.get("phone_search_task_id")
    phone = request.session.get("phone_search_phone", "No especificado")
    country = request.session.get("phone_search_country", "No especificado")

    if not task_id:
        messages.error(request, "No hay búsqueda en proceso.")
        return redirect(reverse("phonesearch:search"))

    # Verificar estado de la task
    task_result = AsyncResult(task_id)

    context = {
        "phone": phone,
        "country": country,
        "task_id": task_id,
        "task_status": task_result.status,
    }

    if task_result.ready():
        if task_result.successful():
            results = task_result.result
            request.session["phone_search_results"] = results
            request.session["phone_search_status"] = "completed"
            messages.success(request, "✅ Búsqueda completada exitosamente!")
            return redirect(reverse("phonesearch:results"))
        else:
            # Task falló
            error_msg = (
                str(task_result.result) if task_result.result else "Error desconocido"
            )
            messages.error(request, f"❌ La búsqueda falló: {error_msg}")
            return redirect(reverse("phonesearch:search"))

    # Si es AJAX request, devolver JSON
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "status": task_result.status,
                "ready": task_result.ready(),
                "phone": phone,
            }
        )

    # Mostrar página de carga
    return render(request, "phonesearch/loading.html", context)


def show_results(request):
    """Mostrar resultados de búsqueda almacenados en sesión."""
    results = request.session.get("phone_search_results", [])
    phone = request.session.get("phone_search_phone", "No especificado")
    country = request.session.get("phone_search_country", "No especificado")

    logger.info(f"Mostrando resultados para {phone}: {len(results)} entradas")

    # Parsear resultados
    found_count = sum(
        1 for r in results if isinstance(r, dict) and r.get("exists") == True
    )
    rate_limited = any(r.get("rateLimit") for r in results if isinstance(r, dict))

    context = {
        "results": results,
        "phone": phone,
        "country": country,
        "found_count": found_count,
        "rate_limited": rate_limited,
        "total_count": len(results),
    }

    return render(request, "phonesearch/results.html", context)


def test_celery_view(request):
    """Vista para probar que Celery funciona."""
    try:
        task = test_celery.delay()
        messages.success(request, f"✅ Task de prueba iniciada. ID: {task.id}")
        return redirect(reverse("phonesearch:search"))
    except Exception as e:
        messages.error(request, f"❌ Error: {str(e)}")
        return redirect(reverse("phonesearch:search"))
