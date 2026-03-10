from decimal import Decimal


def _rows_to_dicts(cur, rows):
    result = []

    for row in rows:
        if isinstance(row, dict):
            item = dict(row)
        else:
            columns = [desc[0] for desc in cur.description]
            item = dict(zip(columns, row))

        for key in ("price", "total"):
            if key in item and isinstance(item[key], Decimal):
                item[key] = float(item[key])

        result.append(item)

    return result


def search_tracks(conn, q: str, limit: int = 50):
    limit = max(1, min(int(limit), 100))
    term = f"%{q}%"

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                t.track_id,
                t.name AS track,
                ar.name AS artist,
                g.name AS genre,
                t.unit_price AS price
            FROM track t
            LEFT JOIN album al
                ON al.album_id = t.album_id
            LEFT JOIN artist ar
                ON ar.artist_id = al.artist_id
            LEFT JOIN genre g
                ON g.genre_id = t.genre_id
            WHERE
                t.name ILIKE %s
                OR ar.name ILIKE %s
                OR g.name ILIKE %s
            ORDER BY ar.name NULLS LAST, t.name
            LIMIT %s
            """,
            (term, term, term, limit),
        )
        rows = cur.fetchall()
        return _rows_to_dicts(cur, rows)


def get_customer_summary(conn, customer_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                c.customer_id,
                c.first_name || ' ' || c.last_name AS name,
                c.email,
                c.country,
                COALESCE(SUM(i.total), 0) AS total,
                COUNT(DISTINCT i.invoice_id) AS invoices
            FROM customer c
            LEFT JOIN invoice i
                ON i.customer_id = c.customer_id
            WHERE c.customer_id = %s
            GROUP BY
                c.customer_id,
                c.first_name,
                c.last_name,
                c.email,
                c.country
            """,
            (int(customer_id),),
        )
        row = cur.fetchone()
        if not row:
            return None

        item = _rows_to_dicts(cur, [row])[0]
        item["customer_id"] = int(item["customer_id"])
        item["invoices"] = int(item["invoices"])
        return item


def purchase_track(conn, customer_id: int, track_id: int, quantity: int = 1):
    quantity = int(quantity)
    if quantity < 1:
        raise ValueError("quantity must be >= 1")

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT address, city, state, country, postal_code
                FROM customer
                WHERE customer_id = %s
                """,
                (int(customer_id),),
            )
            customer = cur.fetchone()
            if not customer:
                raise ValueError("customer not found")

            if isinstance(customer, dict):
                address = customer["address"]
                city = customer["city"]
                state = customer["state"]
                country = customer["country"]
                postal_code = customer["postal_code"]
            else:
                address, city, state, country, postal_code = customer

            cur.execute(
                """
                SELECT name, unit_price
                FROM track
                WHERE track_id = %s
                """,
                (int(track_id),),
            )
            track = cur.fetchone()
            if not track:
                raise ValueError("track not found")

            if isinstance(track, dict):
                track_name = track["name"]
                unit_price = float(track["unit_price"])
            else:
                track_name, unit_price = track
                unit_price = float(unit_price)

            total = unit_price * quantity

            cur.execute("SELECT COALESCE(MAX(invoice_id), 0) + 1 AS next_id FROM invoice")
            invoice_id_row = cur.fetchone()
            invoice_id = invoice_id_row["next_id"] if isinstance(invoice_id_row, dict) else invoice_id_row[0]

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
                VALUES (%s, %s, NOW(), %s, %s, %s, %s, %s, %s)
                """,
                (
                    invoice_id,
                    int(customer_id),
                    address,
                    city,
                    state,
                    country,
                    postal_code,
                    total,
                ),
            )

            cur.execute("SELECT COALESCE(MAX(invoice_line_id), 0) + 1 AS next_id FROM invoice_line")
            invoice_line_id_row = cur.fetchone()
            invoice_line_id = invoice_line_id_row["next_id"] if isinstance(invoice_line_id_row, dict) else invoice_line_id_row[0]

            cur.execute(
                """
                INSERT INTO invoice_line (
                    invoice_line_id,
                    invoice_id,
                    track_id,
                    unit_price,
                    quantity
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    invoice_line_id,
                    invoice_id,
                    int(track_id),
                    unit_price,
                    quantity,
                ),
            )

        conn.commit()

        return {
            "ok": True,
            "invoice_id": int(invoice_id),
            "invoice_line_id": int(invoice_line_id),
            "customer_id": int(customer_id),
            "track_id": int(track_id),
            "track": track_name,
            "quantity": int(quantity),
            "unit_price": float(unit_price),
            "total": float(total),
        }
    except Exception:
        conn.rollback()
        raise
