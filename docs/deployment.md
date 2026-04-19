# Deployment Guide

## 1. Objective

This document explains how to deploy the project from scratch in a fresh AWS
account using simple, auditable infrastructure:

- 1 Ubuntu EC2 for the backend
- 1 Ubuntu EC2 for the frontend and Nginx
- 1 private Amazon RDS PostgreSQL instance
- GitHub Actions for CI/CD

The design is intentionally straightforward so it can be defended clearly in an
academic presentation.

## 2. Project Architecture

### Backend Role

The backend is a FastAPI application that:

- exposes the API endpoints
- handles authentication
- executes business logic
- connects to PostgreSQL
- runs under `uvicorn` managed by `systemd`

### Frontend Role

The frontend is a React application built with Vite that:

- provides the user interface
- calls the backend through relative `/api` routes
- is deployed as static files served by Nginx

### Reverse Proxy Role

Nginx is required because the frontend already uses relative `/api` calls. In
production, Nginx keeps that behavior by:

- serving the static frontend files
- receiving all browser requests on the frontend EC2
- forwarding `/api/*` requests to the backend EC2 private address

This avoids changing frontend code for production and gives a clean separation
between static delivery and API execution.

### Database Role

Amazon RDS is used as the managed PostgreSQL service. It must not be public
because:

- only the backend server needs direct access
- public exposure would unnecessarily increase the attack surface
- a private database is the standard secure deployment pattern

## 3. Provisioning Strategy

The repository now separates the infrastructure flow into four stages:

1. `infra/terraform`: provisions AWS infrastructure
2. `infra/scripts`: bootstraps and deploys the EC2 instances
3. `infra/db`: initializes the Chinook database
4. `.github/workflows/deploy.yml`: handles CI/CD for code delivery after tests pass

GitHub Actions is intentionally **not** used to create infrastructure on every
push. Infrastructure is provisioned separately with Terraform.

## 4. Required AWS Components

Terraform provisions these resources:

1. VPC
2. public subnets for frontend EC2 and backend EC2
3. private subnets for RDS
4. route tables and internet gateway
5. security groups
6. frontend EC2 instance
7. backend EC2 instance
8. PostgreSQL RDS instance with `publicly_accessible = false`

The current Terraform layout does not create a NAT gateway because the chosen
academic design keeps the backend EC2 reachable for SSH and package updates in a
public subnet while still restricting application traffic with security groups.
The database remains private in private subnets.

## 5. Recommended Security Groups

### Frontend EC2 Security Group

- allow `22` from your administrator IP or approved deployment source
- allow `80` from the internet
- allow `443` from the internet if HTTPS is added
- allow outbound traffic to backend port `8000`

### Backend EC2 Security Group

- allow `22` from your administrator IP or approved deployment source
- allow `8000` only from the frontend EC2 security group
- allow outbound traffic to RDS port `5432`

### RDS Security Group

- allow `5432` only from the backend EC2 security group

This model ensures:

- the frontend is public
- the backend instance is SSH-accessible in a public subnet for a simple demo setup
- backend application traffic on port `8000` is restricted to the frontend EC2 security group
- the database is private except for backend-to-database traffic

## 6. Terraform Files

Main files under `infra/terraform`:

- `versions.tf`: Terraform and provider requirements
- `providers.tf`: AWS provider configuration
- `variables.tf`: input variables
- `network.tf`: VPC, subnets, route tables, internet gateway, and DB subnet group
- `security.tf`: security groups
- `compute.tf`: Ubuntu EC2 instances
- `database.tf`: PostgreSQL RDS instance
- `outputs.tf`: frontend public IP or DNS, backend IPs, RDS endpoint, and security group IDs
- `terraform.tfvars.example`: example values

## 7. Fixed Paths Used By This Repository

- Backend code: `/opt/chinook/backend`
- Frontend build: `/var/www/chinook`
- Backend environment file: `/etc/chinook/backend.env`

These fixed paths are used by the deployment scripts, the `systemd` service,
and the Nginx configuration.

## 8. Required Backend Environment Variables

The backend reads configuration from environment variables stored on the server
in `/etc/chinook/backend.env`.

Required variables:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

Optional but recommended variables:

- `AUTH_SECRET_KEY`
- `AUTH_ACCESS_TOKEN_MINUTES`
- `SKIP_DB_INIT`
- `CORS_ALLOW_ORIGINS`

See [backend/.env.example](../backend/.env.example) for the template. After
Terraform runs, `DB_HOST` should use the `rds_endpoint` output value.

## 9. Required GitHub Secrets

The GitHub Actions workflow requires these secrets:

- `SSH_PRIVATE_KEY_B64`
- `SSH_USER`
- `BACKEND_HOST`
- `FRONTEND_HOST`
- `BACKEND_UPSTREAM`
- `FRONTEND_SERVER_NAME`
- `FRONTEND_BASE_URL`

Meaning of the deployment secrets:

- `BACKEND_UPSTREAM`
  - private backend URL used by Nginx on the frontend EC2
  - example: `http://10.0.2.15:8000`
- `FRONTEND_SERVER_NAME`
  - server name written into the Nginx site config
  - example: `app.example.com`
- `FRONTEND_BASE_URL`
  - public URL used for the final smoke test
  - example: `http://ec2-xx-xx-xx-xx.compute-1.amazonaws.com`

Do not store real credentials in the repository.

## 10. First-Time Deployment Steps

### Step 1: Create Terraform Variables

Move into the Terraform directory and prepare your local variables file:

```powershell
cd infra/terraform
copy terraform.tfvars.example terraform.tfvars
```

Set values for:

- `region`
- `frontend_instance_type`
- `backend_instance_type`
- `key_pair_name`
- `admin_cidr_blocks`
- `db_name`
- `db_username`
- `db_password`

Do not commit `terraform.tfvars`.

### Step 2: Provision AWS Infrastructure With Terraform

Run:

```powershell
terraform init
terraform plan
terraform apply
```

Important outputs to save:

- frontend public IP or DNS
- backend public IP
- backend private IP
- RDS endpoint
- security group IDs

You will use those outputs in the next steps.

### Step 3: Verify Local SSH Access

From your local terminal, verify access to both servers using your local key
file. Replace `BACKEND_IP` and `FRONTEND_IP` with the real public IPs:

```powershell
ssh -i "C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem" ubuntu@BACKEND_IP
ssh -i "C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem" ubuntu@FRONTEND_IP
```

### Step 4: Copy Infrastructure Files To The Servers

Before bootstrap, copy the repo-managed `infra/` directory to each server:

```powershell
rsync -avz -e "ssh -i \"C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem\"" infra/ ubuntu@BACKEND_IP:/tmp/chinook/infra/
rsync -avz -e "ssh -i \"C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem\"" infra/ ubuntu@FRONTEND_IP:/tmp/chinook/infra/
```

### Step 5: Prepare The Backend Server

Connect to the backend EC2 and run:

```powershell
ssh -i "C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem" ubuntu@BACKEND_IP
sudo bash /tmp/chinook/infra/scripts/bootstrap_backend_server.sh
```

This script:

- installs Python 3.12 and deployment tools
- installs `psql` through `postgresql-client` so database initialization works from the backend host
- creates `/opt/chinook/backend`
- creates `/etc/chinook`
- installs the `systemd` service definition

### Step 6: Prepare The Frontend Server

Connect to the frontend EC2 and run:

```powershell
ssh -i "C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem" ubuntu@FRONTEND_IP
sudo bash /tmp/chinook/infra/scripts/bootstrap_frontend_server.sh
```

This script:

- installs Nginx and deployment tools
- creates `/var/www/chinook`
- installs the Nginx site configuration
- enables the site and reloads Nginx safely

### Step 7: Create The Backend Environment File

On the backend EC2, create:

```powershell
ssh -i "C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem" ubuntu@BACKEND_IP
sudo nano /etc/chinook/backend.env
```

Populate it using the values from [backend/.env.example](../backend/.env.example).
Use:

- `DB_HOST` = Terraform `rds_endpoint`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD` = your Terraform DB variables

Important:

- the current GitHub Actions workflow does **not** create or upload `/etc/chinook/backend.env`
- create this file manually during the first-time setup
- later deployments assume the file already exists on the backend EC2

### Step 8: Initialize The Chinook Database

The application requires the Chinook schema/data plus the `app_user` table.

This repository does not already contain the real Chinook PostgreSQL SQL file.
Instead, it uses a pinned download script under `infra/db` that fetches the
official PostgreSQL asset from the `lerocha/chinook-database` release `v1.4.5`.

Recommended place to run this:

- on the backend EC2 instance after bootstrap
- this is practical because the backend host can reach the private RDS instance and now includes `psql`

Download the SQL first:

```bash
bash /tmp/chinook/infra/db/download_chinook_postgres.sh
```

Then initialize the database:

```bash
export DB_HOST="YOUR_RDS_ENDPOINT"
export DB_PORT="5432"
export DB_NAME="chinook"
export DB_USER="chinook_admin"
export DB_PASSWORD="replace-me"
bash /tmp/chinook/infra/db/init_chinook.sh
```

Important:

- `infra/db/download_chinook_postgres.sh` downloads the pinned PostgreSQL Chinook SQL
- `infra/db/init_chinook.sh` loads that SQL into RDS
- `infra/db/app_user.sql` creates the application authentication table

This step is required because the backend business logic queries Chinook tables
such as `track`, `artist`, `customer`, `invoice`, and `invoice_line`.

### Step 9: Deploy The Application

Backend:

- copy backend source to `/tmp/chinook/backend`
- copy `infra/` to `/tmp/chinook/infra`
- run:

```powershell
rsync -avz -e "ssh -i \"C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem\"" backend/ ubuntu@BACKEND_IP:/tmp/chinook/backend/
rsync -avz -e "ssh -i \"C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem\"" infra/ ubuntu@BACKEND_IP:/tmp/chinook/infra/
ssh -i "C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem" ubuntu@BACKEND_IP
sudo bash /tmp/chinook/infra/scripts/deploy_backend.sh
```

Frontend:

- copy built frontend files to `/tmp/chinook/frontend-dist`
- copy `infra/` to `/tmp/chinook/infra`
- run:

```powershell
rsync -avz -e "ssh -i \"C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem\"" frontend/dist/ ubuntu@FRONTEND_IP:/tmp/chinook/frontend-dist/
rsync -avz -e "ssh -i \"C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem\"" infra/ ubuntu@FRONTEND_IP:/tmp/chinook/infra/
ssh -i "C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem" ubuntu@FRONTEND_IP
sudo BACKEND_UPSTREAM=http://10.0.2.15:8000 SERVER_NAME=app.example.com \
  bash /tmp/chinook/infra/scripts/deploy_frontend.sh
```

`BACKEND_UPSTREAM` should use the backend **private IP** from Terraform outputs,
for example `http://10.0.2.15:8000`.

### Step 10: Configure GitHub Actions

Add the required GitHub repository secrets, then let the workflow handle test,
build, upload, deploy, and smoke test steps on future pushes.

Recommended mapping:

- `SSH_PRIVATE_KEY_B64` = base64-encoded private key used by GitHub Actions for SSH
- `SSH_USER` = SSH username for both EC2 instances, for example `ubuntu`
- `BACKEND_HOST` = backend public IP or DNS from Terraform
- `FRONTEND_HOST` = frontend public IP or DNS from Terraform
- `BACKEND_UPSTREAM` = backend private IP from Terraform, for example `http://10.0.2.15:8000`
- `FRONTEND_SERVER_NAME` = public hostname used in the Nginx config, or `_` if no custom domain is used yet
- `FRONTEND_BASE_URL` = frontend public URL

## 11. Update Deployment Steps

For a regular update after the servers are already bootstrapped:

1. push code to the repository
2. let GitHub Actions run backend tests
3. let GitHub Actions run frontend tests and build
4. let GitHub Actions upload staged files to the two EC2 instances
5. let GitHub Actions execute the repo-managed deploy scripts remotely
6. confirm the smoke tests pass

Terraform is not part of the normal update path unless you intentionally want to
change infrastructure.

If deploying manually:

Backend:

```powershell
rsync -avz -e "ssh -i \"C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem\"" backend/ ubuntu@BACKEND_IP:/tmp/chinook/backend/
rsync -avz -e "ssh -i \"C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem\"" infra/ ubuntu@BACKEND_IP:/tmp/chinook/infra/
ssh -i "C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem" ubuntu@BACKEND_IP
sudo bash /tmp/chinook/infra/scripts/deploy_backend.sh
```

Frontend:

```powershell
rsync -avz -e "ssh -i \"C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem\"" frontend/dist/ ubuntu@FRONTEND_IP:/tmp/chinook/frontend-dist/
rsync -avz -e "ssh -i \"C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem\"" infra/ ubuntu@FRONTEND_IP:/tmp/chinook/infra/
ssh -i "C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem" ubuntu@FRONTEND_IP
sudo BACKEND_UPSTREAM=http://10.0.2.15:8000 SERVER_NAME=app.example.com \
  bash /tmp/chinook/infra/scripts/deploy_frontend.sh
```

## 12. Validation Checklist Before Submission

Use this checklist before presenting or submitting the project:

- `terraform plan` and `terraform apply` succeed
- Terraform outputs show frontend public address, backend IPs, and RDS endpoint
- backend tests pass
- frontend tests pass
- frontend build succeeds
- backend service is active in `systemctl`
- Nginx configuration passes `nginx -t`
- backend direct health check succeeds on `/health`
- frontend is reachable from the browser
- `/api/health` responds successfully through the frontend host
- backend connects to RDS successfully
- Chinook schema and seed data were loaded successfully
- RDS public access is disabled
- backend environment file exists on the server and is not committed to Git
- GitHub Actions workflow deploys only after tests pass
- GitHub Actions is not recreating infrastructure on every push
- deployment scripts come from the repository, not manual server-only scripts

## 13. Why This Deployment Is Defensible In Class

This delivery is easy to justify technically because:

- the architecture is layered and secure
- infrastructure is reproducible through Terraform
- responsibilities are clearly separated between frontend, backend, and database
- the frontend behavior is preserved through Nginx reverse proxying
- the database is private by design
- the Chinook database is initialized explicitly and can be audited
- CI/CD is reproducible from version-controlled scripts
- the deployment process is explicit, readable, and easy to demonstrate
