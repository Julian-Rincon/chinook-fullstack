from fastapi.testclient import TestClient

from app.main import app
from app.db import get_conn
from app import services
import app.main as mainmod


class DummyCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, *args, **kwargs):
        return None

    def fetchone(self):
        return (1,)


class DummyConn:
    def cursor(self):
        return DummyCursor()

    def commit(self):
        return None


def override_conn():
    return DummyConn()


client = TestClient(app)


def setup_function():
    app.dependency_overrides[get_conn] = override_conn


def teardown_function():
    app.dependency_overrides.clear()


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "db": 1}


def test_search_validation_param_missing():
    response = client.get("/search")
    assert response.status_code == 422


def test_search_ok_mocked(monkeypatch):
    monkeypatch.setattr(
        services,
        "search_tracks",
        lambda conn, q, limit: [
            {"track_id": 1, "track": "Song", "artist": "Artist", "genre": "Rock", "price": 0.99}
        ],
    )
    response = client.get("/search?q=rock")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["track"] == "Song"


def test_customer_ok_mocked(monkeypatch):
    monkeypatch.setattr(
        services,
        "get_customer_summary",
        lambda conn, customer_id: {
            "customer_id": 1,
            "name": "Luis",
            "email": "luis@example.com",
            "country": "Brazil",
            "total": 10.5,
            "invoices": 2,
        },
    )
    response = client.get("/customer/1")
    assert response.status_code == 200
    assert response.json()["customer_id"] == 1


def test_purchase_requires_auth():
    response = client.post("/purchase", json={"customer_id": 1, "track_id": 2, "quantity": 1})
    assert response.status_code == 401


def test_purchase_ok_mocked(monkeypatch):
    monkeypatch.setattr(
        mainmod,
        "get_user_by_id",
        lambda conn, user_id: {
            "user_id": 1,
            "full_name": "User",
            "email": "user@test.com",
            "password_hash": "x",
            "role": "user",
            "is_active": True,
        },
    )
    monkeypatch.setattr(
        services,
        "purchase_track",
        lambda conn, customer_id, track_id, quantity: {
            "ok": True,
            "invoice_id": 10,
            "customer_id": customer_id,
            "track_id": track_id,
            "quantity": quantity,
            "total": 0.99,
        },
    )

    token = mainmod.create_access_token({"sub": "1", "role": "user"})
    response = client.post(
        "/purchase",
        json={"customer_id": 1, "track_id": 2, "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
