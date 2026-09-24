# Bronze is not an overwrite. Each run reads the current source snapshot and MERGEs it into Delta on the primary key,
# so inserts, updates, and soft-deletes are all reflected without destroying history.
# This is the same Delta operation a Debezium sink would use; only the change transport differs.

import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # → ai-agent-context-pipeline/

# Load a profile only when running outside Docker.
# Inside Docker, env vars come from `env_file:` in compose.
if not Path("/.dockerenv").exists():
    env_file = Path(os.environ.get("ENV_FILE", PROJECT_ROOT / ".env"))
    if not env_file.exists():
        raise RuntimeError(f"Env file not found: {env_file}")
    load_dotenv(env_file)
    print(f"Loaded env from: {env_file}")

from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


JDBC_JAR = str(PROJECT_ROOT / "jars" / "postgresql-42.7.4.jar")

PG_HOST = required_env("POSTGRES_HOST")
PG_PORT = required_env("POSTGRES_PORT")
PG_DB   = required_env("POSTGRES_DB")
PG_USER = required_env("POSTGRES_USER")
PG_PASS = required_env("POSTGRES_PASSWORD")

JDBC_URL = f"jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}"

BRONZE_ROOT = os.environ.get("BRONZE_ROOT", "./data/bronze")


def build_spark():
    builder = (
        SparkSession.builder
        .appName("Insurance-CDC-Pipeline")
        .master("local[*]")
        .config("spark.jars", JDBC_JAR)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()


def read_from_postgres(spark, table_name):
    print(f"Reading source table: {table_name}")
    return (
        spark.read
        .format("jdbc")
        .option("url", JDBC_URL)
        .option("dbtable", table_name)
        .option("user", PG_USER)
        .option("password", PG_PASS)
        .option("driver", "org.postgresql.Driver")
        .load()
    )


def upsert_to_bronze(spark, df, path, key):
    if DeltaTable.isDeltaTable(spark, path):
        (
            DeltaTable.forPath(spark, path).alias("t")
            .merge(df.alias("s"), f"t.{key} = s.{key}")
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )
    else:
        df.write.format("delta").save(path)


def main():
    spark = build_spark()
    for table, key in [("policy", "policy_id"), ("claims", "claim_id")]:
        df = read_from_postgres(spark, table)
        path = str(PROJECT_ROOT / BRONZE_ROOT / table)
        upsert_to_bronze(spark, df, path, key)
        print(f"Bronze {table}: merged {df.count()} rows")
    spark.stop()


if __name__ == "__main__":
    main()