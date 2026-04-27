import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
def test_email_search_valid_email(client):
    """Valid email search should redirect to results."""
    with patch("email_holehe.views.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="[+] Email used on GitHub\n",
            stderr="",
            returncode=0
        )
        resp = client.post("/email/search/", {"email": "test@example.com"})
    assert resp.status_code == 302


@pytest.mark.django_db
def test_email_search_invalid_email_rejected(client):
    """Invalid email format must be rejected."""
    resp = client.post("/email/search/", {"email": "not-an-email"})
    assert resp.status_code == 200
    content = resp.content.decode()
    assert "válido" in content


@pytest.mark.django_db
def test_hash_md5_text(client):
    """MD5 hash of 'hello' must equal known value."""
    resp = client.post(
        "/hash/",
        {
            "input_type": "text",
            "text_input": "hello",
            "algorithm": "md5",
            "action": "Gen",
            "generate": "1",
            "text": "hello",
        }
    )
    assert "5d41402abc4b2a76b9719d911017c592" in resp.content.decode()


@pytest.mark.django_db
def test_exiftool_upload_rejects_oversized_file(client, tmp_path):
    """Files over 50MB must be rejected."""
    big_file = tmp_path / "big.jpg"
    big_file.write_bytes(b"x" * (51 * 1024 * 1024))
    with open(big_file, "rb") as f:
        resp = client.post("/exiftool/upload/", {"file": f})
    assert resp.status_code == 302


@pytest.mark.django_db
def test_iplookup_valid_ip_uses_api(client):
    """Valid public IP should trigger API call."""
    import httpx
    with patch("IPLookup.views.httpx.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"ip": "8.8.8.8", "location": {}, "network": {}}
        )
        resp = client.post("/ip/", {"ip": "8.8.8.8"})
    assert resp.status_code == 302
