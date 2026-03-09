from fastapi import HTTPException

def search_tracks(conn, q: str, limit: int = 50):
    pattern = f"%{q}%"
    sql = """
    SELECT
      t.trackid,
      t.name AS track,
      ar.name AS artist,
      g.name AS genre,
      t.unitprice
    FROM track t
      JOIN album al ON t.albumid = al.albumid
      JOIN artist ar ON al.artistid = ar.artistid
      LEFT JOIN genre g ON t.genreid = g.genreid
    WHERE
      t.name ILIKE %s OR ar.name ILIKE %s OR g.name ILIKE %s
    ORDER BY t.name
    LIMIT %s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (pattern, pattern, pattern, limit))
        return cur.fetchall()

def purchase_track(conn, customer_id: int, track_id: int, quantity: int = 1):
    if quantity < 1:
        raise HTTPException(status_code=400, detail="quantity must be >= 1")

    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM customer WHERE customerid=%s", (customer_id,))
            customer = cur.fetchone()
            if not customer:
                raise HTTPException(status_code=404, detail="customer not found")

            cur.execute("SELECT trackid, unitprice FROM track WHERE trackid=%s", (track_id,))
            track = cur.fetchone()
            if not track:
                raise HTTPException(status_code=404, detail="track not found")

            unit_price = float(track["unitprice"])
            total = unit_price * int(quantity)

            cur.execute(
                """
                INSERT INTO invoice
                  (customerid, invoicedate, billingaddress, billingcity, billingstate,
                   billingcountry, billingpostalcode, total)
                VALUES
                  (%s, NOW(), %s, %s, %s, %s, %s, %s)
                RETURNING invoiceid;
                """,
                (
                    customer_id,
                    customer.get("address"),
                    customer.get("city"),
                    customer.get("state"),
                    customer.get("country"),
                    customer.get("postalcode"),
                    total,
                ),
            )
            invoice_id = cur.fetchone()["invoiceid"]

            cur.execute(
                """
                INSERT INTO invoice_line (invoiceid, trackid, unitprice, quantity)
                VALUES (%s, %s, %s, %s);
                """,
                (invoice_id, track_id, unit_price, quantity),
            )

            return {"invoice_id": int(invoice_id), "total": float(total)}
