import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_profile_view_ok(client):
    url = reverse("api-profile")
    resp = client.get(url)
    assert resp.status_code in (200, 401, 302)

@pytest.mark.django_db
def test_debug_headers_view_ok(client):
    url = reverse("debug-headers")
    resp = client.get(url)
    assert resp.status_code in (200, 401, 302)

@pytest.mark.django_db
def test_debug_authenticate_view_ok(client):
    url = reverse("debug-auth")
    resp = client.get(url)
    assert resp.status_code in (200, 401, 302)