"""Tests for FaceVerify app — written first (TDD)."""

import io
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from PIL import Image


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _png_bytes() -> bytes:
    """Return bytes of a valid 1×1 px PNG (Pillow-verifiable)."""
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), color=(255, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


def _make_upload(
    name: str = "photo.png",
    content_type: str = "image/png",
    fake_size: int | None = None,
) -> SimpleUploadedFile:
    """Create an upload with valid PNG content. Override `size` if fake_size given."""
    f = SimpleUploadedFile(name, _png_bytes(), content_type=content_type)
    if fake_size is not None:
        f.size = fake_size
    return f


def _make_bad_upload(
    name: str = "evil.exe", content_type: str = "application/octet-stream"
) -> SimpleUploadedFile:
    """Non-image upload (PIL will reject it)."""
    return SimpleUploadedFile(name, b"\x00" * 100, content_type=content_type)


# ---------------------------------------------------------------------------
# Form tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFaceVerifyForm:
    def test_form_rejects_oversize_file(self):
        """File > 10 MB (faked size on valid PNG) should make form invalid with '10 MB'."""
        from FaceVerify.forms import FaceVerifyForm, MAX_FILE_SIZE

        big = _make_upload(fake_size=MAX_FILE_SIZE + 1)
        normal = _make_upload()
        form = FaceVerifyForm(
            data={"detector": "mtcnn"},
            files={"image1": big, "image2": normal},
        )
        assert not form.is_valid()
        assert "10 MB" in str(form.errors)

    def test_form_rejects_bad_content_type(self):
        """Non-image file (PIL-rejected) should make form invalid."""
        from FaceVerify.forms import FaceVerifyForm

        bad = _make_bad_upload()
        normal = _make_upload()
        form = FaceVerifyForm(
            data={"detector": "mtcnn"},
            files={"image1": bad, "image2": normal},
        )
        assert not form.is_valid()

    def test_form_accepts_webp_png_jpg(self):
        """Valid PNG content passed with jpeg/webp/png MIME types should be accepted.

        ImageField validates by reading actual file bytes (PIL), not MIME header.
        Our _validate_image checks content_type against ALLOWED_CONTENT_TYPES,
        so we confirm each type is in the allowlist.
        """
        from FaceVerify.forms import FaceVerifyForm

        for ct, ext in [
            ("image/jpeg", "a.jpg"),
            ("image/webp", "a.webp"),
            ("image/png", "a.png"),
        ]:
            img1 = _make_upload(name=ext, content_type=ct)
            img2 = _make_upload(name=ext, content_type=ct)
            form = FaceVerifyForm(
                data={"detector": "mtcnn"},
                files={"image1": img1, "image2": img2},
            )
            assert form.is_valid(), f"Expected valid for {ct}, got: {form.errors}"


# ---------------------------------------------------------------------------
# View tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIndexView:
    def test_index_get_renders_template(self, client: Client):
        """GET /face/ should return 200 and render 'faceverify/verify.html'."""
        response = client.get("/face/")
        assert response.status_code == 200
        assert "faceverify/verify.html" in [t.name for t in response.templates]

    def test_index_post_invalid_returns_400(self, client: Client):
        """POST without images should return 400 JSON with errors."""
        # Django test client sends multipart form-data by default when data is a dict.
        # Sending only the detector field (no image files) triggers form validation failure.
        response = client.post("/face/", data={"detector": "mtcnn"})
        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert "errors" in data

    def test_index_post_valid_returns_202(self, client: Client):
        """Valid POST with mocked task should return 202 JSON with task_id."""
        mock_result = MagicMock()
        mock_result.id = "fake-task-id-123"

        img1 = _make_upload(name="face1.png", content_type="image/png")
        img2 = _make_upload(name="face2.png", content_type="image/png")

        with patch("FaceVerify.views.verify_faces_task") as mock_task:
            mock_task.delay.return_value = mock_result
            response = client.post(
                "/face/",
                data={"detector": "mtcnn", "image1": img1, "image2": img2},
            )

        assert response.status_code == 202
        body = response.json()
        assert body["ok"] is True
        assert body["task_id"] == "fake-task-id-123"


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------


class TestVerifyFacesTask:
    """Tests call the Celery task function directly (no broker needed).

    The task does ``from deepface import DeepFace`` inside the function body,
    so we patch sys.modules["deepface"] with a MagicMock.  That means
    ``from deepface import DeepFace`` resolves to ``mock_module.DeepFace``
    (an auto-created sub-mock attribute), so we configure behaviour on
    ``mock_module.DeepFace.verify``, not ``mock_module.verify``.
    """

    def _make_deepface_module_mock(self, **overrides: object) -> MagicMock:
        """Return a mock representing the *deepface* module with DeepFace.verify stubbed."""
        defaults = {
            "verified": True,
            "distance": 0.2,
            "threshold": 0.68,
            "confidence": 85.0,
            "model": "ArcFace",
            "distance_metric": "cosine",
        }
        defaults.update(overrides)
        mock_module = MagicMock()
        mock_module.DeepFace.verify.return_value = defaults
        return mock_module

    def test_task_cleans_tmp_dir_on_success(self, tmp_path: object) -> None:
        """Temp dir must be deleted after successful DeepFace.verify call."""
        mock_module = self._make_deepface_module_mock()

        # Ensure a fresh import of the task module inside the patch context
        sys.modules.pop("FaceVerify.tasks", None)

        with patch.dict("sys.modules", {"deepface": mock_module}):
            from FaceVerify.tasks import verify_faces_task  # noqa: PLC0415

            tmp_dir = tempfile.mkdtemp()
            p1 = os.path.join(tmp_dir, "a.jpg")
            p2 = os.path.join(tmp_dir, "b.jpg")
            open(p1, "w").close()  # noqa: WPS515
            open(p2, "w").close()  # noqa: WPS515

            result = verify_faces_task(p1, p2, "mtcnn", tmp_dir)

        assert not os.path.exists(tmp_dir), "tmp_dir should have been cleaned up"
        assert result["ok"] is True

    def test_task_cleans_tmp_dir_on_exception(self, tmp_path: object) -> None:
        """Temp dir must be deleted even when an unexpected exception occurs."""
        mock_module = MagicMock()
        mock_module.DeepFace.verify.side_effect = RuntimeError("GPU exploded")

        sys.modules.pop("FaceVerify.tasks", None)

        with patch.dict("sys.modules", {"deepface": mock_module}):
            from FaceVerify.tasks import verify_faces_task  # noqa: PLC0415

            tmp_dir = tempfile.mkdtemp()
            p1 = os.path.join(tmp_dir, "a.jpg")
            p2 = os.path.join(tmp_dir, "b.jpg")
            open(p1, "w").close()  # noqa: WPS515
            open(p2, "w").close()  # noqa: WPS515

            result = verify_faces_task(p1, p2, "mtcnn", tmp_dir)

        assert not os.path.exists(tmp_dir), (
            "tmp_dir should be cleaned up even on exception"
        )
        assert result["ok"] is False

    def test_task_returns_no_face_error_on_value_error(self, tmp_path: object) -> None:
        """ValueError from DeepFace should produce ok=False with 'No se detectó rostro'."""
        mock_module = MagicMock()
        mock_module.DeepFace.verify.side_effect = ValueError(
            "Face could not be detected"
        )

        sys.modules.pop("FaceVerify.tasks", None)

        with patch.dict("sys.modules", {"deepface": mock_module}):
            from FaceVerify.tasks import verify_faces_task  # noqa: PLC0415

            tmp_dir = tempfile.mkdtemp()
            p1 = os.path.join(tmp_dir, "a.jpg")
            p2 = os.path.join(tmp_dir, "b.jpg")
            open(p1, "w").close()  # noqa: WPS515
            open(p2, "w").close()  # noqa: WPS515

            result = verify_faces_task(p1, p2, "mtcnn", tmp_dir)

        assert result["ok"] is False
        assert "No se detectó rostro" in result["error"]


# ---------------------------------------------------------------------------
# Status endpoint test
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStatusEndpoint:
    def test_status_endpoint_pending(self, client: Client):
        """GET /face/status/<fake-id>/ should return JSON with state=PENDING."""
        with patch("FaceVerify.views.AsyncResult") as mock_ar:
            mock_ar.return_value.state = "PENDING"
            response = client.get("/face/status/fake-id/")

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "PENDING"
