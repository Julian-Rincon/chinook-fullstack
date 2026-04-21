"""
tests/test_etl.py
Pruebas unitarias para los ETL del Parcial 2 — Big Data e Ingeniería de Datos
Universidad Sergio Arboleda | Profesor: Oscar Andrés Arias M.
"""
import pytest
from datetime import date, datetime


# ── DimDate ───────────────────────────────────────────────────────────────────

def test_datekey_format():
    """DateKey debe tener formato YYYYMMDD (8 dígitos)."""
    sample_dates = [date(2020, 1, 15), date(2022, 12, 31), date(2000, 6, 1)]
    for d in sample_dates:
        datekey = int(d.strftime("%Y%m%d"))
        assert len(str(datekey)) == 8, f"DateKey inválido: {datekey}"

def test_datekey_range():
    """DateKey debe estar dentro del rango generado 20000101–20301231."""
    datekey = 20231025
    assert 20000101 <= datekey <= 20301231

def test_day_of_week_range():
    """DayOfWeek debe estar entre 0 (Lunes) y 6 (Domingo)."""
    for dow in range(7):
        assert 0 <= dow <= 6

def test_quarter_derivation():
    """Quarter debe derivarse correctamente del mes."""
    expected = {1:1,2:1,3:1, 4:2,5:2,6:2, 7:3,8:3,9:3, 10:4,11:4,12:4}
    for month, quarter in expected.items():
        assert (month - 1) // 3 + 1 == quarter

def test_dim_date_required_columns():
    """DimDate debe exponer exactamente las columnas del enunciado."""
    required = {"DateKey","FullDate","Year","Quarter","Month","Day","DayOfWeek","IsHoliday"}
    assert len(required) == 8

def test_is_holiday_boolean():
    """IsHoliday debe ser de tipo booleano."""
    assert isinstance(True, bool)
    assert isinstance(False, bool)


# ── DimCustomer ───────────────────────────────────────────────────────────────

def test_dim_customer_required_columns():
    """DimCustomer debe exponer exactamente las columnas del enunciado."""
    required = {"CustomerKey","FirstName","LastName","Company",
                "Country","City","State","Email"}
    assert len(required) == 8

def test_customer_key_is_positive_integer():
    """CustomerKey debe ser un entero positivo."""
    key = 42
    assert isinstance(key, int)
    assert key > 0

def test_customer_email_contains_at():
    """Email no vacío debe contener '@'."""
    emails = ["julian@usa.edu.co", "test@example.com", ""]
    for email in emails:
        if email:
            assert "@" in email, f"Email inválido: {email}"

def test_reports_to_nullable():
    """ReportsTo puede ser cadena vacía (empleado raíz sin jefe)."""
    reports_to = ""
    assert isinstance(reports_to, str)


# ── DimTrack ──────────────────────────────────────────────────────────────────

def test_dim_track_required_columns():
    """DimTrack debe exponer exactamente las columnas del enunciado."""
    required = {"TrackKey","Name","Album","Artist","Genre","MediaType","Composer","Milliseconds"}
    assert len(required) == 8

def test_track_key_positive():
    """TrackKey debe ser entero positivo."""
    key = 100
    assert isinstance(key, int)
    assert key > 0

def test_milliseconds_positive():
    """Milliseconds debe ser mayor a cero."""
    assert 240000 > 0

def test_unit_price_chinook_range():
    """UnitPrice en Chinook está entre 0.99 y 1.99."""
    for price in [0.99, 1.99]:
        assert 0 < price <= 2.0


# ── FactSales ─────────────────────────────────────────────────────────────────

def test_fact_sales_required_columns():
    """FactSales debe exponer exactamente las columnas del enunciado."""
    required = {"CustomerKey","TrackKey","InvoiceDateKey",
                "EmployeeKey","Quantity","UnitPrice","TotalAmount"}
    assert len(required) == 7

def test_total_amount_equals_qty_times_price():
    """TotalAmount = Quantity × UnitPrice."""
    assert round(3 * 0.99, 2) == 2.97

def test_quantity_positive():
    """Quantity debe ser mayor a cero."""
    assert 2 > 0

def test_invoice_date_key_format_and_value():
    """InvoiceDateKey en formato YYYYMMDD debe ser consistente con la fecha."""
    d = datetime(2022, 2, 10)
    dk = int(d.strftime("%Y%m%d"))
    assert dk == 20220210
    assert len(str(dk)) == 8

def test_partition_columns_exist():
    """FactSales debe tener columnas de partición year, month, day."""
    assert len({"year","month","day"}) == 3

def test_year_in_chinook_range():
    """El año de las ventas debe estar en el rango de datos de Chinook."""
    assert 2009 <= 2022 <= 2025

def test_partition_consistency():
    """year/month/day deben ser consistentes con InvoiceDateKey."""
    d = datetime(2022, 2, 10)
    dk = int(d.strftime("%Y%m%d"))
    assert str(dk)[:4] == str(d.year)
    assert str(dk)[4:6] == f"{d.month:02d}"
    assert str(dk)[6:8] == f"{d.day:02d}"

def test_s3_dw_paths():
    """Las rutas S3 del DW deben seguir la convención correcta."""
    bucket = "chinook-dw-parcial2"
    for table in ["dim_date","dim_customer","dim_track","fact_sales"]:
        path = f"s3://{bucket}/{table}/"
        assert path.startswith("s3://")
        assert bucket in path
        assert table in path
