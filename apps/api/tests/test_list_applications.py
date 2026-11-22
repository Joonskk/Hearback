from datetime import UTC, datetime, timedelta

START = datetime(2026, 9, 1, tzinfo=UTC)


def create(client, headers, i: int) -> str:
    payload = {
        "company_name": f"Company {i}",
        "title": "SWE Intern",
        "applied_at": (START + timedelta(days=i)).isoformat(),
    }
    return client.post("/applications", json=payload, headers=headers).json()["id"]


def fetch_all_pages(client, headers, **params) -> list[list[str]]:
    pages = []
    cursor = None
    while True:
        query = dict(params)
        if cursor is not None:
            query["cursor"] = cursor
        body = client.get("/applications", params=query, headers=headers).json()
        pages.append([item["id"] for item in body["items"]])
        cursor = body["next_cursor"]
        if cursor is None:
            return pages


def test_pages_cover_everything_newest_first(client, headers_for):
    headers = headers_for()
    ids = [create(client, headers, i) for i in range(25)]

    pages = fetch_all_pages(client, headers, limit=10)

    assert [len(page) for page in pages] == [10, 10, 5]
    assert sum(pages, []) == list(reversed(ids))


def test_new_application_does_not_shift_the_next_page(client, headers_for):
    headers = headers_for()
    ids = [create(client, headers, i) for i in range(15)]
    first = client.get("/applications", params={"limit": 10}, headers=headers).json()

    create(client, headers, 100)
    second = client.get(
        "/applications",
        params={"limit": 10, "cursor": first["next_cursor"]},
        headers=headers,
    ).json()

    assert [item["id"] for item in second["items"]] == list(reversed(ids[:5]))
    assert second["next_cursor"] is None


def test_same_applied_at_still_pages_correctly(client, headers_for):
    headers = headers_for()
    ids = {
        client.post(
            "/applications", json={"company_name": f"Tie {i}", "title": "SWE"}, headers=headers
        ).json()["id"]
        for i in range(5)
    }

    pages = fetch_all_pages(client, headers, limit=2)

    assert [len(page) for page in pages] == [2, 2, 1]
    assert set(sum(pages, [])) == ids


def test_items_include_company_and_title(client, headers_for):
    headers = headers_for()
    create(client, headers, 1)

    item = client.get("/applications", headers=headers).json()["items"][0]

    assert (item["company_name"], item["title"]) == ("Company 1", "SWE Intern")
    assert "events" not in item


def test_status_filter(client, headers_for):
    headers = headers_for()
    interview_id = create(client, headers, 1)
    create(client, headers, 2)
    client.post(
        f"/applications/{interview_id}/status", json={"to_status": "interview"}, headers=headers
    )

    body = client.get("/applications", params={"status": "interview"}, headers=headers).json()

    assert [item["id"] for item in body["items"]] == [interview_id]


def test_garbage_cursor_is_422(client, headers_for):
    response = client.get("/applications", params={"cursor": "not-a-cursor"}, headers=headers_for())
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_cursor"


def test_limit_above_100_is_422(client, headers_for):
    response = client.get("/applications", params={"limit": 101}, headers=headers_for())
    assert response.status_code == 422


def test_other_users_applications_are_hidden(client, headers_for):
    create(client, headers_for("sub-a"), 1)

    body = client.get("/applications", headers=headers_for("sub-b")).json()

    assert body == {"items": [], "next_cursor": None}
