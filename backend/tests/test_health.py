import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_reports_database_ok():
    response = APIClient().get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] is True
    assert isinstance(body["search"], bool)
