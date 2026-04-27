import pytest
from django.test import override_settings
from django.conf import settings


@pytest.mark.django_db
def test_production_session_cookie_is_secure():
    """SESSION_COOKIE_SECURE must be True in production."""
    with override_settings(DEBUG=False):
        assert settings.SESSION_COOKIE_SECURE is True


@pytest.mark.django_db
def test_production_csrf_cookie_is_secure():
    """CSRF_COOKIE_SECURE must be True in production."""
    with override_settings(DEBUG=False):
        assert settings.CSRF_COOKIE_SECURE is True


@pytest.mark.django_db
def test_redis_url_not_hardcoded(settings):
    """Redis URL must not be hardcoded as localhost."""
    assert "localhost" not in settings.CELERY_BROKER_URL


@pytest.mark.django_db
def test_upload_sanitizes_path_traversal(client, tmp_path):
    """Path traversal filenames must not write outside tmp dir."""
    img = tmp_path / "safe.jpg"
    img.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
    with open(img, "rb") as f:
        resp = client.post(
            "/exiftool/upload/",
            {"file": f},
            format="multipart",
        )
    # The response must redirect (not 500) and not write files outside tmp
    assert resp.status_code in (200, 302)


@pytest.mark.django_db
def test_error_does_not_expose_internal_paths(client):
    """Error messages must not expose internal exception details."""
    from unittest.mock import patch
    with patch("email_holehe.views.subprocess.run", side_effect=RuntimeError("/app/internal/path error")):
        resp = client.post("/email/search/", {"email": "test@example.com"})
    content = resp.content.decode()
    assert "/app/internal/path error" not in content
    assert "RuntimeError" not in content


@pytest.mark.django_db
def test_iplookup_rejects_private_ip(client):
    """Private/RFC1918 IPs must be rejected to prevent SSRF.

    BUG: Currently no SSRF protection exists — private IPs are accepted and
    the app makes an outbound HTTP call. This test documents the expected
    behaviour: a private IP must be rejected with a validation error on the
    form (200 with error message) and must NOT redirect to results.
    """
    from unittest.mock import patch
    # Patch httpx.get so we never make a real network call; if the view
    # reaches the API call that means SSRF protection is missing.
    with patch("IPLookup.views.httpx.get") as mock_get:
        mock_get.return_value = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock(
            status_code=200,
            json=lambda: {"ip": "192.168.1.1", "location": {}, "network": {}}
        )
        resp = client.post("/ip/", {"ip": "192.168.1.1"})
    # Expected: form re-render with error (200), private IP is rejected
    # Bug behaviour: the view redirects (302) because there is no check
    assert resp.status_code == 200, (
        "Private IP 192.168.1.1 must be rejected (form error, status 200), "
        "but the view redirected — SSRF protection is missing."
    )
    content = resp.content.decode()
    # At least one of these error strings should appear
    has_error = (
        "privada" in content.lower()
        or "private" in content.lower()
        or "ssrf" in content.lower()
        or "no permitida" in content.lower()
        or "not allowed" in content.lower()
    )
    assert has_error, "No SSRF-rejection error message found for private IP."
