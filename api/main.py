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
    

#@app.get("/health")
#def health():
#    pass

#@app.get("/bronze/status")
#def status():
#    pass

@app.get("/bronze/policy/{policy_id}")
def get_policy(policy_id: str):
    df = read_bronze("policy")
    return
    

@app.get("/bronze/claims/{claim_id}")
def get_claims(claim_id: str):
    df = read_bronze("claims")
    return
    