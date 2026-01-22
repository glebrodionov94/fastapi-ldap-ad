from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)


@patch("app.services.ldap_service.ldap_service.search")
def test_list_users_empty(mock_search: MagicMock) -> None:
    mock_search.return_value = []
    response = client.get("/users?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["skip"] == 0
    assert data["limit"] == 10
    assert data["pages"] == 0


@patch("app.services.ldap_service.ldap_service.search")
def test_list_users_with_pagination(mock_search: MagicMock) -> None:
    mock_search.return_value = [
        {
            "distinguishedName": ["CN=John Doe,OU=Users,DC=example,DC=com"],
            "cn": ["John Doe"],
            "sAMAccountName": ["jdoe"],
            "givenName": ["John"],
            "sn": ["Doe"],
            "mail": ["jdoe@example.com"],
            "telephoneNumber": [None],
            "title": [None],
            "department": [None],
            "description": [None],
            "userAccountControl": [512],
        }
    ]
    response = client.get("/users?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["sAMAccountName"] == "jdoe"
    assert data["total"] == 1
    assert data["pages"] == 1
