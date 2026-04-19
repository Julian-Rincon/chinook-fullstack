# Database Initialization

This folder contains the database initialization layer required for PostgreSQL
RDS.

## Does This Repository Already Contain The Chinook PostgreSQL SQL?

No. The repository does not ship the real Chinook PostgreSQL SQL file.

To keep the repository lightweight and avoid copying external course assets into
source control, the project now uses a pinned download script that retrieves the
official PostgreSQL Chinook script from the Chinook database release assets.

## Pinned Source Used By This Project

The download script fetches this exact release asset:

- project: `lerocha/chinook-database`
- release: `v1.4.5`
- asset: `Chinook_PostgreSql.sql`

This is a practical choice for student setups because it is:

- public
- stable
- version-pinned
- directly compatible with PostgreSQL

## Files

- `download_chinook_postgres.sh`: downloads the pinned Chinook PostgreSQL SQL file
- `init_chinook.sh`: initializes the PostgreSQL RDS database
- `chinook_postgresql.sql`: downloaded Chinook SQL file
- `app_user.sql`: creates the `app_user` table used by the backend

## Why This Supports The Existing Backend

The backend queries these Chinook tables directly:

- `track`
- `album`
- `artist`
- `genre`
- `customer`
- `invoice`
- `invoice_line`

Those tables are required by the existing backend flows for:

- search
- customer lookup
- purchase

The initialization process therefore has two parts:

1. load the full Chinook PostgreSQL script
2. create the `app_user` table for application authentication

## Recommended Execution Location

The most practical student setup is to run the initialization from the backend
EC2 instance after Terraform provisioning and server bootstrap. That keeps the
database private while still allowing initialization through the backend host,
which is already allowed to reach RDS.

## Step 1: Download The Pinned Chinook SQL

From the backend EC2 or from a machine that can reach the database:

```bash
bash infra/db/download_chinook_postgres.sh
```

## Step 2: Run The Initialization

Set the PostgreSQL connection variables and run:

```bash
export DB_HOST=your-rds-endpoint.amazonaws.com
export DB_PORT=5432
export DB_NAME=chinook
export DB_USER=chinook_admin
export DB_PASSWORD=replace-me
bash infra/db/init_chinook.sh
```

## What The Initialization Script Does

1. validates the required PostgreSQL environment variables
2. validates that `chinook_postgresql.sql` exists
3. applies the full Chinook PostgreSQL script
4. creates the `app_user` table
5. stops on the first SQL error
