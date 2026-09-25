import os
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from delta import configure_spark_with_delta_pip

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

def read_bronze(table):
    return spark.read.format("delta").load(f"data/bronze/{table}")

def split_and_persist(df, label):
    """Split into clean and quarantined, persisting both."""
    pass

# ---- policy checks ----
policy = read_bronze("policy")

p = policy.withColumn(
    "quality_flag",
    F.when(F.col("policy_id").isNull(), "null_key")
)

p = p.withColumn(
    "quality_flag",
    F.when(F.col("quality_flag").isNull() &
           ~F.col("status").isin("active", "expired", "cancelled"), 
           "invalid_status")
     .otherwise(F.col("quality_flag"))
)

p = p.withColumn(
    "quality_flag", 
    F.when(F.col("quality_flag").isNull() &
           (F.col("premium") < 0), "negative_premium")
     .otherwise(F.col("quality_flag")) 
)

policy_clean, _ = split_and_persist(p, "policy")