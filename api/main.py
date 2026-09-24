from pathlib import Path
from fastapi import FastAPI, HTTPException
from deltalake import DeltaTable
from slugify import slugify

app = FastAPI(
    title = "CDC Bronze Ingestion API",
    description = "Read API over the Bronze Delta tables.",
    version = "0.1.0",
)

BRONZE_ROOT = Path(__file__).parent.parent / "data" / "bronze" 
print(f"{BRONZE_ROOT}")

def read_bronze(table: str):
    path = BRONZE_ROOT / table
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Table {table} not found")
    return DeltaTable(str(path)).to_pandas()
    

# Azure Container Apps (and Kubernetes, and most container platforms) periodically sends an HTTP request to decide whether your container is healthy.
@app.get("/health")
def health():
    """Liveness probe. Used by Azure Container Apps."""
    return {"status": "ok"}

@app.get("/bronze/status")
def status():
    """Row counts for each Bronze table."""
    out = {}
    for table in ("policy", "claims"):
        try:
            df = read_bronze(table)
            out[table] ={
                "rows": int(len(df)),
                "active": int((~df["is_deleted"]).sum())
                # flips boolean, means "NOT deleted"
                if "is_deleted" in df.columns
                else int(len(df)),
            }
        except HTTPException:
            out[table] = {"rows": 0, "active": 0}
    return out

@app.get("/bronze/policy/{policy_id}")
def get_policy(policy_id: str):
    df = read_bronze("policy")
    row = df[df["policy_id"] == policy_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Policy not found")
    return row.iloc[0].to_dict()
    

@app.get("/bronze/claims/{claim_id}")
def get_claims(claim_id: str):
    df = read_bronze("claims")
    row = df[df["claim_id"] == claim_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Claim not found")
    return row.iloc[0].to_dict()
    