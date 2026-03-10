from fastapi.testclient import TestClient

from app.main import app
from app.db import get_conn
import app.main as mainmod


class DummyConn:
    def cursor(self):
        raise RuntimeError("Cursor should not be used in mocked auth tests")

    def commit(self):
        return None


def override_conn():
    return DummyConn()


client = TestClient(app)


def setup_function():
    app.dependency_overrides[get_conn] = override_conn


def teardown_function():
    app.dependency_overrides.clear()


def test_register_user(monkeypatch):
    monkeypatch.setattr(mainmod, "get_user_by_email", lambda conn, email: None)
    monkeypatch.setattr(
        mainmod,
        "create_user_record",
        lambda conn, full_name, email, password, role: {
            "user_id": 1,
            "full_name": full_name,
            "email": email,
            "password_hash": "hash",
            "role": role,
            "is_active": True,
        },
    )

    response = client.post(
        "/auth/register",
        json={"full_name": "User One", "email": "user1@test.com", "password": "secret123"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "user"


def test_login_ok(monkeypatch):
    user_row = {
        "user_id": 2,
        "full_name": "Admin",
        "email": "admin@test.com",
        "password_hash": "fake-hash",
        "role": "admin",
        "is_active": True,
    }

    monkeypatch.setattr(mainmod, "get_user_by_email", lambda conn, email: user_row)
    monkeypatch.setattr(mainmod, "verify_password", lambda plain, hashed: True)

    response = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "secret123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["user"]["role"] == "admin"


def test_me_ok(monkeypatch):
    token = mainmod.create_access_token({"sub": "7", "role": "user"})
    monkeypatch.setattr(
        mainmod,
        "get_user_by_id",
        lambda conn, user_id: {
            "user_id": 7,
            "full_name": "User Seven",
            "email": "user7@test.com",
            "password_hash": "hash",
            "role": "user",
            "is_active": True,
        },
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "user7@test.com"


def test_admin_list_requires_admin(monkeypatch):
    token = mainmod.create_access_token({"sub": "3", "role": "user"})
    monkeypatch.setattr(
        mainmod,
        "get_user_by_id",
        lambda conn, user_id: {
            "user_id": 3,
            "full_name": "Normal User",
            "email": "normal@test.com",
            "password_hash": "hash",
            "role": "user",
            "is_active": True,
        },
    )

    response = client.get("/auth/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_bootstrap_admin(monkeypatch):
    monkeypatch.setattr(mainmod, "count_admins", lambda conn: 0)
    monkeypatch.setattr(mainmod, "get_user_by_email", lambda conn, email: None)
    monkeypatch.setattr(
        mainmod,
        "create_user_record",
        lambda conn, full_name, email, password, role: {
            "user_id": 10,
            "full_name": full_name,
            "email": email,
            "password_hash": "hash",
            "role": role,
            "is_active": True,
        },
    )

    response = client.post(
        "/auth/bootstrap-admin",
        json={"full_name": "First Admin", "email": "firstadmin@test.com", "password": "secret123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["role"] == "admin"
    assert "access_token" in body
