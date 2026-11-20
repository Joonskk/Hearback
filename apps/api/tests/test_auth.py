import pytest
from sqlalchemy import func, select

from app.models import User


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_me_creates_user_once(client, db, make_token):
    token = make_token(sub="sub-a", email="a@example.com")
    first = client.get("/me", headers=auth(token))
    second = client.get("/me", headers=auth(token))

    assert first.status_code == 200
    assert first.json()["email"] == "a@example.com"
    assert second.json()["id"] == first.json()["id"]
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_me_without_token_is_401(client):
    response = client.get("/me")
    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "invalid_token", "message": "Missing or invalid token"}
    }


@pytest.mark.parametrize(
    "token_args",
    [{"exp_in": -10}, {"aud": "some-other-app"}, {"secret": "x" * 40}],
    ids=["expired", "wrong-audience", "wrong-secret"],
)
def test_me_rejects_bad_tokens(client, make_token, token_args):
    token = make_token(**token_args)
    response = client.get("/me", headers=auth(token))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_me_rejects_garbage_token(client):
    response = client.get("/me", headers=auth("not-a-jwt"))
    assert response.status_code == 401
