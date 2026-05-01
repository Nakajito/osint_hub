import logging
import os
import re
import shutil
import tempfile

from celery.result import AsyncResult
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render

from .forms import FaceVerifyForm
from .tasks import verify_faces_task

logger = logging.getLogger(__name__)


def _safe_save(uploaded: UploadedFile, tmp_dir: str, prefix: str) -> str:
    safe = re.sub(r"[^\w\.\-]", "_", os.path.basename(uploaded.name))[:200] or "img"
    path = os.path.join(tmp_dir, f"{prefix}_{safe}")
    with open(path, "wb+") as f:
        for chunk in uploaded.chunks():
            f.write(chunk)
    return path


def index(request: HttpRequest) -> JsonResponse | object:
    if request.method == "POST":
        form = FaceVerifyForm(request.POST, request.FILES)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        tmp_dir = tempfile.mkdtemp(prefix="faceverify_")
        try:
            p1 = _safe_save(form.cleaned_data["image1"], tmp_dir, "a")
            p2 = _safe_save(form.cleaned_data["image2"], tmp_dir, "b")
        except Exception:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return JsonResponse(
                {"ok": False, "error": "Error guardando archivos"}, status=500
            )

        task = verify_faces_task.delay(p1, p2, form.cleaned_data["detector"], tmp_dir)
        return JsonResponse({"ok": True, "task_id": task.id}, status=202)

    return render(request, "faceverify/verify.html", {"form": FaceVerifyForm()})


def task_status(request: HttpRequest, task_id: str) -> JsonResponse:
    res = AsyncResult(task_id)
    if res.state in {"PENDING", "STARTED", "RETRY"}:
        return JsonResponse({"state": res.state})
    if res.state == "SUCCESS":
        return JsonResponse({"state": "SUCCESS", "result": res.result})
    if res.state == "FAILURE":
        return JsonResponse({"state": "FAILURE", "error": str(res.result)[:200]})
    return JsonResponse({"state": res.state})
