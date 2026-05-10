# Data Warehouse Module

This directory contains the AWS data engineering layer for the Chinook Cloud
Data Platform. It builds an analytical star schema from the transactional RDS
PostgreSQL database and publishes query-ready datasets to S3 and Athena.

## Pipeline

1. `01_setup_s3.py` creates the S3 buckets and dataset prefixes.
2. `02_setup_glue.py` creates the Glue database, RDS connection, and Secrets Manager entry.
3. `03_load_dim_date.py` generates `dim_date` for 2000-2030 with Colombian holidays.
4. `04_register_sales_etl.py` uploads and registers Glue jobs for `dim_customer`, `dim_track`, and `fact_sales`.
5. `05_setup_athena.py` creates Athena external tables, repairs partitions, and runs analytics queries.
6. `inspect_dw.py` provides quick validation for S3 outputs and Glue catalog tables.

## Outputs

```text
s3://chinook-dw-parcial2/dim_date/
s3://chinook-dw-parcial2/dim_customer/
s3://chinook-dw-parcial2/dim_track/
s3://chinook-dw-parcial2/fact_sales/year=.../month=.../day=.../
```

## Configuration

The scripts use conservative defaults for the deployed demo environment and can
be adjusted through environment variables:

- `AWS_REGION`
- `DW_BUCKET`
- `ATHENA_OUTPUT`
- `GLUE_DATABASE`
- `GLUE_CONNECTION_NAME`
- `GLUE_ROLE_ARN`
- `RDS_ENDPOINT`
- `RDS_DB_NAME`
- `RDS_USERNAME`
- `RDS_PASSWORD`

Do not commit real AWS credentials, database passwords, private keys, or local
lab account exports.

## Validation

```bash
pytest tests/test_etl.py -v
```
