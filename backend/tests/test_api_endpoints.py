from fastapi.testclient import TestClient

from app.db import get_conn
from app.main import app
from app import services


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


def test_search_endpoint(monkeypatch):
    monkeypatch.setattr(
        services,
        "search_tracks",
        lambda conn, q, limit: [
            {"track_id": 1, "track": "Song", "artist": "Artist", "genre": "Rock", "price": 0.99}
        ],
    )

    response = client.get("/search", params={"q": "rock"})
    assert response.status_code == 200
    assert response.json()[0]["track"] == "Song"


def test_customer_endpoint(monkeypatch):
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


def test_purchase_endpoint(monkeypatch):
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

    response = client.post(
        "/purchase",
        json={"customer_id": 1, "track_id": 2, "quantity": 1},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
