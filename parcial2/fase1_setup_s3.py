"""
fase1_setup_s3.py
Create the S3 storage layer for the Chinook Data Warehouse.

The script is idempotent: existing buckets are reused and the expected prefixes
are created as zero-byte folder markers.
"""
from __future__ import annotations

import os

import boto3
from botocore.exceptions import ClientError


REGION = os.getenv("AWS_REGION", "us-east-1")
DW_BUCKET = os.getenv("DW_BUCKET", "chinook-dw-parcial2")
ATHENA_BUCKET = os.getenv("ATHENA_BUCKET", "chinook-athena-results")
DW_PREFIXES = ("dim_date/", "dim_customer/", "dim_track/", "fact_sales/", "tmp/glue/")
ATHENA_PREFIXES = ("results/",)


def ensure_bucket(s3_client, bucket_name: str, region: str) -> None:
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket already exists: s3://{bucket_name}")
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code not in {"404", "NoSuchBucket", "NotFound"}:
            raise

        kwargs = {"Bucket": bucket_name}
        if region != "us-east-1":
            kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
        s3_client.create_bucket(**kwargs)
        print(f"Created bucket: s3://{bucket_name}")

    s3_client.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )
    s3_client.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256",
                    }
                }
            ]
        },
    )


def ensure_prefixes(s3_client, bucket_name: str, prefixes: tuple[str, ...]) -> None:
    for prefix in prefixes:
        s3_client.put_object(Bucket=bucket_name, Key=prefix)
        print(f"Ensured prefix: s3://{bucket_name}/{prefix}")


def main() -> None:
    s3_client = boto3.client("s3", region_name=REGION)
    ensure_bucket(s3_client, DW_BUCKET, REGION)
    ensure_bucket(s3_client, ATHENA_BUCKET, REGION)
    ensure_prefixes(s3_client, DW_BUCKET, DW_PREFIXES)
    ensure_prefixes(s3_client, ATHENA_BUCKET, ATHENA_PREFIXES)
    print("S3 storage layer is ready.")


if __name__ == "__main__":
    main()
