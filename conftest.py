import pytest
from django.test import RequestFactory, Client


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def sample_image(tmp_path):
    f = tmp_path / "test.jpg"
    f.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
    return f
