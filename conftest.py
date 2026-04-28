import os
os.environ.setdefault("SECRET_KEY", "test-only-insecure-key-not-for-production")

import django
from django.test import override_settings

import pytest
from django.test import RequestFactory

# Override the staticfiles storage globally for all tests so that
# CompressedManifestStaticFilesStorage does not require a pre-built manifest.
_STORAGES_OVERRIDE = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


def pytest_configure(config):
    """Apply global Django settings overrides before tests run."""
    from django.conf import settings as django_settings
    # Only override once Django is configured
    try:
        django_settings.STORAGES = _STORAGES_OVERRIDE
    except Exception:
        pass


@pytest.fixture(autouse=True)
def override_staticfiles_storage(settings):
    """Ensure every test uses plain StaticFilesStorage to avoid manifest errors."""
    settings.STORAGES = _STORAGES_OVERRIDE


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def sample_image(tmp_path):
    f = tmp_path / "test.jpg"
    f.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
    return f
