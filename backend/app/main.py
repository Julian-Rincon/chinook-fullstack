from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .db import get_conn
from . import services

app = FastAPI(title="Chinook API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health(conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT 1;")
        cur.fetchone()
    return {"ok": True, "db": 1}


@app.get("/search")
def search(q: str, limit: int = 50, conn=Depends(get_conn)):
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="q is required")
    return services.search_tracks(conn, q.strip(), limit)


@app.get("/customer/{customer_id}")
def customer(customer_id: int, conn=Depends(get_conn)):
    data = services.get_customer_summary(conn, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail="customer not found")
    return data


@app.post("/purchase")
def purchase(payload: dict, conn=Depends(get_conn)):
    if "customer_id" not in payload or "track_id" not in payload:
        raise HTTPException(status_code=400, detail="customer_id and track_id are required")

    customer_id = int(payload["customer_id"])
    track_id = int(payload["track_id"])
    quantity = int(payload.get("quantity", 1))

    try:
        return services.purchase_track(conn, customer_id, track_id, quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
