# Every read that could reach the Agent is routed through a single accessor scoped by the
# authenticated customer_id. The value is expected to come from a session, not from user-supplied
# text; the demo does not include an auth layer, but the boundary is explicit so that
# adding one is a one-line change. There is no string interpolation into SQL anywhere,
# reads are built from DataFrame filters, so a malicious customer_id cannot alter the query shape.
# such as customer_id = ' ' or '1'='1'


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

_policy_clean = spark.read.format("delta").load(str(PROJECT_ROOT / "data" / "silver" / "policy_clean")).filter(~F.col("is_deleted"))
_claims_clean = spark.read.format("delta").load(str(PROJECT_ROOT / "data" / "silver" / "claims_clean")).filter(~F.col("is_deleted"))
#policy_clean.show()
#print(f"{claims_clean.count()}")

def get_agent_context(customer_id: str):
    """
    Row-level isolation boundary. 'customer_id' is expected to come from an 
    anthenticated session (login), NOT from user-supplied text. In production this 
    would additionally be enforced by a row filter / RLS policy at the storage layer;
    here it is enforced by scoping every read through this funciton.
    """

    return (_policy_clean
            .filter(F.col("customer_id") == customer_id)
            .join(_claims_clean, "policy_id", "left")
            .drop(_claims_clean["customer_id"]) # remove the duplicate
            .select(
                "policy_id", 
                "customer_id",
                F.col("status").alias("policy_status"),
                "premium",
                "claim_id", "claim_status", "amount"))

if __name__ == "__main__":
    customer_id = "C001"
    ctx = get_agent_context(customer_id)
    ctx.show(truncate=False)
    #policy_clean.select("customer_id").distinct().show(20, truncate=False)
    print(f"Customer {customer_id} has {ctx.count()} context")
    #joined = (policy_clean
    #          .filter(F.col("customer_id") == "CL0001")
    #          .join(claims_clean, "policy_id", "left"))
    #joined.printSchema() # customer_id twice
    _policy_clean.printSchema()