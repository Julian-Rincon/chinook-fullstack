"""
fase3_etl_dim_date.py
Generate DimDate for the Chinook Data Warehouse.

This script can run as an AWS Glue PySpark job. When executed locally without
Spark, it validates the date-generation logic and prints a small sample.
"""
from __future__ import annotations

import os
from datetime import date, timedelta


START_DATE = date(2000, 1, 1)
END_DATE = date(2030, 12, 31)
OUTPUT_PATH = os.getenv("DIM_DATE_OUTPUT_PATH", "s3://chinook-dw-parcial2/dim_date/")


def colombian_holidays(years: range) -> set[date]:
    try:
        import holidays

        return set(holidays.country_holidays("CO", years=years).keys())
    except Exception:
        # Glue can install holidays as an additional Python module. Local dry
        # runs still work and mark IsHoliday as False if it is unavailable.
        return set()


def iter_dates(start: date = START_DATE, end: date = END_DATE):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def build_rows() -> list[dict]:
    holiday_dates = colombian_holidays(range(START_DATE.year, END_DATE.year + 1))
    rows = []
    for current in iter_dates():
        rows.append(
            {
                "DateKey": int(current.strftime("%Y%m%d")),
                "FullDate": current.isoformat(),
                "Year": current.year,
                "Quarter": (current.month - 1) // 3 + 1,
                "Month": current.month,
                "Day": current.day,
                "DayOfWeek": current.weekday(),
                "IsHoliday": current in holiday_dates,
            }
        )
    return rows


def write_with_spark(rows: list[dict], output_path: str) -> None:
    from pyspark.sql import SparkSession
    from pyspark.sql.types import BooleanType, IntegerType, StringType, StructField, StructType

    spark = SparkSession.builder.appName("etl-dim-date").getOrCreate()
    schema = StructType(
        [
            StructField("DateKey", IntegerType(), False),
            StructField("FullDate", StringType(), False),
            StructField("Year", IntegerType(), False),
            StructField("Quarter", IntegerType(), False),
            StructField("Month", IntegerType(), False),
            StructField("Day", IntegerType(), False),
            StructField("DayOfWeek", IntegerType(), False),
            StructField("IsHoliday", BooleanType(), False),
        ]
    )
    dataframe = spark.createDataFrame(rows, schema=schema)
    dataframe.coalesce(1).write.mode("overwrite").parquet(output_path)
    spark.stop()


def main() -> None:
    rows = build_rows()
    try:
        write_with_spark(rows, OUTPUT_PATH)
        print(f"Wrote {len(rows)} DimDate rows to {OUTPUT_PATH}")
    except ModuleNotFoundError:
        print("PySpark is not installed; local dry run completed.")
        print(f"Generated {len(rows)} DimDate rows. Sample: {rows[:3]}")


if __name__ == "__main__":
    main()
