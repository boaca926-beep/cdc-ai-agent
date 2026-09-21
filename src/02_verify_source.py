# check_db.py
import psycopg2

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="insurance_db",
    user="insurance_user", password="insurance_pw",
)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM policy WHERE NOT is_deleted")
print(f"active policy count: {cur.fetchone()}[0]")

cur.execute("SELECT COUNT(*) FROM claims WHERE NOT is_deleted")
print(f"active claims count: {cur.fetchone()}[0]")

#cur.execute("""
#    SELECT table_name FROM information_schema.tables
#    WHERE table_schema = 'public'
#    ORDER BY table_name;
#""")
#print("Tables:", [r[0] for r in cur.fetchall()])

#cur.execute("SELECT COUNT(*) FROM policy;")
#print("policy rows:", cur.fetchone()[0])

#cur.execute("SELECT COUNT(*) FROM claims;")
#print("claims rows:", cur.fetchone()[0])

#cur.execute("SELECT * FROM policy ORDER BY policy_id LIMIT 5;")
#print("First 5 policies:")
#for row in cur.fetchall():
#    print("  ", row)

#cur.execute("SELECT * FROM claims ORDER BY policy_id LIMIT 5;")
#print("First 5 claims:")
#for row in cur.fetchall():
#    print("  ", row)


#cur.close()
#conn.close()