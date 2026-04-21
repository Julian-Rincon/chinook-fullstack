"""
fase4y5_final.py
Upload and register the Glue ETL jobs for DimCustomer, DimTrack and FactSales.

The jobs read Chinook PostgreSQL through the Glue JDBC connection created in
fase2_glue_setup.py and write Parquet datasets to S3.
"""
from __future__ import annotations

import os
import textwrap

import boto3
from botocore.exceptions import ClientError


REGION = os.getenv("AWS_REGION", "us-east-1")
DW_BUCKET = os.getenv("DW_BUCKET", "chinook-dw-parcial2")
CONNECTION_NAME = os.getenv("GLUE_CONNECTION_NAME", "chinook-rds-connection")
GLUE_VERSION = os.getenv("GLUE_VERSION", "4.0")
WORKER_TYPE = os.getenv("GLUE_WORKER_TYPE", "G.1X")
NUMBER_OF_WORKERS = int(os.getenv("GLUE_NUMBER_OF_WORKERS", "2"))
TIMEOUT_MINUTES = int(os.getenv("GLUE_TIMEOUT_MINUTES", "20"))


def lab_role_arn(sts_client) -> str:
    configured = os.getenv("GLUE_ROLE_ARN")
    if configured:
        return configured
    account_id = sts_client.get_caller_identity()["Account"]
    return f"arn:aws:iam::{account_id}:role/LabRole"


DIM_CUSTOMER_SCRIPT = r"""
import sys
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql.functions import col, concat_ws

args = getResolvedOptions(sys.argv, ["JOB_NAME", "output_bucket", "connection_name"])
glue_context = GlueContext(SparkContext.getOrCreate())

def read_table(table_name):
    return glue_context.create_dynamic_frame.from_options(
        connection_type="postgresql",
        connection_options={
            "useConnectionProperties": "true",
            "connectionName": args["connection_name"],
            "dbtable": table_name,
        },
    ).toDF()

customer = read_table("customer").alias("c")
employee = read_table("employee").alias("e")

dim_customer = (
    customer.join(employee, col("c.support_rep_id") == col("e.employee_id"), "left")
    .select(
        col("c.customer_id").alias("CustomerKey"),
        col("c.first_name").alias("FirstName"),
        col("c.last_name").alias("LastName"),
        col("c.company").alias("Company"),
        col("c.country").alias("Country"),
        col("c.city").alias("City"),
        col("c.state").alias("State"),
        col("c.email").alias("Email"),
        col("c.support_rep_id").alias("EmployeeKey"),
        concat_ws(" ", col("e.first_name"), col("e.last_name")).alias("EmployeeName"),
        col("e.reports_to").alias("ReportsTo"),
    )
)

dim_customer.write.mode("overwrite").parquet(args["output_bucket"].rstrip("/") + "/dim_customer/")
"""


DIM_TRACK_SCRIPT = r"""
import sys
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql.functions import col

args = getResolvedOptions(sys.argv, ["JOB_NAME", "output_bucket", "connection_name"])
glue_context = GlueContext(SparkContext.getOrCreate())

def read_table(table_name):
    return glue_context.create_dynamic_frame.from_options(
        connection_type="postgresql",
        connection_options={
            "useConnectionProperties": "true",
            "connectionName": args["connection_name"],
            "dbtable": table_name,
        },
    ).toDF()

track = read_table("track").alias("t")
album = read_table("album").alias("al")
artist = read_table("artist").alias("ar")
genre = read_table("genre").alias("g")
media_type = read_table("media_type").alias("mt")

dim_track = (
    track.join(album, col("t.album_id") == col("al.album_id"), "left")
    .join(artist, col("al.artist_id") == col("ar.artist_id"), "left")
    .join(genre, col("t.genre_id") == col("g.genre_id"), "left")
    .join(media_type, col("t.media_type_id") == col("mt.media_type_id"), "left")
    .select(
        col("t.track_id").alias("TrackKey"),
        col("t.name").alias("Name"),
        col("al.title").alias("Album"),
        col("ar.name").alias("Artist"),
        col("g.name").alias("Genre"),
        col("mt.name").alias("MediaType"),
        col("t.composer").alias("Composer"),
        col("t.milliseconds").alias("Milliseconds"),
        col("t.unit_price").alias("UnitPrice"),
    )
)

dim_track.write.mode("overwrite").parquet(args["output_bucket"].rstrip("/") + "/dim_track/")
"""


FACT_SALES_SCRIPT = r"""
import sys
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql.functions import col, date_format, dayofmonth, month, round, year

args = getResolvedOptions(sys.argv, ["JOB_NAME", "output_bucket", "connection_name"])
glue_context = GlueContext(SparkContext.getOrCreate())

def read_table(table_name):
    return glue_context.create_dynamic_frame.from_options(
        connection_type="postgresql",
        connection_options={
            "useConnectionProperties": "true",
            "connectionName": args["connection_name"],
            "dbtable": table_name,
        },
    ).toDF()

invoice = read_table("invoice").alias("i")
invoice_line = read_table("invoice_line").alias("il")
customer = read_table("customer").alias("c")

fact_sales = (
    invoice.join(invoice_line, col("i.invoice_id") == col("il.invoice_id"), "inner")
    .join(customer, col("i.customer_id") == col("c.customer_id"), "left")
    .select(
        col("i.customer_id").alias("CustomerKey"),
        col("il.track_id").alias("TrackKey"),
        date_format(col("i.invoice_date"), "yyyyMMdd").cast("int").alias("InvoiceDateKey"),
        col("c.support_rep_id").alias("EmployeeKey"),
        col("il.quantity").alias("Quantity"),
        col("il.unit_price").alias("UnitPrice"),
        round(col("il.quantity") * col("il.unit_price"), 2).alias("TotalAmount"),
        year(col("i.invoice_date")).alias("year"),
        month(col("i.invoice_date")).alias("month"),
        dayofmonth(col("i.invoice_date")).alias("day"),
    )
)

(
    fact_sales.write.mode("overwrite")
    .partitionBy("year", "month", "day")
    .parquet(args["output_bucket"].rstrip("/") + "/fact_sales/")
)
"""


JOBS = {
    "etl-dim-customer": DIM_CUSTOMER_SCRIPT,
    "etl-dim-track": DIM_TRACK_SCRIPT,
    "etl-fact-sales": FACT_SALES_SCRIPT,
}


def upload_script(s3_client, job_name: str, script: str) -> str:
    key = f"glue-scripts/{job_name}.py"
    s3_client.put_object(
        Bucket=DW_BUCKET,
        Key=key,
        Body=textwrap.dedent(script).strip().encode("utf-8"),
    )
    return f"s3://{DW_BUCKET}/{key}"


def ensure_job(glue_client, job_name: str, script_location: str, role_arn: str) -> None:
    job_input = {
        "Name": job_name,
        "Role": role_arn,
        "Description": f"Parcial 2 Chinook DW job: {job_name}",
        "Command": {
            "Name": "glueetl",
            "ScriptLocation": script_location,
            "PythonVersion": "3",
        },
        "DefaultArguments": {
            "--job-language": "python",
            "--enable-metrics": "true",
            "--enable-continuous-cloudwatch-log": "true",
            "--TempDir": f"s3://{DW_BUCKET}/tmp/glue/",
            "--output_bucket": f"s3://{DW_BUCKET}",
            "--connection_name": CONNECTION_NAME,
        },
        "Connections": {"Connections": [CONNECTION_NAME]},
        "GlueVersion": GLUE_VERSION,
        "WorkerType": WORKER_TYPE,
        "NumberOfWorkers": NUMBER_OF_WORKERS,
        "Timeout": TIMEOUT_MINUTES,
    }

    try:
        glue_client.create_job(**job_input)
        print(f"Created Glue job: {job_name}")
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "AlreadyExistsException":
            raise
        job_update = dict(job_input)
        job_update.pop("Name")
        glue_client.update_job(JobName=job_name, JobUpdate=job_update)
        print(f"Updated Glue job: {job_name}")


def main() -> None:
    s3_client = boto3.client("s3", region_name=REGION)
    glue_client = boto3.client("glue", region_name=REGION)
    sts_client = boto3.client("sts", region_name=REGION)
    role_arn = lab_role_arn(sts_client)

    for job_name, script in JOBS.items():
        script_location = upload_script(s3_client, job_name, script)
        ensure_job(glue_client, job_name, script_location, role_arn)

    print("Glue ETL jobs for dimensions and facts are ready.")


if __name__ == "__main__":
    main()
