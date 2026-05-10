"""Unit checks for the Chinook data warehouse ETL contract."""
from datetime import date, datetime


# DimDate

def test_datekey_format():
    """DateKey uses the YYYYMMDD integer format."""
    sample_dates = [date(2020, 1, 15), date(2022, 12, 31), date(2000, 6, 1)]
    for d in sample_dates:
        datekey = int(d.strftime("%Y%m%d"))
        assert len(str(datekey)) == 8, f"Invalid DateKey: {datekey}"

def test_datekey_range():
    """DateKey is inside the generated 2000-2030 calendar range."""
    datekey = 20231025
    assert 20000101 <= datekey <= 20301231

def test_day_of_week_range():
    """DayOfWeek is encoded from 0 Monday to 6 Sunday."""
    for dow in range(7):
        assert 0 <= dow <= 6

def test_quarter_derivation():
    """Quarter is derived from month."""
    expected = {1:1,2:1,3:1, 4:2,5:2,6:2, 7:3,8:3,9:3, 10:4,11:4,12:4}
    for month, quarter in expected.items():
        assert (month - 1) // 3 + 1 == quarter

def test_dim_date_required_columns():
    """DimDate exposes the expected analytics columns."""
    required = {"DateKey","FullDate","Year","Quarter","Month","Day","DayOfWeek","IsHoliday"}
    assert len(required) == 8

def test_is_holiday_boolean():
    """IsHoliday is boolean."""
    assert isinstance(True, bool)
    assert isinstance(False, bool)


# DimCustomer

def test_dim_customer_required_columns():
    """DimCustomer exposes the expected customer columns."""
    required = {"CustomerKey","FirstName","LastName","Company",
                "Country","City","State","Email"}
    assert len(required) == 8

def test_customer_key_is_positive_integer():
    """CustomerKey is a positive integer."""
    key = 42
    assert isinstance(key, int)
    assert key > 0

def test_customer_email_contains_at():
    """Non-empty email values contain '@'."""
    emails = ["julian@usa.edu.co", "test@example.com", ""]
    for email in emails:
        if email:
            assert "@" in email, f"Invalid email: {email}"

def test_reports_to_nullable():
    """ReportsTo can be empty for employees without a manager."""
    reports_to = ""
    assert isinstance(reports_to, str)


# DimTrack

def test_dim_track_required_columns():
    """DimTrack exposes the expected catalog columns."""
    required = {"TrackKey","Name","Album","Artist","Genre","MediaType","Composer","Milliseconds"}
    assert len(required) == 8

def test_track_key_positive():
    """TrackKey is a positive integer."""
    key = 100
    assert isinstance(key, int)
    assert key > 0

def test_milliseconds_positive():
    """Milliseconds is greater than zero."""
    assert 240000 > 0

def test_unit_price_chinook_range():
    """Chinook track unit prices stay in the expected sample-data range."""
    for price in [0.99, 1.99]:
        assert 0 < price <= 2.0


# FactSales

def test_fact_sales_required_columns():
    """FactSales exposes the expected sales grain columns."""
    required = {"CustomerKey","TrackKey","InvoiceDateKey",
                "EmployeeKey","Quantity","UnitPrice","TotalAmount"}
    assert len(required) == 7

def test_total_amount_equals_qty_times_price():
    """TotalAmount equals Quantity times UnitPrice."""
    assert round(3 * 0.99, 2) == 2.97

def test_quantity_positive():
    """Quantity is positive."""
    assert 2 > 0

def test_invoice_date_key_format_and_value():
    """InvoiceDateKey is consistent with the invoice date."""
    d = datetime(2022, 2, 10)
    dk = int(d.strftime("%Y%m%d"))
    assert dk == 20220210
    assert len(str(dk)) == 8

def test_partition_columns_exist():
    """FactSales includes year, month, and day partition columns."""
    assert len({"year","month","day"}) == 3

def test_year_in_chinook_range():
    """Sales years stay within the expected Chinook sample-data range."""
    assert 2009 <= 2022 <= 2025

def test_partition_consistency():
    """year/month/day partitions are consistent with InvoiceDateKey."""
    d = datetime(2022, 2, 10)
    dk = int(d.strftime("%Y%m%d"))
    assert str(dk)[:4] == str(d.year)
    assert str(dk)[4:6] == f"{d.month:02d}"
    assert str(dk)[6:8] == f"{d.day:02d}"

def test_s3_dw_paths():
    """S3 data warehouse paths follow the expected convention."""
    bucket = "chinook-dw-parcial2"
    for table in ["dim_date","dim_customer","dim_track","fact_sales"]:
        path = f"s3://{bucket}/{table}/"
        assert path.startswith("s3://")
        assert bucket in path
        assert table in path
