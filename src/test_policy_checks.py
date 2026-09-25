# Test the flag with synthetic data
import os
os.environ["SPARK_LOCAL_IP"] = "172.20.23.187"

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Sets the Spark master URL to run Spark in local mode, not on a cluster
spark = SparkSession.builder.master("local[*]").getOrCreate()

def split_and_persist(df):
    """Split into clean and quarantined, persisting both."""
    bad = df.filter(F.col("quality_flag").isNotNull())
    return bad

policy = spark.createDataFrame([
    ("P0001", "active", 100.0), # ok
    (None,    "active", 100.0), # null key
    ("P0002", "unknown", 100.0), # invalid_status
    ("P0003", "active", -5.0), # negative_premium
    (None,    "active", -5.0), # null_key (first match)
    ("P0004", "active", None), # invalid_premium (null premium)
],
"policy_id string, status string, premium double",
)

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
           ((F.col("premium") < 0) | F.col("premium").isNull()), 
           "invalid_premium")
     .otherwise(F.col("quality_flag"))
)

print(policy)
p.show(truncate=False) # show all cell contents
bad = split_and_persist(p)
#print(f"{type(p)}")
bad.show(truncate=False)
spark.stop()