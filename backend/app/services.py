from decimal import Decimal


def _rows_to_dicts(cur, rows):
    items = []

    for row in rows:
        if isinstance(row, dict):
            item = dict(row)
        else:
            columns = [col[0] for col in cur.description]
            item = dict(zip(columns, row))

        if "price" in item and isinstance(item["price"], Decimal):
            item["price"] = float(item["price"])

        if "unit_price" in item and isinstance(item["unit_price"], Decimal):
            item["unit_price"] = float(item["unit_price"])

        if "total" in item and isinstance(item["total"], Decimal):
            item["total"] = float(item["total"])

        items.append(item)

    return items


def search_tracks(conn, q: str, limit: int = 20):
    sql = """
    SELECT
        t.track_id,
        t.name AS track,
        ar.name AS artist,
        g.name AS genre,
        t.unit_price AS price
    FROM track t
    LEFT JOIN album al ON al.album_id = t.album_id
    LEFT JOIN artist ar ON ar.artist_id = al.artist_id
    LEFT JOIN genre g ON g.genre_id = t.genre_id
    WHERE t.name ILIKE %(term)s
       OR ar.name ILIKE %(term)s
       OR g.name ILIKE %(term)s
    ORDER BY ar.name NULLS LAST, t.name
    LIMIT %(limit)s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"term": f"%{q}%", "limit": limit})
        rows = cur.fetchall()
        return _rows_to_dicts(cur, rows)


def get_customer_summary(conn, customer_id: int):
    sql = """
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS name,
        c.email,
        c.country,
        COALESCE(SUM(i.total), 0) AS total,
        COUNT(DISTINCT i.invoice_id) AS invoices
    FROM customer c
    LEFT JOIN invoice i ON i.customer_id = c.customer_id
    WHERE c.customer_id = %(customer_id)s
    GROUP BY
        c.customer_id,
        c.first_name,
        c.last_name,
        c.email,
        c.country;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"customer_id": customer_id})
        row = cur.fetchone()
        if not row:
            return None
        return _rows_to_dicts(cur, [row])[0]


def purchase_track(conn, customer_id: int, track_id: int, quantity: int = 1):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT customer_id, billing_address, billing_city, billing_state,
                   billing_country, billing_postal_code
            FROM customer
            WHERE customer_id = %(customer_id)s
            """,
            {"customer_id": customer_id},
        )
        customer = cur.fetchone()
        if not customer:
            raise ValueError("Customer not found")

        cur.execute(
            """
            SELECT track_id, name, unit_price
            FROM track
            WHERE track_id = %(track_id)s
            """,
            {"track_id": track_id},
        )
        track = cur.fetchone()
        if not track:
            raise ValueError("Track not found")

        unit_price = float(track["unit_price"])
        total = round(unit_price * quantity, 2)

        cur.execute("SELECT COALESCE(MAX(invoice_id), 0) + 1 AS next_id FROM invoice")
        invoice_id = cur.fetchone()["next_id"]

        cur.execute("SELECT COALESCE(MAX(invoice_line_id), 0) + 1 AS next_id FROM invoice_line")
        invoice_line_id = cur.fetchone()["next_id"]

        cur.execute(
            """
            INSERT INTO invoice (
                invoice_id,
                customer_id,
                invoice_date,
                billing_address,
                billing_city,
                billing_state,
                billing_country,
                billing_postal_code,
                total
            )
            VALUES (
                %(invoice_id)s,
                %(customer_id)s,
                CURRENT_TIMESTAMP,
                %(billing_address)s,
                %(billing_city)s,
                %(billing_state)s,
                %(billing_country)s,
                %(billing_postal_code)s,
                %(total)s
            )
            """,
            {
                "invoice_id": invoice_id,
                "customer_id": customer_id,
                "billing_address": customer["billing_address"],
                "billing_city": customer["billing_city"],
                "billing_state": customer["billing_state"],
                "billing_country": customer["billing_country"],
                "billing_postal_code": customer["billing_postal_code"],
                "total": total,
            },
        )

        cur.execute(
            """
            INSERT INTO invoice_line (
                invoice_line_id,
                invoice_id,
                track_id,
                unit_price,
                quantity
            )
            VALUES (
                %(invoice_line_id)s,
                %(invoice_id)s,
                %(track_id)s,
                %(unit_price)s,
                %(quantity)s
            )
            """,
            {
                "invoice_line_id": invoice_line_id,
                "invoice_id": invoice_id,
                "track_id": track_id,
                "unit_price": unit_price,
                "quantity": quantity,
            },
        )

    conn.commit()

    return {
        "ok": True,
        "invoice_id": invoice_id,
        "invoice_line_id": invoice_line_id,
        "customer_id": customer_id,
        "track_id": track_id,
        "track": track["name"],
        "quantity": quantity,
        "unit_price": unit_price,
        "total": total,
    }
