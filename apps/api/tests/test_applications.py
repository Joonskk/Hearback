import uuid

import pytest
from sqlalchemy import func, select

from app.models import Company

PAYLOAD = {
    "company_name": "Stripe",
    "title": "Software Engineer Intern",
    "url": "https://jobs.example.com/stripe/123",
}


@pytest.fixture
def headers_for(make_token):
    def _headers(sub: str = "sub-a") -> dict[str, str]:
        token = make_token(sub=sub, email=f"{sub}@example.com")
        return {"Authorization": f"Bearer {token}"}

    return _headers


def test_create_returns_application_with_created_event(client, headers_for):
    response = client.post("/applications", json=PAYLOAD, headers=headers_for())

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "applied"
    assert body["company_name"] == "Stripe"
    assert body["title"] == "Software Engineer Intern"
    assert [event["type"] for event in body["events"]] == ["created"]


def test_get_returns_the_created_application(client, headers_for):
    created = client.post("/applications", json=PAYLOAD, headers=headers_for()).json()

    response = client.get(f"/applications/{created['id']}", headers=headers_for())

    assert response.status_code == 200
    assert response.json() == created


def test_company_name_ignores_case(client, db, headers_for):
    client.post(
        "/applications",
        json={"company_name": "Stripe", "title": "SWE Intern"},
        headers=headers_for(),
    )
    client.post(
        "/applications",
        json={"company_name": "stripe", "title": "Data Intern"},
        headers=headers_for(),
    )

    assert db.scalar(select(func.count()).select_from(Company)) == 1


def test_same_job_twice_is_409(client, headers_for):
    client.post("/applications", json=PAYLOAD, headers=headers_for())
    response = client.post("/applications", json=PAYLOAD, headers=headers_for())

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_application"


def test_other_users_application_is_404(client, headers_for):
    created = client.post("/applications", json=PAYLOAD, headers=headers_for("sub-a")).json()

    response = client.get(f"/applications/{created['id']}", headers=headers_for("sub-b"))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_missing_application_is_404(client, headers_for):
    response = client.get(f"/applications/{uuid.uuid4()}", headers=headers_for())
    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"company_name": "Stripe"},
        {"company_name": "Stripe", "title": "SWE", "source": "linkedin"},
        {"company_name": "   ", "title": "SWE"},
    ],
    ids=["missing-title", "bad-source", "blank-company"],
)
def test_invalid_input_is_422(client, headers_for, payload):
    response = client.post("/applications", json=payload, headers=headers_for())

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"


def test_requires_a_token(client):
    response = client.post("/applications", json=PAYLOAD)
    assert response.status_code == 401
