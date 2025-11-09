from django.shortcuts import render, redirect
from django.contrib import messages


def search_email(request):
    """Vista para mostrar el formulario de búsqueda de email"""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "Por favor, ingresa un correo electrónico.")
            return render(request, "email_holehe/search.html")

        # TODO: Implementar la búsqueda con Holehe
        # Por ahora, redirigir a resultados de prueba
        return redirect("email_holehe:results")

    return render(request, "email_holehe/search.html")


def search_results(request):
    """Vista para mostrar los resultados de la búsqueda"""
    # TODO: Implementar la lógica de resultados
    context = {"email": "ejemplo@correo.com", "results": []}
    return render(request, "email_holehe/results.html", context)
