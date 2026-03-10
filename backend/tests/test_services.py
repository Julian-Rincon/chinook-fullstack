from decimal import Decimal

from app.services import _rows_to_dicts


class FakeCursor:
    description = [("track",), ("price",), ("artist",), ("total",)]


def test_rows_to_dicts_with_tuple_rows():
    rows = [("Song A", Decimal("0.99"), "Artist A", Decimal("10.50"))]
    result = _rows_to_dicts(FakeCursor(), rows)

    assert result == [
        {"track": "Song A", "price": 0.99, "artist": "Artist A", "total": 10.5}
    ]


def test_rows_to_dicts_with_dict_rows():
    rows = [{"track": "Song B", "price": Decimal("1.99"), "artist": "Artist B", "total": Decimal("4.20")}]
    result = _rows_to_dicts(FakeCursor(), rows)

    assert result == [
        {"track": "Song B", "price": 1.99, "artist": "Artist B", "total": 4.2}
    ]
