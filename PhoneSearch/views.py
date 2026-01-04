import logging
from django.shortcuts import render
from django.contrib import messages
from .forms import PhoneSearchForm
from .tasks import search_phone_async  # Importamos la función async directamente

logger = logging.getLogger(__name__)


async def search_phone(request):
    """
    Vista asíncrona que maneja el formulario y ejecuta la búsqueda en el mismo hilo.
    No requiere Celery ni Workers.
    """
    # Manejo inicial del formulario (GET y POST)
    form = PhoneSearchForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            # 1. Obtener datos limpios desde las propiedades del form
            phone = form.phone
            country_code = form.country_code

            try:
                # 2. Ejecutar búsqueda asíncrona (el navegador espera aquí)
                logger.info(
                    f"Iniciando búsqueda directa para: {phone} (+{country_code})"
                )
                results = await search_phone_async(phone, country_code)

                # 3. Calcular estadísticas para la plantilla (Importante para que se vea bien)
                found_count = sum(
                    1
                    for r in results
                    if isinstance(r, dict) and r.get("exists") is True
                )
                rate_limited = any(
                    r.get("rateLimit") for r in results if isinstance(r, dict)
                )

                context = {
                    "results": results,
                    "phone": phone,
                    "country": country_code,
                    "found_count": found_count,
                    "rate_limited": rate_limited,
                    "total_count": len(results),
                }

                # 4. Renderizar resultados directamente
                return render(request, "phonesearch/results.html", context)

            except Exception as e:
                logger.exception(f"Error en búsqueda directa: {e}")
                messages.error(request, "Ocurrió un error al procesar la búsqueda.")
                # Si falla, mostramos el formulario nuevamente con el error

        else:
            # Si el formulario no es válido, mostramos los errores
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    # Renderizar el formulario de búsqueda (para GET o si hubo error en POST)
    return render(request, "phonesearch/search.html", {"form": form})
