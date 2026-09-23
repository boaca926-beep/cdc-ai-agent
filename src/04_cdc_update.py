# Mutate source (the "CDC event generator")

import psycopg2

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="insurance_db",
    user="insurance_user", password="insurance_pw",
)
cur = conn.cursor()

cur.execute("""
    UPDATE policy SET status = 'cancelled', updated_at = NOW()
    WHERE policy_id IN('P0001', 'P0005', 'P0010')
""")

cur.execute("""
    UPDATE claims SET claim_status = 'processing', updated_at = NOW()
    WHERE claim_id IN('CL0001', 'CL0005', 'CL0010')
""")

# Soft delete: the row remains, ingetstion sees it and marks it deleted
cur.execute("""
    UPDATE claims SET is_deleted = TRUE, deleted_at = NOW(),
                      updated_at = NOW()
    WHERE claim_id = 'CL0011'
""")

conn.commit()
cur.close()
conn.close()
print("Simulated CDC changes applied to source database")
print(" Updated 3 policies")
print(" Updated 3 claims")
print(" Soft-deleted 1 claim (CL0011)")
print("Re-run 03_bronze_ingestion.py to pick up changes via MERGE")