# Inspect Delta lake (../data/bronze), lake house (table format) parquet + log
# Check if changes on the living schema (postqes) are merged to Delta
# The Lakehouse (architecture pattern) including three table format: Delta Lake: a directory of Parquet files managed by a sequential, append-only JSON transaction log (_delta_log),
# Apache Iceberg: a catalog points to a metadata.json, which points to a tree of manifest files listing the Parquet data files. 
# Apache Hudi: a timeline coordinates operations on "file groups" that can contain both Parquet base files and Avro delta logs (for MoR).

#Platform         Databricks, Snowflake, AWS EMR, Cloudera, ...
#                    ↓ bundles and manages
#Compute engine   Apache Spark, Flink, Trino, ...
#                    ↓ reads and writes
#Table format     Delta Lake, Iceberg, Hudi, ...
#                    ↓ stores as
#File format      Parquet, ORC, Avro, ...
#                    ↓ on
#Storage          S3, ADLS, GCS, HDFS, local disk

import os
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent # back to ai-agent-context-pipeline folder
print(PROJECT_ROOT)
DATALAKE = str(PROJECT_ROOT / "data" / "bronze") # location where the .jar file is stored
print(DATALAKE)

# One-time per session
duckdb.sql("INSTALL delta; LOAD delta;")

#print(duckdb.sql(f"SELECT * FROM delta_scan('{DATALAKE}/policy') LIMIT 11").df())
print(duckdb.sql(f"SELECT * FROM delta_scan('{DATALAKE}/claims') LIMIT 11").df())

