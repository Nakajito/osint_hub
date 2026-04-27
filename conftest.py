import os
os.environ.setdefault("SECRET_KEY", "test-only-insecure-key-not-for-production")

import pytest
from django.test import RequestFactory


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def sample_image(tmp_path):
    f = tmp_path / "test.jpg"
    f.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
    return f
