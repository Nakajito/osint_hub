import json
import logging
import subprocess
import sys
import os
import shutil
import re
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages

from .forms import UsernameSearchForm


logger = logging.getLogger(__name__)


def _run_sherlock(username, timeout=60):
    """Run Sherlock and return a list of result dicts: {'site','url','exists'}.

    This tries `python -m sherlock` first and falls back to a `sherlock` executable
    if available. Supports parsing JSON output or a simple CLI-style fallback.
    """
    cmd_mod = [sys.executable, "-m", "sherlock", username, "--timeout", "10"]
    stdout = ""
    stderr = ""
    try:
        proc = subprocess.run(cmd_mod, capture_output=True, text=True, timeout=timeout)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
    except Exception:
        stdout = ""
        stderr = ""

    # fallback to sherlock console script if module did not produce output
    if not stdout:
        sherlock_exe = shutil.which("sherlock")
        if not sherlock_exe:
            bin_path = os.path.dirname(sys.executable)
            possible = os.path.join(bin_path, "sherlock")
            if os.path.exists(possible):
                sherlock_exe = possible

        if sherlock_exe:
            cmd = [sherlock_exe, username, "--timeout", "10", "--print-all"]
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=timeout
                )
                stdout = proc.stdout or ""
                stderr = proc.stderr or ""
            except Exception as e:
                logger.exception("Error running sherlock executable: %s", e)
                stderr = str(e)

    results = []
    # Try JSON parse
    try:
        data = json.loads(stdout)
        for site, info in data.items():
            if isinstance(info, dict):
                results.append(
                    {
                        "site": site,
                        "url": info.get("url"),
                        "exists": bool(info.get("exists")),
                    }
                )
            else:
                results.append({"site": site, "url": None, "exists": False})
        return results
    except Exception:
        # not JSON, fall through to text parsing
        pass

    # Simple text parsing fallback
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^[\[\+\-\s]*\]?\s*([^:]+):\s*(.*)$", line)
        if m:
            site = m.group(1).strip()
            rest = m.group(2).strip()
            is_url = rest.startswith("http://") or rest.startswith("https://")
            exists = is_url or (
                not rest.lower().startswith("not found")
                and not rest.lower().startswith("error")
                and rest != ""
            )
            url = rest if is_url else None
            results.append({"site": site, "url": url, "exists": bool(exists)})

    if not results and (stderr or stdout):
        err_text = stderr or stdout
        results.append(
            {"site": "sherlock", "url": None, "exists": False, "error": err_text}
        )

    return results


def search_username(request):
    """Show search form and run Sherlock on POST; persist results to session and disk."""
    if request.method == "POST":
        form = UsernameSearchForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            try:
                results_dir = getattr(settings, "BASE_DIR", None)
                base_results = None
                if results_dir:
                    base_results = os.path.join(
                        results_dir, "search_results", "username"
                    )
                    os.makedirs(base_results, exist_ok=True)

                results = _run_sherlock(username)

                request.session["username_search_results"] = results
                request.session["username_search_username"] = username

                # persist files
                if base_results:
                    try:
                        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                        json_path = os.path.join(
                            base_results, f"sherlock_{username}_{timestamp}.json"
                        )
                        with open(json_path, "w", encoding="utf-8") as jf:
                            json.dump(results, jf, ensure_ascii=False, indent=2)

                        txt_path = os.path.join(
                            base_results, f"sherlock_{username}_{timestamp}.txt"
                        )
                        lines = [
                            f"Sherlock results for: {username}",
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
    # Build CSV content
    import csv
    from io import StringIO

    sio = StringIO()
    writer = csv.writer(sio)

    # CSV columns (header + rows)
    writer.writerow(["site", "url", "exists", "error"])

    if not results:
        # no results -> produce no data rows (only header), or optionally one row indicating empty
        pass
    else:
        for r in results:
            site = r.get("site") or ""
            url = r.get("url") or ""
            exists = "YES" if r.get("exists") else "NO"
            error = r.get("error") or ""
            writer.writerow([site, url, exists, error])

    content = sio.getvalue()
    filename = f"sherlock_{username}.csv"
    response = HttpResponse(content, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
