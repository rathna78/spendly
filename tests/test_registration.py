from werkzeug.security import check_password_hash

from database import db


def _post(client, **overrides):
    data = {"name": "Asha Rao", "email": "asha@example.com", "password": "secret123"}
    data.update(overrides)
    return client.post("/register", data=data)


def _count_users(email):
    conn = db.get_db()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM users WHERE email = ?", (email,)
        ).fetchone()[0]
    finally:
        conn.close()


def test_get_register_ok(client):
    assert client.get("/register").status_code == 200


def test_success_creates_hashed_user_and_redirects(client):
    resp = _post(client)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")

    user = db.get_user_by_email("asha@example.com")
    assert user is not None
    assert user["name"] == "Asha Rao"
    assert user["password_hash"] != "secret123"
    assert check_password_hash(user["password_hash"], "secret123")


def test_success_flash_shown_on_login(client):
    resp = client.post(
        "/register",
        data={"name": "A", "email": "a@example.com", "password": "secret123"},
        follow_redirects=True,
    )
    assert b"Account created" in resp.data


def test_email_is_trimmed_and_lowercased(client):
    _post(client, email="  Asha@Example.COM ")
    assert db.get_user_by_email("asha@example.com") is not None


def test_duplicate_email_rejected_case_insensitive(client):
    _post(client)
    resp = _post(client, email="ASHA@example.com")
    assert resp.status_code == 409
    assert b"already exists" in resp.data
    assert _count_users("asha@example.com") == 1


def test_invalid_email_rejected(client):
    for bad in ["nope", "a@b", "@x.com", "a@@x.com", "a b@x.com", "a@x."]:
        resp = _post(client, email=bad)
        assert resp.status_code == 400, bad


def test_short_password_rejected(client):
    resp = _post(client, password="short")
    assert resp.status_code == 400
    assert _count_users("asha@example.com") == 0


def test_empty_and_whitespace_name_rejected(client):
    assert _post(client, name="").status_code == 400
    assert _post(client, name="   ").status_code == 400


def test_overlong_name_rejected(client):
    assert _post(client, name="x" * 101).status_code == 400


def test_error_preserves_fields_but_not_password(client):
    resp = _post(client, password="short")
    body = resp.data.decode()
    assert 'value="Asha Rao"' in body
    assert 'value="asha@example.com"' in body
    assert "short" not in body.replace("Min. 8 characters", "").replace("at least 8", "")


def test_demo_user_still_exists(client):
    assert db.get_user_by_email("demo@spendly.com") is not None
