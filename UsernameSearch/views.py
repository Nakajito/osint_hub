import json
import logging
import subprocess
import sys
import os
import shutil
import re
from datetime import datetime

# Intentamos importar werkzeug, si no está, usaremos el fallback
try:
    from werkzeug.utils import secure_filename
except ImportError:
    secure_filename = None

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages

from .forms import UsernameSearchForm


logger = logging.getLogger(__name__)


def get_safe_filename(filename):
    """
    Sanitiza estrictamente el input para usarlo como nombre de archivo o directorio.
    Elimina caracteres peligrosos y Directory Traversal.
    """
    if secure_filename:
        # Opción A: Usar Werkzeug si está disponible
        safe = secure_filename(filename)
    else:
        # Opción B: Fallback estricto (Regex)
        # Elimina todo lo que NO sea alfanumérico (a-z, A-Z, 0-9).
        # Si quieres permitir guiones bajos, usa r'[^a-zA-Z0-9_]'
        safe = re.sub(r"[^a-zA-Z0-9]", "", str(filename).strip())

    # Si el nombre queda vacío tras la limpieza, usamos uno por defecto
    if not safe:
        safe = "unknown_user"

    return safe


def _run_sherlock(username, timeout=300):
    """Run Sherlock and return a list of result dicts: {'site','url','exists'}.
    (Sin cambios en la lógica de ejecución, solo sanitización externa)
    """
    cmd_mod = [
        sys.executable,
        "-m",
        "sherlock",
        username,
        "--timeout",
        "15",
        "--no-color",
    ]

    stdout = ""
    stderr = ""

    try:
        proc = subprocess.run(cmd_mod, capture_output=True, text=True, timeout=timeout)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
    except subprocess.TimeoutExpired:
        logger.error("Sherlock Timeout: El proceso tardó más de 300s")
        return [
            {
                "site": "Timeout",
                "url": None,
                "exists": False,
                "error": "La búsqueda tardó demasiado",
            }
        ]
    except Exception as e:
        logger.error(f"Error crítico ejecutando sherlock: {e}")
        return []

    if not stdout:
        sherlock_exe = shutil.which("sherlock")
        if not sherlock_exe:
            bin_path = os.path.dirname(sys.executable)
            possible = os.path.join(bin_path, "sherlock")
            if os.path.exists(possible):
                sherlock_exe = possible

        if sherlock_exe:
            cmd = [
                sherlock_exe,
                username,
                "--timeout",
                "15",
                "--print-all",
                "--no-color",
            ]
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=timeout
                )
                stdout = proc.stdout or ""
            except Exception as e:
                logger.error(f"Error fallback sherlock: {e}")

    results = []

    for line in (stdout or "").splitlines():
        line = line.strip()
        match = re.search(r"\[\+\]\s+([^:]+):\s+(http.*)$", line)

        if match:
            site = match.group(1).strip()
            url = match.group(2).strip()
            results.append({"site": site, "url": url, "exists": True})

    if not results and "Blocked" in stdout:
        results.append(
            {
                "site": "Aviso",
                "url": None,
                "exists": False,
                "error": "IP Bloqueada por varios sitios",
            }
        )

    return results


def search_username(request):
    """Show search form and run Sherlock on POST; persist results to session and disk."""
    if request.method == "POST":
        form = UsernameSearchForm(request.POST)
        if form.is_valid():
            # Username original para Sherlock (puede contener puntos, guiones, etc.)
            raw_username = form.cleaned_data.get("username")

            # Username SANITIZADO para Rutas de Archivos (Directory Traversal Prevention)
            safe_filename = get_safe_filename(raw_username)

            try:
                base_results = None
                search_root = getattr(settings, "SEARCH_RESULTS_DIR", None)
                if not search_root:
                    try:
                        search_root = os.path.expanduser("~/.local/share/osint_hub")
                    except Exception:
                        search_root = None
                if not search_root:
                    project_base = getattr(settings, "BASE_DIR", None)
                    if project_base:
                        search_root = os.path.join(project_base, "search_results")

                if search_root:
                    # USAR SAFE_FILENAME AQUÍ
                    base_results = os.path.join(search_root, safe_filename)
                    try:
                        # os.makedirs es seguro ahora porque base_results usa el nombre sanitizado
                        os.makedirs(base_results, exist_ok=True)
                    except Exception:
                        logger.exception(
                            "Failed to create results directory: %s", base_results
                        )
                        base_results = None

                logger.info("search_username: persistence dir=%s", base_results)

                # Ejecutamos Sherlock con el username REAL
                results = _run_sherlock(raw_username)

                request.session["username_search_results"] = results
                request.session["username_search_username"] = raw_username

                # Persistir archivos usando SAFE_FILENAME
                if base_results:
                    try:
                        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                        # Usamos safe_filename en el nombre del archivo
                        json_path = os.path.join(
                            base_results, f"sherlock_{safe_filename}_{timestamp}.json"
                        )
                        with open(json_path, "w", encoding="utf-8") as jf:
                            json.dump(results, jf, ensure_ascii=False, indent=2)

                        txt_path = os.path.join(
                            base_results, f"sherlock_{safe_filename}_{timestamp}.txt"
                        )
                        lines = [
                            f"Sherlock results for: {raw_username}",
                            f"Timestamp: {datetime.utcnow().isoformat()}Z",
                            "",
                        ]
                        if not results:
                            lines.append("No results found.")
                        else:
                            for r in results:
                                site = r.get("site") or "-"
                                url = r.get("url") or "-"
                                exists = "YES" if r.get("exists") else "NO"
                                error = r.get("error")
                                if error:
                                    lines.append(
                                        f"{site}\t{url}\t{exists}\tERROR: {error}"
                                    )
                                else:
                                    lines.append(f"{site}\t{url}\t{exists}")

                        with open(txt_path, "w", encoding="utf-8") as tf:
                            tf.write("\n".join(lines))
                    except Exception:
                        logger.exception("Failed to write search results to disk")

                # Limpieza de archivos antiguos
                try:
                    cnt = (
                        int(request.session.get("username_search_dir_clean_count", 0))
                        + 1
                    )
                    request.session["username_search_dir_clean_count"] = cnt
                    if base_results and cnt >= 3:
                        try:
                            # base_results ya es seguro, podemos listar
                            for fname in os.listdir(base_results):
                                path = os.path.join(base_results, fname)
                                try:
                                    if os.path.isfile(path) or os.path.islink(path):
                                        os.unlink(path)
                                    elif os.path.isdir(path):
                                        shutil.rmtree(path)
                                except Exception:
                                    logger.exception(
                                        "Failed to remove result file during auto-clean: %s",
                                        path,
                                    )
                        except Exception:
                            logger.exception(
                                "Failed to iterate results dir for auto-clean: %s",
                                base_results,
                            )
                        request.session["username_search_dir_clean_count"] = 0
                except Exception:
                    logger.exception(
                        "Error updating username_search_dir_clean_count in session"
                    )

                # Limpieza Legacy (Archivos antiguos en raíz)
                # IMPORTANTE: Sanitizar también aquí para evitar borrar archivos arbitrarios
                try:
                    project_base = getattr(settings, "BASE_DIR", None)
                    if project_base:
                        for ext in (".txt", ".json", ".csv", ""):
                            # Usamos safe_filename para evitar '..' en la construcción del path
                            candidate = os.path.join(
                                project_base, f"{safe_filename}{ext}"
                            )

                            # Validación extra de seguridad: asegurar que candidate está dentro de project_base
                            # (Aunque safe_filename debería prevenirlo, es defensa en profundidad)
                            if os.path.abspath(candidate).startswith(
                                os.path.abspath(project_base)
                            ):
                                if os.path.exists(candidate) and os.path.isfile(
                                    candidate
                                ):
                                    try:
                                        os.unlink(candidate)
                                        logger.info(
                                            "Removed legacy root file: %s", candidate
                                        )
                                    except Exception:
                                        logger.exception(
                                            "Failed to remove legacy root file: %s",
                                            candidate,
                                        )
                except Exception:
                    logger.exception(
                        "Error while attempting to clean legacy root files"
                    )

                return redirect(reverse("usersearch:results"))
            except Exception as e:
                logger.exception("Error running sherlock: %s", e)
                messages.error(request, f"Error ejecutando Sherlock: {e}")
                return redirect(reverse("usersearch:search"))
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, str(err))
    else:
        form = UsernameSearchForm()

    return render(request, "usersearch/search.html", {"form": form})


def show_results(request):
    """Render all results (or only found ones) — no pagination."""
    results = request.session.get("username_search_results", []) or []
    username = request.session.get("username_search_username", "-")

    # normalize
    if isinstance(results, str):
        try:
            results = json.loads(results)
        except Exception:
            results = [
                {
                    "site": "sherlock",
                    "url": None,
                    "exists": False,
                    "error": str(results),
                }
            ]

    normalized = []
    for r in results:
        if isinstance(r, dict):
            normalized.append(r)
        else:
            try:
                normalized.append(dict(r))
            except Exception:
                normalized.append({"site": str(r), "url": None, "exists": False})

    results = normalized
    found_count = sum(1 for r in results if r.get("exists"))

    show_all = request.GET.get("show_all") in ("1", "true", "yes")
    if show_all:
        displayed = results
    else:
        displayed = [r for r in results if r.get("exists")]

    logger.info(
        "show_results: username=%s results_count=%d displayed_count=%d",
        username,
        len(results),
        len(displayed),
    )

    return render(
        request,
        "usersearch/results.html",
        {
            "results": displayed,
            "username": username,
            "found_count": found_count,
            "show_all": show_all,
        },
    )


def download_results(request):
    """Return a plain-text file with the search results stored in session."""
    results = request.session.get("username_search_results", [])
    username = request.session.get("username_search_username", "-")

    # Sanitizamos el nombre de usuario para el archivo de descarga también
    safe_filename = get_safe_filename(username)

    import csv
    from io import StringIO

    sio = StringIO()
    writer = csv.writer(sio)

    writer.writerow(["site", "url", "exists", "error"])

    if results:
        for r in results:
            site = r.get("site") or ""
            url = r.get("url") or ""
            exists = "YES" if r.get("exists") else "NO"
            error = r.get("error") or ""
            writer.writerow([site, url, exists, error])

    content = sio.getvalue()
    filename = f"sherlock_{safe_filename}.csv"
    response = HttpResponse(content, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
