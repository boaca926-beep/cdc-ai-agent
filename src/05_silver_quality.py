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
    return spark.read.format("delta").load(str(PROJECT_ROOT/"data"/"bronze"/table))

def split_and_persist(df, label):
    """Split into clean and quarantined, persisting both."""
    bad = df.filter(F.col("quality_flag").isNotNull())
    good = df.filter(F.col("quality_flag").isNull()).drop("quality_flag")
    bad.write.format("delta").mode("overwrite").save(str(PROJECT_ROOT/"data"/"quarantine"/label))
    print(f"    {label}: clean={good.count()} quarantined={bad.count()}")
    return good, bad

# Staleness cutoff is read from Postgres, in the same clock as updated_at.
stale_cutoff = (spark.read.format("jdbc") # use the JDBC interface (not Postgres-specific)
                .option("url", JDBC_URL)
                .option("query", "SELECT (NOW() - INTERVAL '30 days') AS cutoff")
                .option("user", "insurance_user")
                .option("password", "insurance_pw")
                .option("driver", "org.postgresql.Driver") # the thing on the other end is Postgres
                .load()
                .collect()[0]["cutoff"])
print(f"stale_cutoff = {stale_cutoff}")

# ---- policy checks ----
policy = read_bronze("policy")

p = policy.withColumn("quality_flag",
    F.when(F.col("policy_id").isNull(), "null_key"))

p = p.withColumn("quality_flag",
                 F.when(F.col("quality_flag").isNull() &
                         (~F.col("status").isin("active", "expired", "cancelled")),
                         "invalid_status").otherwise(F.col("quality_flag")))

p = p.withColumn("quality_flag",
                  F.when(F.col("quality_flag").isNull() &
                          (F.col("premium") < 0), "negative_premium")
                          .otherwise(F.col("quality_flag"))) 

policy_clean, policy_quarantine = split_and_persist(p, "policy")

# ---- claims checks ----
claims = read_bronze("claims")

c = claims.withColumn("quality_flag", 
                      F.when(F.col("claim_id").isNull(), "null_key"))

c = c.withColumn("quality_flag", 
                 F.when(F.col("quality_flag").isNull() & 
                 (~F.col("claim_status").isin(
                     "submitted", "processing", "approved", "rejected")),
                 "invalid_status").otherwise(F.col("quality_flag")))

# Referential integrity: policy_id must exist in the clean policy set
valid_policies = policy_clean.select("policy_id").distinct().withColumnRenamed("policy_id", "_p")
print(f"valid_policies: {valid_policies.count()}, policy_clean: {policy_clean.count()}")
print(f"before c: {c.count()}")

c = c.join(valid_policies, c.policy_id == F.col("_p"), "left").withColumn(
    "quality_flag",
    F.when(F.col("quality_flag").isNull() & 
    F.col("_p").isNull(), 
    "orphan_policy").otherwise(F.col("quality_flag"))).drop("_p")

# Stalness: open claims not touched in 30 days
c = c.withColumn(
    "quality_flag", 
    F.when(F.col("quality_flag").isNull() &
            (F.col("claim_status").isin("submitted", "processing")) & 
            (F.col("updated_at") < F.lit(stale_cutoff)), # evaluate Columns against the data and compare
            "stale_claim").otherwise(F.col("quality_flag")))

claims_clean, claim_quarantine = split_and_persist(c, "claims")

print(f"after c: {c.show()}")

orphans = c.filter(F.col("quality_flag") == "orphan_policy").count()
print(f"orphans: {orphans}")

# write the results
policy_clean.write.format("delta").mode("overwrite").save(str(PROJECT_ROOT/"data"/"silver"/"policy_clean"))
claims_clean.write.format("delta").mode("overwrite").save(str(PROJECT_ROOT/"data"/"silver"/"claims_clean"))

spark.stop()