# Chinook Fullstack

## Project Overview

This repository is an academic full-stack delivery based on three main layers:

- `backend`: FastAPI application with authentication, search, customer lookup, purchase logic, and PostgreSQL access through `psycopg`
- `frontend`: React application built with Vite
- `infrastructure`: Terraform provisioning, database initialization, deployment scripts, `systemd` service definition, Nginx configuration, and GitHub Actions workflow

The objective of the project is not only to implement the application logic, but
also to demonstrate a reproducible production-style deployment in AWS using
simple and explainable components.

## Architecture

The target production architecture is:

- 1 Ubuntu EC2 instance for the backend API
- 1 Ubuntu EC2 instance for the frontend and Nginx
- 1 Amazon RDS PostgreSQL instance with public access disabled

Role of each component:

- The backend EC2 runs FastAPI with `uvicorn` under `systemd`
- The frontend EC2 serves the React static build from Nginx
- Nginx also reverse proxies `/api/*` requests from the frontend host to the backend EC2 private address
- Amazon RDS stores application data and is reachable only from the backend EC2

In the current Terraform design, both EC2 instances receive public IPs so they
can be administered directly over SSH in a simple student setup. Application
traffic is still layered correctly:

- users access the frontend EC2 on Nginx
- Nginx forwards API traffic to the backend EC2 private IP
- security groups restrict backend port `8000` to the frontend security group
- RDS remains private and is not publicly accessible

## Backend And Frontend Roles

Backend responsibilities:

- expose the API routes
- validate requests
- execute business logic
- connect to PostgreSQL using environment variables
- handle authentication and protected routes

Frontend responsibilities:

- render the user interface
- call the backend using relative `/api` paths
- remain static in production so it can be served efficiently by Nginx

## Why Nginx Reverse Proxy Is Needed

The frontend already uses relative `/api` paths instead of a hardcoded backend
URL. In production, that behavior must be preserved. Nginx solves this by:

- serving the static frontend files from `/var/www/chinook`
- receiving browser requests on the frontend host
- forwarding `/api/*` traffic to the backend EC2

This keeps the frontend code simple, avoids exposing an extra public API domain
for basic deployments, and gives a clear separation between static delivery and
application execution.

## Why RDS Must Not Be Public

The database should not be exposed to the internet because:

- the application server is the only component that needs direct DB access
- reducing public exposure lowers attack surface
- this follows the standard layered security model used in real deployments

For that reason, the recommended design is:

- RDS with `Public access = No`
- inbound database access allowed only from the backend EC2 security group

## Repository Structure

- `backend/`: FastAPI app, database access code, and backend tests
- `frontend/`: React app, Vite configuration, and frontend tests
- `infra/terraform/`: Terraform files to provision AWS networking, EC2 instances, security groups, and RDS
- `infra/db/`: Chinook database initialization files and helper script
- `infra/`: bootstrap scripts, deploy scripts, `systemd` service, and Nginx template
- `docs/`: deployment documentation for AWS and CI/CD
- `.github/workflows/`: GitHub Actions CI/CD pipeline

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

## Deployment Summary

This repository includes a deployment structure designed for:

- Ubuntu 24.04 LTS on EC2
- Python 3.12 on the backend server
- Node 20 LTS in CI for frontend testing and build
- Nginx as static server and reverse proxy
- Terraform for infrastructure provisioning
- PostgreSQL on Amazon RDS with public access disabled
- GitHub Actions on `ubuntu-latest` for tests, build, and deployment
- direct deployment to the frontend EC2 over SSH
- backend deployment over SSH through the frontend EC2 as a jump host

This deployment model is intentionally aligned with the current student-account
constraints:

- no self-hosted runners
- no extra IAM role or instance-profile redesign
- no SSM-based deployment path
- no infrastructure recreation for normal code delivery

When running manual deployment commands from your local terminal, the examples
in the deployment guide use this local SSH key path:

`C:\Users\jrinc\Desktop\Big Data\parcial2\vockey.pem`

## Zero-To-Working Flow

The complete academic delivery now follows this order:

1. provision AWS infrastructure with Terraform under `infra/terraform`
2. read the Terraform outputs for frontend IP/DNS, backend IPs, and RDS endpoint
3. bootstrap the backend and frontend EC2 instances with the existing repo scripts
4. download and initialize the Chinook PostgreSQL database under `infra/db`
5. deploy the backend and frontend application
6. use GitHub Actions for future CI/CD updates after tests pass, with the frontend host acting as the bastion for backend deployment

This separation is intentional:

- Terraform creates infrastructure
- the bootstrap scripts prepare the servers
- the DB initialization layer loads the Chinook database
- the deploy scripts publish the application
- GitHub Actions handles ongoing delivery, not infrastructure creation on every push

## CI/CD Model

The final CI/CD flow is:

- `backend-test` runs on a GitHub-hosted `ubuntu-latest` runner
- `frontend-test-build` runs on a GitHub-hosted `ubuntu-latest` runner
- `deploy` runs on a GitHub-hosted `ubuntu-latest` runner
- the runner deploys directly to `FRONTEND_HOST`
- the runner deploys to the backend using `ssh -J` or `ProxyJump` through `FRONTEND_HOST` and the backend private IP
- the private SSH key stays only on the GitHub-hosted runner and is not copied to the frontend EC2
- the final smoke test still validates the public `/api/health` path through Nginx

Required GitHub repository secrets after this change:

- `SSH_PRIVATE_KEY_B64`
- `SSH_USER`
- `FRONTEND_HOST`
- `BACKEND_PRIVATE_IP`
- `FRONTEND_SERVER_NAME`
- `FRONTEND_BASE_URL`

For the complete deployment procedure, see
[docs/deployment.md](docs/deployment.md).
