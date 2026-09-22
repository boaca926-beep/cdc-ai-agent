# Create schema, seed 100 policies + 150 claims
import psycopg2
import random

PG_CONFIG = {
    "host": "localhost", "port": 5432,
    "dbname": "insurance_db",
    "user": "insurance_user", "password": "insurance_pw",
}

conn = psycopg2.connect(**PG_CONFIG)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS claims CASCADE")
cur.execute("DROP TABLE IF EXISTS policy CASCADE")

cur.execute("""
    CREATE TABLE policy (
        policy_id VARCHAR(50) PRIMARY KEY,
        customer_id VARCHAR(50) NOT NULL,
        status VARCHAR(20) NOT NULL,
        premium NUMERIC(10, 2) NOT NULL CHECK (premium >= 0 ),
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        is_deleted BOOLEAN DEFAULT FALSE,
        deleted_at TIMESTAMPTZ
    )
""")

cur.execute("""
    CREATE TABLE claims (
        claim_id VARCHAR(50) PRIMARY KEY,
        policy_id VARCHAR(50) REFERENCES policy(policy_id),
        customer_id VARCHAR(50) NOT NULL,
        claim_status VARCHAR(20) NOT NULL,
        amount NUMERIC(10, 2) NOT NULL CHECK (amount >= 0),
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        is_deleted BOOLEAN DEFAULT FALSE,
        deleted_at TIMESTAMPTZ 
    )
""")

random.seed(42)

# Build policies first, remembering (policy_id, customer_id) pairs
policies = []
for i in range (1, 101):
    pid = f"P{i:04d}"
    cid = f"C{random.randint(1, 20):03d}"
    #print(pid)
    #print(cid)
    policies.append((pid, cid))
    cur.execute(
        "INSERT INTO policy (policy_id, customer_id, status, premium) "
        "VALUES (%s, %s, %s, %s)",
        (pid, cid,
         random.choice(['active', 'expired', 'cancelled']),
         round(random.uniform(100, 2000), 2)
        )
    )

# Claims inherit customer_id from their parent policy
for i in range(1, 151):
    pid, cid = random.choice(policies)
    #print(f"pid = {pid}, cid = {cid}")
    cur.execute(
        "INSERT INTO claims (claim_id, policy_id, customer_id, claim_status, amount) "
        "VALUES (%s, %s, %s, %s, %s)",
        (f"CL{i:04d}", pid, cid,
         random.choice(["submitted", "processing", "approved", "rejected"]),
         round(random.uniform(500, 50000), 2)
        )
    )

conn.commit()
cur.close()