from django.shortcuts import render, redirect
from django.contrib import messages
import subprocess
import json
import re
import sys
import os


def search_email(request):
    """Vista para mostrar el formulario de búsqueda de email"""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "Por favor, ingresa un correo electrónico.")
            return render(request, "email_holehe/search.html")

        # Validar formato de email
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, email):
            messages.error(request, "Por favor, ingresa un correo electrónico válido.")
            return render(request, "email_holehe/search.html")

        try:
            # Obtener la ruta del ejecutable de holehe en el entorno virtual
            venv_bin = os.path.dirname(sys.executable)
            holehe_path = os.path.join(venv_bin, "holehe")

            # Si no existe en el venv, usar el comando global
            if not os.path.exists(holehe_path):
                holehe_path = "holehe"

            # Ejecutar Holehe
            result = subprocess.run(
                [holehe_path, email, "--only-used"],
                capture_output=True,
                text=True,
                timeout=60,  # Timeout de 60 segundos
            )

            # Guardar email en sesión para la página de resultados
            request.session["searched_email"] = email
            request.session["holehe_output"] = result.stdout
            request.session["holehe_stderr"] = result.stderr

            messages.success(request, f"Búsqueda completada para {email}")
            return redirect("email_holehe:results")

        except subprocess.TimeoutExpired:
            messages.error(
                request, "La búsqueda tardó demasiado tiempo. Intenta nuevamente."
            )
            return render(request, "email_holehe/search.html")
        except FileNotFoundError:
            messages.error(
                request, "Holehe no está instalado. Por favor, instala holehe primero."
            )
            return render(request, "email_holehe/search.html")
        except Exception as e:
            messages.error(request, f"Error al realizar la búsqueda: {str(e)}")
            return render(request, "email_holehe/search.html")

    return render(request, "email_holehe/search.html")


def search_results(request):
    """Vista para mostrar los resultados de la búsqueda"""
    # Obtener email y resultados de la sesión
    email = request.session.get("searched_email", "ejemplo@correo.com")
    holehe_output = request.session.get("holehe_output", "")

    # Parsear resultados de Holehe
    results = parse_holehe_output(holehe_output)

    context = {
        "email": email,
        "results": results,
        "total_platforms": len(results),
    }

    return render(request, "email_holehe/results.html", context)


def parse_holehe_output(output):
    """
    Parsea la salida de Holehe y extrae los servicios donde se encontró el email.
    Holehe muestra líneas con [+] para servicios encontrados.
    """
    results = []

    if not output:
        return results

    # Dividir por líneas
    lines = output.strip().split("\n")

    for line in lines:
        # Buscar líneas que indican que se encontró el email
        # Formato típico: "[+] Email used on ServiceName"
        if "[+]" in line:
            # Extraer el nombre del servicio
            # El formato puede variar, intentamos diferentes patrones

            # Patrón 1: [+] Email used on ServiceName
            match = re.search(r"\[\+\]\s+Email used on\s+(.+)", line, re.IGNORECASE)
            if match:
                service_name = match.group(1).strip()
                results.append(
                    {
                        "platform": service_name,
                        "details": "Email encontrado en esta plataforma",
                        "status": "found",
                    }
                )
                continue

            # Patrón 2: [+] ServiceName
            match = re.search(r"\[\+\]\s+(.+?)(?:\s+\[|$)", line)
            if match:
                service_name = match.group(1).strip()
                # Filtrar nombres muy cortos o genéricos
                if len(service_name) > 2:
                    results.append(
                        {
                            "platform": service_name,
                            "details": "Email registrado",
                            "status": "found",
                        }
                    )

    # Eliminar duplicados manteniendo el orden
    seen = set()
    unique_results = []
    for result in results:
        platform = result["platform"].lower()
        if platform not in seen:
            seen.add(platform)
            unique_results.append(result)

    return unique_results
