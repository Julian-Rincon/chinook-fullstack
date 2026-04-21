"""
fase2_glue_setup.py
Create the Glue Data Catalog database and JDBC connection used by the ETL jobs.

Required environment variables:
  CHINOOK_JDBC_URL          jdbc:postgresql://host:5432/chinook
  CHINOOK_DB_USER          PostgreSQL user
  CHINOOK_DB_PASSWORD      PostgreSQL password
  CHINOOK_SUBNET_ID        Private subnet where Glue can reach RDS
  CHINOOK_SECURITY_GROUP_ID Security group allowed to reach RDS

Optional:
  CHINOOK_AVAILABILITY_ZONE, AWS_REGION, GLUE_DATABASE, GLUE_CONNECTION_NAME
"""
from __future__ import annotations

import json
import os

import boto3
from botocore.exceptions import ClientError


REGION = os.getenv("AWS_REGION", "us-east-1")
GLUE_DATABASE = os.getenv("GLUE_DATABASE", "chinook_dw")
CONNECTION_NAME = os.getenv("GLUE_CONNECTION_NAME", "chinook-rds-connection")
SECRET_NAME = os.getenv("CHINOOK_SECRET_NAME", "chinook/rds/credentials")
REQUIRED_ENV = (
    "CHINOOK_JDBC_URL",
    "CHINOOK_DB_USER",
    "CHINOOK_DB_PASSWORD",
    "CHINOOK_SUBNET_ID",
    "CHINOOK_SECURITY_GROUP_ID",
)


def env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def ensure_database(glue_client) -> None:
    try:
        glue_client.create_database(
            DatabaseInput={
                "Name": GLUE_DATABASE,
                "Description": "Chinook star-schema Data Warehouse for Parcial 2",
            }
        )
        print(f"Created Glue database: {GLUE_DATABASE}")
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "AlreadyExistsException":
            raise
        print(f"Glue database already exists: {GLUE_DATABASE}")


def ensure_secret(secrets_client) -> None:
    secret_payload = {
        "username": env("CHINOOK_DB_USER"),
        "password": env("CHINOOK_DB_PASSWORD"),
        "jdbc_url": env("CHINOOK_JDBC_URL"),
    }
    secret_string = json.dumps(secret_payload)

    try:
        secrets_client.create_secret(Name=SECRET_NAME, SecretString=secret_string)
        print(f"Created Secrets Manager secret: {SECRET_NAME}")
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "ResourceExistsException":
            raise
        secrets_client.put_secret_value(SecretId=SECRET_NAME, SecretString=secret_string)
        print(f"Updated Secrets Manager secret: {SECRET_NAME}")


def ensure_connection(glue_client) -> None:
    physical = {
        "SubnetId": env("CHINOOK_SUBNET_ID"),
        "SecurityGroupIdList": [env("CHINOOK_SECURITY_GROUP_ID")],
    }
    availability_zone = os.getenv("CHINOOK_AVAILABILITY_ZONE")
    if availability_zone:
        physical["AvailabilityZone"] = availability_zone

    connection_input = {
        "Name": CONNECTION_NAME,
        "Description": "JDBC connection from Glue to private Chinook PostgreSQL RDS",
        "ConnectionType": "JDBC",
        "ConnectionProperties": {
            "JDBC_CONNECTION_URL": env("CHINOOK_JDBC_URL"),
            "USERNAME": env("CHINOOK_DB_USER"),
            "PASSWORD": env("CHINOOK_DB_PASSWORD"),
            "JDBC_ENFORCE_SSL": "false",
        },
        "PhysicalConnectionRequirements": physical,
    }

    try:
        glue_client.create_connection(ConnectionInput=connection_input)
        print(f"Created Glue connection: {CONNECTION_NAME}")
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "AlreadyExistsException":
            raise
        glue_client.update_connection(Name=CONNECTION_NAME, ConnectionInput=connection_input)
        print(f"Updated Glue connection: {CONNECTION_NAME}")


def main() -> None:
    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    if missing:
        raise RuntimeError("Missing required environment variables: " + ", ".join(missing))

    glue_client = boto3.client("glue", region_name=REGION)
    secrets_client = boto3.client("secretsmanager", region_name=REGION)
    ensure_database(glue_client)
    ensure_secret(secrets_client)
    ensure_connection(glue_client)
    print("Glue setup is ready.")


if __name__ == "__main__":
    main()
