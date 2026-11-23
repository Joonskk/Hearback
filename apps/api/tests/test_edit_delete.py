import pytest
from sqlalchemy import select

from app.models import ApplicationEvent

PAYLOAD = {
    "company_name": "Stripe",
    "title": "Software Engineer Intern",
    "url": "https://stripe.com/jobs/1",
    "notes": "Referral from Sam",
}


@pytest.fixture
def application_id(client, headers_for) -> str:
    response = client.post("/applications", json=PAYLOAD, headers=headers_for())
    return response.json()["id"]


def patch(client, headers, application_id, body):
    return client.patch(f"/applications/{application_id}", json=body, headers=headers)


def test_patch_notes_only_changes_notes(client, headers_for, application_id):
    response = patch(client, headers_for(), application_id, {"notes": "Recruiter call Friday"})

    assert response.status_code == 200
    body = response.json()
    assert body["notes"] == "Recruiter call Friday"
    assert (body["title"], body["url"]) == (PAYLOAD["title"], PAYLOAD["url"])
    assert body["events"][0]["type"] == "note"
    assert body["events"][0]["details"] == {"notes": "Recruiter call Friday"}


def test_patch_applied_at(client, headers_for, application_id):
    response = patch(client, headers_for(), application_id, {"applied_at": "2026-10-01T00:00:00Z"})

    body = response.json()
    assert body["applied_at"].startswith("2026-10-01")
    assert [event["type"] for event in body["events"]] == ["created"]


def test_patch_null_notes_clears_them(client, headers_for, application_id):
    response = patch(client, headers_for(), application_id, {"notes": None})
    assert response.json()["notes"] is None


def test_patch_null_applied_at_is_422(client, headers_for, application_id):
    response = patch(client, headers_for(), application_id, {"applied_at": None})
    assert response.status_code == 422


def test_patch_status_is_422(client, headers_for, application_id):
    response = patch(client, headers_for(), application_id, {"status": "offer"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"


def test_delete_removes_application_and_events(client, headers_for, application_id, db):
    headers = headers_for()

    response = client.delete(f"/applications/{application_id}", headers=headers)

    assert response.status_code == 204
    assert client.get(f"/applications/{application_id}", headers=headers).status_code == 404
    events = db.scalars(
        select(ApplicationEvent).where(ApplicationEvent.application_id == application_id)
    ).all()
    assert events == []


def test_other_user_gets_404(client, headers_for, application_id):
    other = headers_for("sub-b")

    assert patch(client, other, application_id, {"notes": "hi"}).status_code == 404
    assert client.delete(f"/applications/{application_id}", headers=other).status_code == 404
