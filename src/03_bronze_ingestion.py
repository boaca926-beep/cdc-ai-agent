# Bronze is not an overwrit. Each run reads the current source snapshot and MERGEs it into Delta on the primary key, 
# so inserts, updates, and soft-deletes are all reflected without destorying history.
# This is the same Delta operation a Debezium sink would use; only the change transport differs.
# Snapshot-read source, MERGE into Delta Bronze

import os
from pathlib import Path
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

PROJECT_ROOT = Path(__file__).resolve().parent.parent # back to ai-agent-context-pipeline folder
print(PROJECT_ROOT)
JDBC_JAR = str(PROJECT_ROOT / "jars" / "postgresql-42.7.4.jar") # location where the .jar file is stored
print(JDBC_JAR)
JDBC_URL = "jdbc:postgresql://localhost:5432/insurance_db" # JDBC url

# Build spark
def build_spark():
    builder = (SparkSession.builder
               .appName("Insurance-CDC-Pipeline")
               .master("local[*]") # tells Spark to run in local mode using all available CPU cores on the machine
               .config("spark.jars", JDBC_JAR)
               .config("spark.sql.extensions",
                       "io.delta.sql.DeltaSparkSessionExtension")
               .config("spark.sql.catalog.spark_catalog",
                       "org.apache.spark.sql.delta.catalog.DeltaCatalog"))
    return configure_spark_with_delta_pip(builder).getOrCreate()

spark = build_spark()

def read_from_postgres(table_name):
    print(table_name)
    return (spark.read
            .format("jdbc")
            .option("url", JDBC_URL)
            .option("dbtable", table_name)
            .option("user", "insurance_user")
            .option("password", "insurance_pw")
            .option("driver", "org.postgresql.Driver") # class name from the jars/*.jar file
            .load())

def upsert_to_bronze(df, path, key):
    """MERGE a source snapshot into Bronze keyed by primary key."""
    if DeltaTable.isDeltaTable(spark, path):
        (DeltaTable.forPath(spark, path).alias("t")
         .merge(df.alias("s"), f"t.{key} = s.{key}")
         .whenMatchedUpdateAll()
         .whenNotMatchedInsertAll()
         .execute())
    else:
        df.write.format("delta").save(path)

for table, key in [("policy", "policy_id"), ("claims", "claim_id")]:
    #print(f"{table}, {key}")
    df = read_from_postgres(table)
    path = str(PROJECT_ROOT / "data" / "bronze" / table)
    upsert_to_bronze(df, path, key)
    print(f"Bronze {table}: merged {df.count()} rows")