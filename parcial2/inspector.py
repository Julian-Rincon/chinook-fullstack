"""
inspector.py
Quick checks for the Parcial 2 Data Warehouse resources.
"""
from __future__ import annotations

import os

import boto3
from botocore.exceptions import ClientError


REGION = os.getenv("AWS_REGION", "us-east-1")
DW_BUCKET = os.getenv("DW_BUCKET", "chinook-dw-parcial2")
DATABASE = os.getenv("GLUE_DATABASE", "chinook_dw")


def inspect_s3(s3_client) -> None:
    print(f"S3 datasets in s3://{DW_BUCKET}/")
    for prefix in ("dim_date/", "dim_customer/", "dim_track/", "fact_sales/"):
        response = s3_client.list_objects_v2(Bucket=DW_BUCKET, Prefix=prefix, MaxKeys=5)
        count = response.get("KeyCount", 0)
        print(f"  {prefix}: {count} object(s) shown")
        for item in response.get("Contents", []):
            print(f"    - {item['Key']} ({item['Size']} bytes)")


def inspect_glue(glue_client) -> None:
    print(f"Glue tables in database: {DATABASE}")
    try:
        paginator = glue_client.get_paginator("get_tables")
        for page in paginator.paginate(DatabaseName=DATABASE):
            for table in page.get("TableList", []):
                print(f"  - {table['Name']} at {table.get('StorageDescriptor', {}).get('Location')}")
    except ClientError as exc:
        print(f"Could not inspect Glue database: {exc}")


def main() -> None:
    s3_client = boto3.client("s3", region_name=REGION)
    glue_client = boto3.client("glue", region_name=REGION)
    inspect_s3(s3_client)
    inspect_glue(glue_client)


if __name__ == "__main__":
    main()
