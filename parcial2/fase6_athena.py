"""
fase6_athena.py
Create Athena external tables and run the required analytical queries.
"""
from __future__ import annotations

import os
import time

import boto3


REGION = os.getenv("AWS_REGION", "us-east-1")
DATABASE = os.getenv("GLUE_DATABASE", "chinook_dw")
DW_BUCKET = os.getenv("DW_BUCKET", "chinook-dw-parcial2")
ATHENA_OUTPUT = os.getenv("ATHENA_OUTPUT", "s3://chinook-athena-results/results/")
WORKGROUP = os.getenv("ATHENA_WORKGROUP", "primary")


DDL_STATEMENTS = [
    f"CREATE DATABASE IF NOT EXISTS {DATABASE} LOCATION 's3://{DW_BUCKET}/'",
    f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {DATABASE}.dim_date (
      DateKey int,
      FullDate string,
      Year int,
      Quarter int,
      Month int,
      Day int,
      DayOfWeek int,
      IsHoliday boolean
    )
    STORED AS PARQUET
    LOCATION 's3://{DW_BUCKET}/dim_date/'
    """,
    f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {DATABASE}.dim_customer (
      CustomerKey int,
      FirstName string,
      LastName string,
      Company string,
      Country string,
      City string,
      State string,
      Email string,
      EmployeeKey int,
      EmployeeName string,
      ReportsTo int
    )
    STORED AS PARQUET
    LOCATION 's3://{DW_BUCKET}/dim_customer/'
    """,
    f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {DATABASE}.dim_track (
      TrackKey int,
      Name string,
      Album string,
      Artist string,
      Genre string,
      MediaType string,
      Composer string,
      Milliseconds int,
      UnitPrice decimal(10,2)
    )
    STORED AS PARQUET
    LOCATION 's3://{DW_BUCKET}/dim_track/'
    """,
    f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {DATABASE}.fact_sales (
      CustomerKey int,
      TrackKey int,
      InvoiceDateKey int,
      EmployeeKey int,
      Quantity int,
      UnitPrice decimal(10,2),
      TotalAmount decimal(10,2)
    )
    PARTITIONED BY (year int, month int, day int)
    STORED AS PARQUET
    LOCATION 's3://{DW_BUCKET}/fact_sales/'
    """,
    f"MSCK REPAIR TABLE {DATABASE}.fact_sales",
]


ANALYTICS_QUERIES = {
    "tracks_vendidos_por_dia": """
        SELECT dd.FullDate, SUM(fs.Quantity) AS tracks_sold
        FROM fact_sales fs JOIN dim_date dd ON fs.InvoiceDateKey = dd.DateKey
        GROUP BY dd.FullDate ORDER BY dd.FullDate
    """,
    "artista_mas_vendido_por_mes": """
        SELECT dd.Year, dd.Month, dt.Artist, SUM(fs.Quantity) AS total_vendido
        FROM fact_sales fs
        JOIN dim_date dd ON fs.InvoiceDateKey = dd.DateKey
        JOIN dim_track dt ON fs.TrackKey = dt.TrackKey
        GROUP BY dd.Year, dd.Month, dt.Artist
        ORDER BY dd.Year, dd.Month, total_vendido DESC
    """,
    "dia_semana_con_mas_compras": """
        SELECT dd.DayOfWeek,
               CASE dd.DayOfWeek WHEN 0 THEN 'Lunes' WHEN 1 THEN 'Martes'
                 WHEN 2 THEN 'Miercoles' WHEN 3 THEN 'Jueves' WHEN 4 THEN 'Viernes'
                 WHEN 5 THEN 'Sabado' ELSE 'Domingo' END AS NombreDia,
               SUM(fs.Quantity) AS total_compras
        FROM fact_sales fs JOIN dim_date dd ON fs.InvoiceDateKey = dd.DateKey
        GROUP BY dd.DayOfWeek ORDER BY total_compras DESC
    """,
    "mes_con_mayor_numero_de_ventas": """
        SELECT dd.Month, SUM(fs.TotalAmount) AS total_ventas
        FROM fact_sales fs JOIN dim_date dd ON fs.InvoiceDateKey = dd.DateKey
        GROUP BY dd.Month ORDER BY total_ventas DESC
    """,
}


def run_query(athena_client, query: str, database: str | None = DATABASE) -> str:
    context = {"Database": database} if database else {}
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext=context,
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT},
        WorkGroup=WORKGROUP,
    )
    query_id = response["QueryExecutionId"]

    while True:
        execution = athena_client.get_query_execution(QueryExecutionId=query_id)
        state = execution["QueryExecution"]["Status"]["State"]
        if state in {"SUCCEEDED", "FAILED", "CANCELLED"}:
            break
        time.sleep(2)

    if state != "SUCCEEDED":
        reason = execution["QueryExecution"]["Status"].get("StateChangeReason", "No reason")
        raise RuntimeError(f"Athena query failed ({state}): {reason}")
    return query_id


def main() -> None:
    athena_client = boto3.client("athena", region_name=REGION)

    for statement in DDL_STATEMENTS:
        query_id = run_query(athena_client, statement)
        print(f"DDL completed: {query_id}")

    for name, query in ANALYTICS_QUERIES.items():
        query_id = run_query(athena_client, query)
        print(f"Analytics query '{name}' completed: {query_id}")

    print("Athena schema and analytical queries are ready.")


if __name__ == "__main__":
    main()
