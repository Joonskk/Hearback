import pytest

PAYLOAD = {"company_name": "Stripe", "title": "Software Engineer Intern"}


@pytest.fixture
def application_id(client, headers_for) -> str:
    response = client.post("/applications", json=PAYLOAD, headers=headers_for())
    return response.json()["id"]


def change(client, headers, application_id, to_status, note=None):
    body = {"to_status": to_status}
    if note is not None:
        body["note"] = note
    return client.post(f"/applications/{application_id}/status", json=body, headers=headers)


def test_move_forward_adds_an_event(client, headers_for, application_id):
    response = change(client, headers_for(), application_id, "interview")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "interview"
    assert [event["type"] for event in body["events"]] == ["status_changed", "created"]
    newest = body["events"][0]
    assert (newest["from_status"], newest["to_status"]) == ("applied", "interview")
    assert newest["details"] == {}
    assert body["last_event_at"] == newest["occurred_at"]


def test_note_is_stored_on_the_event(client, headers_for, application_id):
    response = change(client, headers_for(), application_id, "assessment", note="HackerRank OA")
    assert response.json()["events"][0]["details"] == {"note": "HackerRank OA"}


def test_manual_backward_move_is_flagged_as_correction(client, headers_for, application_id):
    change(client, headers_for(), application_id, "offer")
    response = change(client, headers_for(), application_id, "applied")

    assert response.status_code == 200
    assert response.json()["status"] == "applied"
    assert response.json()["events"][0]["details"] == {"correction": True}


def test_same_status_is_409_and_writes_nothing(client, headers_for, application_id):
    response = change(client, headers_for(), application_id, "applied")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invalid_transition"
    events = client.get(f"/applications/{application_id}", headers=headers_for()).json()["events"]
    assert len(events) == 1


def test_unknown_status_is_422(client, headers_for, application_id):
    response = change(client, headers_for(), application_id, "ghosted")
    assert response.status_code == 422


def test_other_user_gets_404(client, headers_for, application_id):
    response = change(client, headers_for("sub-b"), application_id, "interview")
    assert response.status_code == 404
