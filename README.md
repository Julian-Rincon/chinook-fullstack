# Chinook Cloud Data Platform

**Production-style full-stack application and analytics pipeline for a digital music store on AWS.**

[![AWS](https://img.shields.io/badge/Cloud-AWS-ff9900.svg)](https://aws.amazon.com/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18-61dafb.svg)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/Database-RDS_PostgreSQL-336791.svg)](https://www.postgresql.org/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-7b42bc.svg)](https://www.terraform.io/)
[![Athena](https://img.shields.io/badge/Analytics-Athena-232f3e.svg)](https://aws.amazon.com/athena/)

## Overview

Chinook Cloud Data Platform is an end-to-end AWS project that turns the Chinook
music store dataset into a deployable product and an analytics platform.

The transactional side is a React + FastAPI web application deployed on EC2,
backed by a private Amazon RDS PostgreSQL database. The analytical side extends
that same source system into a cloud data warehouse on S3 using AWS Glue, Athena,
and Power BI.

The repository is organized as a portfolio-ready engineering case study:
reproducible infrastructure, clear deployment scripts, automated tests, CI/CD,
secure network boundaries, and a data pipeline that supports business reporting.

## Architecture

```text
Users
  -> EC2 Frontend
       Nginx + React static build
       /api/* reverse proxy
  -> EC2 Backend
       FastAPI + uvicorn + systemd
  -> Amazon RDS PostgreSQL
       private Chinook OLTP database

Amazon RDS PostgreSQL
  -> AWS Glue ETL jobs
  -> Amazon S3 Data Warehouse
       Parquet + Snappy + partitioned fact table
  -> AWS Glue Data Catalog + Athena
  -> Power BI dashboard
```

## What This Demonstrates

- Full-stack cloud deployment with separate frontend, backend, and database tiers
- Private database access through AWS security groups instead of public RDS exposure
- Infrastructure as Code with Terraform for VPC, EC2, RDS, and security groups
- CI/CD with GitHub Actions, automated tests, artifact build, SSH deployment, and smoke tests
- Data warehouse modeling with a star schema over transactional sales data
- Glue ETL jobs that load PostgreSQL data into analytical Parquet datasets on S3
- Athena external tables and business queries for reporting
- Power BI integration through the Athena ODBC driver

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React 18, Vite, Vitest, React Testing Library |
| Backend | FastAPI, Python 3.12, pytest, psycopg2 |
| Database | Amazon RDS PostgreSQL 15 |
| Infrastructure | Terraform, EC2, VPC, Security Groups, Nginx, systemd |
| Data Engineering | AWS Glue, S3, Athena, Glue Data Catalog, Parquet |
| BI | Power BI Desktop, Simba Athena ODBC driver |
| CI/CD | GitHub Actions |

## Repository Layout

```text
backend/             FastAPI application, service layer, DB access, tests
frontend/            React application, API client, tests, Vite build
infra/
  terraform/         AWS infrastructure definitions
  db/                Chinook PostgreSQL initialization scripts
  scripts/           EC2 bootstrap, deployment, and smoke-test scripts
  nginx/             Production Nginx reverse proxy config
  systemd/           Backend service definition
data_warehouse/     Data warehouse setup, Glue ETL, Athena scripts
tests/               Data engineering unit tests
docs/                Deployment and architecture documentation
reports/             Power BI report artifact
.github/workflows/   CI/CD and ETL validation workflows
```

## Application Features

- Search tracks by song, artist, album, or genre
- Purchase flow with frontend and backend validation
- Customer management
- Authentication with admin and regular-user roles
- Health checks for deployment validation
- API-backed user feedback for success and error states

## Data Warehouse Model

```text
dim_customer       dim_date          dim_track
      \              |                 /
       \             |                /
        +--------- fact_sales --------+
                  year/month/day partitions
```

### Dimensions

- `dim_date`: generated calendar from 2000 to 2030, including Colombian holidays
- `dim_customer`: customer profile enriched with support representative data
- `dim_track`: track, album, artist, genre, media type, composer, duration, and price

### Fact Table

- `fact_sales`: invoice line grain with customer, track, invoice date, employee,
  quantity, unit price, total amount, and `year/month/day` partitions

## Analytics Delivered

- Tracks sold by day
- Best-selling artist by month
- Weekday with the highest purchase volume
- Month with the highest sales amount

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On Windows:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

### Data Warehouse Scripts

```bash
cd data_warehouse
pip install -r requirements.txt

python 01_setup_s3.py
python 02_setup_glue.py
python 03_load_dim_date.py
python 04_register_sales_etl.py
python 05_setup_athena.py
```

Runtime configuration is read from environment variables where possible:
`AWS_REGION`, `DW_BUCKET`, `ATHENA_OUTPUT`, `GLUE_DATABASE`,
`GLUE_CONNECTION_NAME`, `GLUE_ROLE_ARN`, `RDS_ENDPOINT`, `RDS_DB_NAME`,
`RDS_USERNAME`, and `RDS_PASSWORD`.

## Testing

```bash
# Backend
cd backend
pytest --cov=app --cov-report=term-missing

# Frontend
cd frontend
npm run test:coverage

# Data engineering checks
pytest tests/test_etl.py -v
```

## Deployment

The production application flow is documented in
[docs/deployment.md](docs/deployment.md). The analytical pipeline is documented
in [docs/data-warehouse.md](docs/data-warehouse.md).
At a high level:

1. Provision AWS resources with Terraform from `infra/terraform/`.
2. Bootstrap the EC2 instances using `infra/scripts/`.
3. Initialize the Chinook schema in RDS using `infra/db/`.
4. Configure GitHub repository secrets.
5. Push to `main`; GitHub Actions tests, builds, deploys, and smoke-tests the app.
6. Run the data warehouse scripts after the transactional database is available.
7. Connect Power BI to Athena for BI reporting.

## Security Notes

- RDS is private and only reachable from the backend security group.
- The frontend is the public entry point and proxies API traffic through Nginx.
- Secrets and AWS credentials are not committed to the repository.
- Terraform variable files, local plans, virtual environments, and build outputs are ignored.

## Project Status

- Full-stack application: implemented and deployable on AWS
- Terraform infrastructure: implemented
- GitHub Actions CI/CD: implemented
- Data warehouse pipeline: implemented
- Athena analytical tables and queries: implemented
- Power BI report artifact: included in `reports/chinook_analytics.pbix`

## Author

**Julian Esteban Rincon Rodriguez**

Systems Engineering and Artificial Intelligence
GitHub: [@Julian-Rincon](https://github.com/Julian-Rincon)
