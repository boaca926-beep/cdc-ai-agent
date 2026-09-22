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
    WHERE policy_id IN('P0001')
""")

conn.commit()
cur.close()
conn.close()
print("Simulated CDC changes applied to source database")