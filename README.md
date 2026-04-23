# Chinook Fullstack — Coursework Project 1 & 2

**Universidad Sergio Arboleda | Big Data and Data Engineering**
**Professor:** Camilo Enrique Rodriguez Torres.
**Student:** Julian Esteban Rincón Rodríguez

---

## Overview

This repository contains the complete implementation of two academic projects for
the **Big Data and Data Engineering** course. Together, they form an end-to-end
cloud data system that starts with a transactional fullstack web application and
extends into an analytical Data Warehouse on AWS, including automated ETL
pipelines, Athena-based analytics, CI/CD workflows, and Business Intelligence
reporting.

The project is also documented as a portfolio-ready engineering case study. It
shows how a transactional application can evolve into a broader data platform
with clear infrastructure boundaries, reproducible deployment steps, automated
testing, and an analytical layer designed for business questions.

---

## Project 1 — Fullstack Web Application on AWS

### Objective

Design and deploy a fullstack web application on AWS for searching, managing,
and purchasing songs from the **Chinook** sample database. The solution applies
cloud architecture practices, private database access, automated tests, and a
complete CI/CD deployment pipeline.

### Architecture

```
User
  └── EC2 Frontend (Nginx + React)
        └── /api/* → EC2 Backend (FastAPI + uvicorn)
                        └── Amazon RDS PostgreSQL (private Chinook database)
```

### Technology Stack

| Layer | Technology |
|------|-----------|
| Frontend | React 18 + Vite |
| Backend | FastAPI + Python 3.12 + psycopg2 |
| Database | PostgreSQL 15 on Amazon RDS with private access |
| Web server | Nginx as reverse proxy and static file server |
| Infrastructure | Terraform + AWS EC2 + VPC + Security Groups |
| CI/CD | GitHub Actions |
| Backend tests | pytest |
| Frontend tests | Vitest + React Testing Library |

### Main Features

- Search songs by name, artist, or genre
- Purchase songs with frontend and backend validation
- Manage customer data
- Authentication and role-based access for admin and regular users
- User-facing success and error alerts

### Network Architecture

```
Internet
  └── EC2 Frontend (public IP) :80
        ├── Serves React static files from /var/www/chinook
        └── Nginx proxy /api/* → EC2 Backend (private IP) :8000
              └── RDS PostgreSQL (reachable only from the backend security group)
```

### Repository Structure for Project 1

```
backend/           FastAPI app, routes, business logic, tests
frontend/          React app, components, tests
infra/
  terraform/       Networking, EC2, Security Groups, RDS
  db/              Chinook PostgreSQL initialization scripts
  scripts/         Server bootstrap and deployment scripts
docs/              Deployment guide
.github/workflows/ CI/CD pipeline
```

### CI/CD Pipeline

On every push to `main`:

1. `backend-test` installs Python dependencies and runs pytest.
2. `frontend-test-build` installs Node dependencies, runs Vitest, and builds the production frontend.
3. `deploy` deploys the backend and frontend to EC2 through SSH, using the frontend instance as a bastion for the private backend instance.

**Required GitHub Secrets:**

- `SSH_PRIVATE_KEY_B64`
- `SSH_USER`
- `FRONTEND_HOST`
- `BACKEND_PRIVATE_IP`
- `FRONTEND_SERVER_NAME`
- `FRONTEND_BASE_URL`

### Local Setup

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm ci
npm run dev
```

---

## Project 2 — Data Warehouse & Analytics on AWS

### Objective

Design and implement a business analytics system on top of the transactional
Chinook database. The analytical layer applies Data Warehouse modeling concepts,
including a star schema, ETL jobs with AWS Glue, analytical storage with S3 and
Athena, and visualization through Power BI.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TRANSACTIONAL LAYER                         │
│              Amazon RDS PostgreSQL — Database: chinook              │
│   customer · employee · invoice · invoice_line · track              │
│   album · artist · genre · media_type                               │
└──────────────────────┬──────────────────────────────────────────────┘
                       │  AWS Glue ETL Jobs (JDBC)
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           STORAGE LAYER                             │
│            s3://chinook-dw-parcial2/   (Parquet + Snappy)           │
│   dim_date/   dim_customer/   dim_track/   fact_sales/year=.../     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │  AWS Athena (Glue Data Catalog)
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          ANALYTICS LAYER                            │
│                  Athena DB: chinook_dw                              │
│         4 external tables · 4 business analytics queries            │
└──────────────────────┬──────────────────────────────────────────────┘
                       │  ODBC (Simba Athena Driver)
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                          │
│                  Power BI Desktop                                   │
│    Tracks sold by day · Top artist by month · Sales by weekday      │
│    Monthly sales volume                                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Star Schema

```
                    ┌─────────────┐
                    │  dim_date   │
                    │─────────────│
                    │ DateKey (PK)│
                    │ FullDate    │
                    │ Year        │
                    │ Quarter     │
                    │ Month       │
                    │ Day         │
                    │ DayOfWeek   │
                    │ IsHoliday   │
                    └──────┬──────┘
                           │
┌─────────────┐    ┌───────┴──────┐    ┌─────────────┐
│ dim_customer│    │  fact_sales  │    │  dim_track  │
│─────────────│    │──────────────│    │─────────────│
│CustomerKey  ├────│ CustomerKey  │────┤ TrackKey    │
│ FirstName   │    │ TrackKey  (FK│    │ Name        │
│ LastName    │    │InvoiceDateKey│    │ Album       │
│ Company     │    │ EmployeeKey  │    │ Artist      │
│ Country     │    │ Quantity     │    │ Genre       │
│ City        │    │ UnitPrice    │    │ MediaType   │
│ State       │    │ TotalAmount  │    │ Composer    │
│ Email       │    │ year (part.) │    │ Milliseconds│
│ EmployeeKey │    │ month(part.) │    │ UnitPrice   │
│EmployeeName │    │ day  (part.) │    └─────────────┘
│ ReportsTo   │    └──────┬───────┘
└─────────────┘           │
                    ┌──────┴──────┐
                    │  dim_date   │
                    │ (see above) │
                    └─────────────┘
```

### ETL Jobs with AWS Glue

| Job | Type | Source tables | S3 output |
|-----|------|---------------|-----------|
| `etl-dim-date` | Python script + holidays | Generated data | `dim_date/dim_date.parquet` |
| `etl-dim-customer` | Glue ETL with Spark | customer + employee | `dim_customer/` |
| `etl-dim-track` | Glue ETL with Spark | track + album + artist + genre + media_type | `dim_track/` |
| `etl-fact-sales` | Glue ETL with Spark | invoice + invoice_line + customer | `fact_sales/year=.../month=.../day=.../` |

**Technical decisions:**

- `DimDate` is generated for the full 2000-2030 range and uses Colombian holidays through the `holidays` package.
- `FactSales` is partitioned by `year/month/day` to improve Athena query performance.
- Glue jobs use `G.1X` workers and a 20-minute timeout as a cost-conscious academic setup.
- Analytical datasets are stored as **Parquet** with **Snappy** compression.
- Glue scripts use Spark JDBC and explicit connection properties so they can reach the private RDS database from the configured subnet.

### Analytics Queries in Athena

```sql
-- 1. Tracks sold by day
SELECT dd.FullDate, SUM(fs.Quantity) AS tracks_sold
FROM fact_sales fs JOIN dim_date dd ON fs.InvoiceDateKey = dd.DateKey
GROUP BY dd.FullDate ORDER BY dd.FullDate;

-- 2. Best-selling artist by month
SELECT dd.Year, dd.Month, dt.Artist, SUM(fs.Quantity) AS total_sold
FROM fact_sales fs
JOIN dim_date dd  ON fs.InvoiceDateKey = dd.DateKey
JOIN dim_track dt ON fs.TrackKey = dt.TrackKey
GROUP BY dd.Year, dd.Month, dt.Artist
ORDER BY dd.Year, dd.Month, total_sold DESC;

-- 3. Weekday with the highest number of purchases
SELECT dd.DayOfWeek,
       CASE dd.DayOfWeek WHEN 0 THEN 'Monday' WHEN 1 THEN 'Tuesday'
         WHEN 2 THEN 'Wednesday' WHEN 3 THEN 'Thursday' WHEN 4 THEN 'Friday'
         WHEN 5 THEN 'Saturday' ELSE 'Sunday' END AS WeekdayName,
       SUM(fs.Quantity) AS total_purchases
FROM fact_sales fs JOIN dim_date dd ON fs.InvoiceDateKey = dd.DateKey
GROUP BY dd.DayOfWeek ORDER BY total_purchases DESC;

-- 4. Month with the highest sales amount
SELECT dd.Month, SUM(fs.TotalAmount) AS total_sales
FROM fact_sales fs JOIN dim_date dd ON fs.InvoiceDateKey = dd.DateKey
GROUP BY dd.Month ORDER BY total_sales DESC;
```

### AWS Resources for Project 2

| Resource | Identifier |
|----------|------------|
| S3 Data Warehouse bucket | `s3://chinook-dw-parcial2/` |
| S3 Athena results bucket | `s3://chinook-athena-results/results/` |
| Glue Connection | `chinook-rds-connection` (JDBC PostgreSQL) |
| Glue Database | `chinook_dw` |
| S3 VPC Endpoint | `vpce-0b552a40d7803f3c1` (Gateway) |
| Region | `us-east-1` |
| IAM Role | `LabRole` (Vocareum) |

### Data Warehouse Setup

**Prerequisites:**

- AWS credentials configured with `aws configure`
- Python 3.11+ with boto3 installed
- The Project 1 RDS database must be running and reachable from the Glue subnet

```bash
cd parcial2
pip install -r requirements.txt

# Run in order:
python fase1_setup_s3.py       # Create S3 buckets and prefixes
python fase2_glue_setup.py     # Create Glue Connection, IAM references, and Secrets Manager secret
python fase3_etl_dim_date.py   # Generate DimDate with Colombian holidays
python fase4y5_final.py        # Register DimCustomer, DimTrack, and FactSales ETL jobs
python fase6_athena.py         # Create external tables and run analytics queries
```

### Power BI Integration

Connection through the Simba Amazon Athena ODBC Driver 64-bit:

| Field | Value |
|-------|-------|
| Region | `us-east-1` |
| S3 Output | `s3://chinook-athena-results/results/` |
| Auth Type | IAM Credentials |
| Schema | `chinook_dw` |

**Implemented reports:**

1. Tracks sold by day — Line chart
2. Best-selling artist by month — Clustered bar chart
3. Weekday with the highest number of purchases — Bar chart
4. Month with the highest sales volume — Bar chart

---

## Automated Tests

### Project 1

```bash
# Backend
cd backend && pytest --cov=app --cov-report=term-missing

# Frontend
cd frontend && npm test
```

### Project 2 ETL

```bash
pytest tests/test_etl.py -v
```

The ETL unit tests validate:

- `DateKey` format and range using `YYYYMMDD`
- Correct `Quarter` and `DayOfWeek` derivation
- Required columns for each dimension and fact table
- `TotalAmount = Quantity × UnitPrice`
- Consistency between `InvoiceDateKey` and the `year/month/day` partition columns
- S3 path conventions for the Data Warehouse datasets

---

## CI/CD

### Project 1 Deployment Pipeline

```
push to main
  ├── backend-test    pytest on ubuntu-latest
  ├── frontend-test   vitest + production build on ubuntu-latest
  └── deploy          SSH deployment to EC2
```

### Project 2 ETL Test Pipeline

```
push to main
  └── etl-tests       pytest tests/test_etl.py on ubuntu-latest
```

---

## Complete Deployment Flow

### Project 1

1. Provision AWS infrastructure with Terraform from `infra/terraform/`.
2. Bootstrap the EC2 instances with the existing scripts.
3. Initialize the Chinook database on RDS using `infra/db/`.
4. Configure the required GitHub Secrets and push to `main` to trigger CI/CD.

### Project 2

1. Ensure the Project 1 RDS database is running.
2. Run the scripts in `parcial2/` in the documented order.
3. Connect Power BI to Athena through the ODBC driver.

---

## Architecture Rationale

### Why keep RDS private?

The RDS instance has no public IP address. Only the backend EC2 instance can
connect to it through the configured security group. This follows a layered
network security model and avoids exposing the database directly to the internet.

### Why use Nginx as a reverse proxy?

The frontend calls relative `/api/*` routes. Nginx serves the React application
and forwards API traffic to the private backend instance, so the backend does not
need to be publicly exposed.

### Why Parquet and Snappy on S3?

Parquet stores data in a columnar format, which reduces the amount of data
scanned by Athena. Snappy provides fast compression and decompression, making it
a practical choice for analytical workloads.

### Why partition FactSales by year, month, and day?

The analytical queries are date-oriented. Partitioning by `year/month/day` lets
Athena prune irrelevant partitions, reducing query cost and improving response
time.

### Why generate DimDate instead of extracting it from RDS?

A date dimension should cover the full analytical range independently from the
transactional records. Generating `DimDate` for 2000-2030 also allows the model
to include attributes such as `IsHoliday`, which do not exist in the source
database.

---

## Author

**Julian Esteban Rincón Rodríguez**
Systems Engineering and Artificial Intelligence Student
Universidad Sergio Arboleda — Bogotá, Colombia
GitHub: [@Julian-Rincon](https://github.com/Julian-Rincon)
