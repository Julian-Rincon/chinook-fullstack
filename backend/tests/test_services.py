from decimal import Decimal

from app.services import _rows_to_dicts


class FakeCursor:
    description = [("track",), ("price",), ("artist",)]


def test_rows_to_dicts_with_tuple_rows():
    rows = [("Song A", Decimal("0.99"), "Artist A")]
    result = _rows_to_dicts(FakeCursor(), rows)

    assert result == [
        {"track": "Song A", "price": 0.99, "artist": "Artist A"}
    ]


def test_rows_to_dicts_with_dict_rows():
    rows = [{"track": "Song B", "price": Decimal("1.99"), "artist": "Artist B"}]
    result = _rows_to_dicts(FakeCursor(), rows)

    assert result == [
        {"track": "Song B", "price": 1.99, "artist": "Artist B"}
    ]
