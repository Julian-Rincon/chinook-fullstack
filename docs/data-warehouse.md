# Data Warehouse Guide

This guide documents the analytical layer of the Chinook Cloud Data Platform.
It assumes the transactional PostgreSQL database is already running in Amazon
RDS and contains the Chinook schema.

## Target Architecture

```text
Amazon RDS PostgreSQL
  source tables:
  customer, employee, invoice, invoice_line, track, album, artist, genre, media_type

AWS Glue
  JDBC connection to private RDS
  Spark ETL jobs

Amazon S3
  Parquet datasets:
  dim_date, dim_customer, dim_track, fact_sales

AWS Athena
  external tables over S3
  business analytics queries

Power BI
  Athena ODBC connection
  executive dashboard
```

## Star Schema

| Table | Grain | Purpose |
| --- | --- | --- |
| `dim_date` | One row per calendar date | Date attributes for trend, weekday, month, quarter, year, and holiday analysis |
| `dim_customer` | One row per customer | Customer geography and support representative context |
| `dim_track` | One row per track | Catalog metadata for track, album, artist, genre, media type, and price |
| `fact_sales` | One row per invoice line | Sales quantity, unit price, total amount, customer, track, employee, and invoice date |

`fact_sales` is partitioned by `year`, `month`, and `day` because the main
analytics are date-oriented and Athena can prune partitions during scans.

## Runtime Configuration

The scripts in `data_warehouse/` provide defaults for the deployed demo environment,
but production values should be injected through environment variables:

| Variable | Purpose |
| --- | --- |
| `AWS_REGION` | AWS region for S3, Glue, Athena, and STS clients |
| `DW_BUCKET` | S3 bucket that stores Parquet datasets and Glue scripts |
| `ATHENA_OUTPUT` | S3 location for Athena query results |
| `ATHENA_WORKGROUP` | Athena workgroup, defaults to `primary` |
| `GLUE_DATABASE` | Glue Data Catalog database for external tables |
| `GLUE_CONNECTION_NAME` | Glue JDBC connection name for RDS |
| `GLUE_ROLE_ARN` | IAM role used by Glue jobs |
| `RDS_ENDPOINT` | PostgreSQL RDS endpoint |
| `RDS_DB_NAME` | Transactional database name |
| `RDS_USERNAME` | Database username |
| `RDS_PASSWORD` | Database password |

Never commit `.env` files, exported lab credentials, private keys, or database
passwords.

## Execution Order

Run from the repository root:

```bash
pip install -r data_warehouse/requirements.txt

python data_warehouse/01_setup_s3.py
python data_warehouse/02_setup_glue.py
python data_warehouse/03_load_dim_date.py
python data_warehouse/04_register_sales_etl.py
python data_warehouse/05_setup_athena.py
```

## Operational Checks

After the jobs finish:

```bash
python data_warehouse/inspect_dw.py
pytest tests/test_etl.py -v
```

In AWS, validate:

- Glue jobs finish with `SUCCEEDED`
- S3 contains Parquet outputs for all dimensions and facts
- `fact_sales` contains `year/month/day` partitions
- Athena can query all four external tables
- Power BI refreshes through the Athena ODBC connection

## Business Queries

The Athena setup script runs four portfolio-ready analytics:

- Tracks sold by day
- Best-selling artist by month
- Weekday with the highest purchase volume
- Month with the highest sales amount

These queries are intentionally simple to demonstrate the value of the model:
business reporting does not need to join raw transactional tables directly once
the star schema is available.
