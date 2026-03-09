from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.db import get_conn

client = TestClient(app)

def override_conn():
    class DummyConn:
        def cursor(self): raise RuntimeError("should not hit real DB in unit tests")
    yield DummyConn()

app.dependency_overrides[get_conn] = override_conn

def test_search_validation_param_missing():
    r = client.get("/search")
    assert r.status_code == 422

def test_search_ok_mocked():
    with patch("app.services.search_tracks", return_value=[{"trackid":1,"track":"x","artist":"y","genre":"z","unitprice":0.99}]):
        r = client.get("/search", params={"q":"x"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

def test_purchase_validation():
    r = client.post("/purchase", json={})
    assert r.status_code == 400

def test_purchase_ok_mocked():
    with patch("app.services.purchase_track", return_value={"invoice_id": 123, "total": 1.98}):
        r = client.post("/purchase", json={"customer_id":1, "track_id":2, "quantity":2})
        assert r.status_code == 200
        assert r.json()["invoice_id"] == 123
